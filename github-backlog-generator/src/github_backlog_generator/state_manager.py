"""State persistence and checkpointing for resumable CLI operations."""

import json
import os
import fcntl
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from rich.console import Console

console = Console()


class ExecutionStep(Enum):
    """Enumeration of execution steps for checkpointing."""
    INIT = "init"
    PHASES_LOADED = "phases_loaded"
    PHASES_PREPROCESSED = "phases_preprocessed"
    MILESTONES_CREATED = "milestones_created"
    EPICS_GENERATED = "epics_generated"
    ISSUES_GENERATED = "issues_generated"
    SUMMARY_GENERATED = "summary_generated"
    COMPLETED = "completed"


class StateManagerError(Exception):
    """Exception raised for state management errors."""
    pass


class StateManager:
    """Manages persistent state for CLI operations with checkpointing."""
    
    def __init__(self, owner: str, repo: str, base_dir: Optional[Path] = None):
        self.owner = owner
        self.repo = repo
        
        if base_dir:
            self.base_dir = base_dir
        else:
            # Use current directory for state file
            self.base_dir = Path.cwd()
        
        self.state_file = self.base_dir / f".backloggen-state-{owner}-{repo}.json"
        self.lock_file = self.base_dir / f".backloggen-lock-{owner}-{repo}.lock"
        self._lock_fd = None
    
    def acquire_lock(self, timeout: int = 30) -> bool:
        """Acquire an exclusive lock for this repository."""
        try:
            # Create lock file if it doesn't exist
            self.lock_file.touch(exist_ok=True)
            
            # Open and lock the file
            self._lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write process info to lock file
            lock_info = {
                'pid': os.getpid(),
                'owner': self.owner,
                'repo': self.repo,
                'locked_at': datetime.now().isoformat(),
                'command': ' '.join(os.sys.argv)
            }
            
            self._lock_fd.write(json.dumps(lock_info, indent=2))
            self._lock_fd.flush()
            
            return True
            
        except (OSError, IOError) as e:
            if self._lock_fd:
                self._lock_fd.close()
                self._lock_fd = None
            return False
    
    def release_lock(self):
        """Release the exclusive lock."""
        if self._lock_fd:
            try:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
                self._lock_fd = None
                
                # Remove lock file
                if self.lock_file.exists():
                    self.lock_file.unlink()
                    
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to release lock cleanly: {e}[/yellow]")
    
    def check_concurrent_execution(self) -> Optional[Dict[str, Any]]:
        """Check if another process is running on this repository."""
        if not self.lock_file.exists():
            return None
        
        try:
            with open(self.lock_file, 'r') as f:
                lock_info = json.load(f)
            
            # Check if process is still running
            pid = lock_info.get('pid')
            if pid:
                try:
                    os.kill(pid, 0)  # Check if process exists
                    return lock_info  # Process is running
                except OSError:
                    # Process doesn't exist, remove stale lock
                    self.lock_file.unlink()
                    return None
            
        except (json.JSONDecodeError, IOError):
            # Corrupted or unreadable lock file, remove it
            try:
                self.lock_file.unlink()
            except:
                pass
            return None
        
        return None
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load the current state from disk."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Validate state structure
            if not isinstance(state, dict):
                raise StateManagerError("Invalid state file format")
            
            return state
            
        except json.JSONDecodeError as e:
            raise StateManagerError(f"Corrupted state file: {e}")
        except Exception as e:
            raise StateManagerError(f"Error loading state: {e}")
    
    def save_state(self, state: Dict[str, Any]):
        """Save the current state to disk."""
        try:
            # Ensure state has required fields
            state.update({
                'owner': self.owner,
                'repo': self.repo,
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            })
            
            # Write atomically by using a temporary file
            temp_file = self.state_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(self.state_file)
            
        except Exception as e:
            raise StateManagerError(f"Error saving state: {e}")
    
    def initialize_state(self, phases: List[Dict[str, Any]], command: str, 
                        options: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new state for execution."""
        initial_state = {
            'execution_id': f"{self.owner}-{self.repo}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'started_at': datetime.now().isoformat(),
            'command': command,
            'options': options,
            'current_step': ExecutionStep.INIT.value,
            'completed_steps': [],
            'phases': phases,
            'execution_log': [
                {
                    'step': ExecutionStep.INIT.value,
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Execution initialized'
                }
            ],
            'checkpoint_data': {}
        }
        
        self.save_state(initial_state)
        return initial_state
    
    def update_step(self, step: ExecutionStep, message: str = None, 
                   checkpoint_data: Dict[str, Any] = None):
        """Update the current execution step."""
        state = self.load_state()
        if not state:
            raise StateManagerError("No active state found")
        
        # Mark current step as completed
        if state['current_step'] not in state['completed_steps']:
            state['completed_steps'].append(state['current_step'])
        
        # Update to new step
        state['current_step'] = step.value
        
        # Add to execution log
        log_entry = {
            'step': step.value,
            'timestamp': datetime.now().isoformat(),
            'message': message or f"Step {step.value} completed"
        }
        state['execution_log'].append(log_entry)
        
        # Update checkpoint data
        if checkpoint_data:
            state['checkpoint_data'].update(checkpoint_data)
        
        self.save_state(state)
    
    def is_step_completed(self, step: ExecutionStep) -> bool:
        """Check if a step has been completed."""
        state = self.load_state()
        if not state:
            return False
        
        return step.value in state['completed_steps']
    
    def get_current_step(self) -> Optional[ExecutionStep]:
        """Get the current execution step."""
        state = self.load_state()
        if not state:
            return None
        
        try:
            return ExecutionStep(state['current_step'])
        except ValueError:
            return None
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        state = self.load_state()
        if not state:
            return False
        
        # Check if execution was completed
        if state.get('current_step') == ExecutionStep.COMPLETED.value:
            return False
        
        # Check if there are any completed steps to resume from
        return len(state.get('completed_steps', [])) > 0
    
    def get_resume_info(self) -> Optional[Dict[str, Any]]:
        """Get information about resumable execution."""
        if not self.can_resume():
            return None
        
        state = self.load_state()
        current_step = self.get_current_step()
        
        return {
            'execution_id': state.get('execution_id'),
            'started_at': state.get('started_at'),
            'current_step': current_step.value if current_step else 'unknown',
            'completed_steps': state.get('completed_steps', []),
            'phases_count': len(state.get('phases', [])),
            'can_resume_from': state.get('current_step')
        }
    
    def clear_state(self):
        """Clear the state file."""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to clear state file: {e}[/yellow]")
    
    def display_resume_prompt(self) -> bool:
        """Display resume prompt and get user confirmation."""
        resume_info = self.get_resume_info()
        if not resume_info:
            return False
        
        console.print("\n[bold yellow]🔄 Previous execution detected![/bold yellow]")
        console.print(f"Execution ID: [cyan]{resume_info['execution_id']}[/cyan]")
        console.print(f"Started: [dim]{resume_info['started_at']}[/dim]")
        console.print(f"Current step: [yellow]{resume_info['current_step']}[/yellow]")
        console.print(f"Completed steps: [green]{len(resume_info['completed_steps'])}[/green]")
        
        from rich.prompt import Confirm
        return Confirm.ask("\nDo you want to resume from the last checkpoint?", default=True)
    
    def get_github_artifacts_status(self, github_client) -> Dict[str, bool]:
        """Check which GitHub artifacts already exist."""
        # This would check GitHub for existing milestones, issues, etc.
        # For now, return placeholder
        return {
            'milestones_exist': False,
            'epics_exist': False,
            'issues_exist': False
        }
    
    def __enter__(self):
        """Context manager entry."""
        if not self.acquire_lock():
            concurrent_info = self.check_concurrent_execution()
            if concurrent_info:
                raise StateManagerError(
                    f"Another process is already running on {self.owner}/{self.repo} "
                    f"(PID: {concurrent_info.get('pid')}, started: {concurrent_info.get('locked_at')})"
                )
            else:
                raise StateManagerError(f"Could not acquire lock for {self.owner}/{self.repo}")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release_lock()


def create_state_manager(owner: str, repo: str, base_dir: Optional[Path] = None) -> StateManager:
    """Factory function to create a StateManager instance."""
    return StateManager(owner, repo, base_dir)