"""Tests for state management and persistence."""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from github_backlog_generator.state_manager import (
    StateManager, ExecutionStep, StateManagerError, create_state_manager
)


class TestStateManager:
    """Test the StateManager class."""
    
    def test_state_manager_initialization(self):
        """Test StateManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            assert manager.owner == 'owner'
            assert manager.repo == 'repo'
            assert manager.base_dir == Path(temp_dir)
            assert str(manager.state_file).endswith('.backloggen-state-owner-repo.json')
            assert str(manager.lock_file).endswith('.backloggen-lock-owner-repo.lock')
    
    def test_acquire_and_release_lock(self):
        """Test lock acquisition and release."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Acquire lock
            assert manager.acquire_lock(timeout=1)
            assert manager.lock_file.exists()
            
            # Read lock file content
            with open(manager.lock_file) as f:
                lock_info = json.load(f)
            
            assert lock_info['owner'] == 'owner'
            assert lock_info['repo'] == 'repo'
            assert 'pid' in lock_info
            assert 'locked_at' in lock_info
            
            # Release lock
            manager.release_lock()
            assert not manager.lock_file.exists()
    
    def test_concurrent_execution_detection(self):
        """Test concurrent execution detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager1 = StateManager('owner', 'repo', Path(temp_dir))
            manager2 = StateManager('owner', 'repo', Path(temp_dir))
            
            # First manager acquires lock
            assert manager1.acquire_lock(timeout=1)
            
            # Second manager should detect concurrent execution
            concurrent_info = manager2.check_concurrent_execution()
            assert concurrent_info is not None
            assert concurrent_info['owner'] == 'owner'
            assert concurrent_info['repo'] == 'repo'
            
            # Second manager cannot acquire lock
            assert not manager2.acquire_lock(timeout=1)
            
            # Clean up
            manager1.release_lock()
    
    def test_state_persistence(self):
        """Test state saving and loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Initial state should not exist
            assert manager.load_state() is None
            
            # Save initial state
            test_phases = [{'title': 'Phase 1', 'description': 'Test phase'}]
            initial_state = manager.initialize_state(
                test_phases, 'test-command', {'option': 'value'}
            )
            
            assert 'execution_id' in initial_state
            assert initial_state['owner'] == 'owner'
            assert initial_state['repo'] == 'repo'
            assert initial_state['current_step'] == ExecutionStep.INIT.value
            assert initial_state['phases'] == test_phases
            
            # Load state back
            loaded_state = manager.load_state()
            assert loaded_state is not None
            assert loaded_state['owner'] == 'owner'
            assert loaded_state['repo'] == 'repo'
            assert loaded_state['phases'] == test_phases
    
    def test_step_updates(self):
        """Test execution step updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Initialize state
            test_phases = [{'title': 'Phase 1'}]
            manager.initialize_state(test_phases, 'test-command', {})
            
            # Update to next step
            manager.update_step(
                ExecutionStep.PHASES_LOADED, 
                "Phases loaded successfully",
                {'loaded_count': 1}
            )
            
            state = manager.load_state()
            assert state['current_step'] == ExecutionStep.PHASES_LOADED.value
            assert ExecutionStep.INIT.value in state['completed_steps']
            assert state['checkpoint_data']['loaded_count'] == 1
            
            # Check execution log
            assert len(state['execution_log']) >= 2
            assert any(entry['step'] == ExecutionStep.PHASES_LOADED.value 
                      for entry in state['execution_log'])
    
    def test_step_completion_checking(self):
        """Test step completion checking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Initialize state
            test_phases = [{'title': 'Phase 1'}]
            manager.initialize_state(test_phases, 'test-command', {})
            
            # Initially, only init should be tracked
            assert not manager.is_step_completed(ExecutionStep.PHASES_LOADED)
            
            # Update step
            manager.update_step(ExecutionStep.PHASES_LOADED, "Phases loaded")
            
            # Now init should be completed
            assert manager.is_step_completed(ExecutionStep.INIT)
            assert not manager.is_step_completed(ExecutionStep.PHASES_LOADED)
            
            # Current step should be phases loaded
            assert manager.get_current_step() == ExecutionStep.PHASES_LOADED
    
    def test_resume_functionality(self):
        """Test resume functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # No state initially - cannot resume
            assert not manager.can_resume()
            assert manager.get_resume_info() is None
            
            # Initialize and progress through steps
            test_phases = [{'title': 'Phase 1'}, {'title': 'Phase 2'}]
            manager.initialize_state(test_phases, 'test-command', {})
            manager.update_step(ExecutionStep.PHASES_LOADED, "Phases loaded")
            manager.update_step(ExecutionStep.EPICS_GENERATED, "Epics created")
            
            # Now should be able to resume
            assert manager.can_resume()
            
            resume_info = manager.get_resume_info()
            assert resume_info is not None
            assert resume_info['current_step'] == ExecutionStep.EPICS_GENERATED.value
            assert len(resume_info['completed_steps']) == 2  # init + phases_loaded
            assert resume_info['phases_count'] == 2
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Use as context manager
            with manager:
                assert manager.lock_file.exists()
                # Do some work within the context
                test_phases = [{'title': 'Test'}]
                manager.initialize_state(test_phases, 'test', {})
            
            # Lock should be released after context
            assert not manager.lock_file.exists()
    
    def test_context_manager_concurrent_execution_error(self):
        """Test context manager with concurrent execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager1 = StateManager('owner', 'repo', Path(temp_dir))
            manager2 = StateManager('owner', 'repo', Path(temp_dir))
            
            # First manager acquires lock
            with manager1:
                # Second manager should raise error when trying to use context
                with pytest.raises(StateManagerError, match="Another process is already running"):
                    with manager2:
                        pass
    
    def test_clear_state(self):
        """Test state clearing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Create state
            test_phases = [{'title': 'Test'}]
            manager.initialize_state(test_phases, 'test', {})
            assert manager.state_file.exists()
            
            # Clear state
            manager.clear_state()
            assert not manager.state_file.exists()
            assert manager.load_state() is None
    
    def test_corrupted_state_handling(self):
        """Test handling of corrupted state files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Create corrupted state file
            with open(manager.state_file, 'w') as f:
                f.write('{ corrupted json }')
            
            # Should raise error when loading
            with pytest.raises(StateManagerError, match="Corrupted state file"):
                manager.load_state()
    
    def test_execution_step_enum(self):
        """Test ExecutionStep enum values."""
        assert ExecutionStep.INIT.value == "init"
        assert ExecutionStep.PHASES_LOADED.value == "phases_loaded"
        assert ExecutionStep.PHASES_PREPROCESSED.value == "phases_preprocessed"
        assert ExecutionStep.MILESTONES_CREATED.value == "milestones_created"
        assert ExecutionStep.EPICS_GENERATED.value == "epics_generated"
        assert ExecutionStep.ISSUES_GENERATED.value == "issues_generated"
        assert ExecutionStep.SUMMARY_GENERATED.value == "summary_generated"
        assert ExecutionStep.COMPLETED.value == "completed"
    
    def test_stale_lock_cleanup(self):
        """Test cleanup of stale lock files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Create a lock file with a non-existent PID
            lock_info = {
                'pid': 99999999,  # Very unlikely to exist
                'owner': 'owner',
                'repo': 'repo',
                'locked_at': '2024-01-01T10:00:00',
                'command': 'test'
            }
            
            with open(manager.lock_file, 'w') as f:
                json.dump(lock_info, f)
            
            # Check concurrent execution should clean up stale lock
            result = manager.check_concurrent_execution()
            assert result is None
            assert not manager.lock_file.exists()


class TestStateManagerFactory:
    """Test the state manager factory function."""
    
    def test_create_state_manager(self):
        """Test state manager factory function."""
        manager = create_state_manager('owner', 'repo')
        
        assert isinstance(manager, StateManager)
        assert manager.owner == 'owner'
        assert manager.repo == 'repo'
    
    def test_create_state_manager_with_base_dir(self):
        """Test state manager factory with custom base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = create_state_manager('owner', 'repo', Path(temp_dir))
            
            assert isinstance(manager, StateManager)
            assert manager.base_dir == Path(temp_dir)


class TestStateManagerIntegration:
    """Integration tests for state manager with CLI operations."""
    
    def test_full_workflow_simulation(self):
        """Test a complete workflow simulation with state management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            test_phases = [
                {'title': 'Planning', 'description': 'Plan the project'},
                {'title': 'Development', 'description': 'Develop the features'}
            ]
            
            # Simulate full workflow with context manager
            with manager:
                # Step 1: Initialize
                state = manager.initialize_state(
                    test_phases, 'run', {'dry_run': False}
                )
                assert state['current_step'] == ExecutionStep.INIT.value
                
                # Step 2: Load phases
                manager.update_step(
                    ExecutionStep.PHASES_LOADED,
                    "Phases loaded from file",
                    {'phases_count': len(test_phases)}
                )
                
                # Step 3: Preprocess phases
                manager.update_step(
                    ExecutionStep.PHASES_PREPROCESSED,
                    "Phases preprocessed with LLM",
                    {'modified_phases': 1}
                )
                
                # Step 4: Create milestones
                manager.update_step(
                    ExecutionStep.MILESTONES_CREATED,
                    "GitHub milestones created",
                    {'milestones_created': 2}
                )
                
                # Step 5: Generate epics
                manager.update_step(
                    ExecutionStep.EPICS_GENERATED,
                    "Epics generated for all phases",
                    {'epics_count': 5}
                )
                
                # Step 6: Generate issues
                manager.update_step(
                    ExecutionStep.ISSUES_GENERATED,
                    "Issues generated for all epics",
                    {'issues_count': 15}
                )
                
                # Step 7: Generate summary
                manager.update_step(
                    ExecutionStep.SUMMARY_GENERATED,
                    "Summary report generated",
                    {'report_format': 'markdown'}
                )
                
                # Step 8: Complete
                manager.update_step(
                    ExecutionStep.COMPLETED,
                    "Workflow completed successfully"
                )
            
            # Verify final state
            final_state = manager.load_state()
            assert final_state['current_step'] == ExecutionStep.COMPLETED.value
            assert len(final_state['completed_steps']) == 7  # All steps except completed
            assert len(final_state['execution_log']) == 8  # All step transitions
            
            # Verify checkpoint data accumulation
            checkpoint_data = final_state['checkpoint_data']
            assert checkpoint_data['phases_count'] == 2
            assert checkpoint_data['modified_phases'] == 1
            assert checkpoint_data['milestones_created'] == 2
            assert checkpoint_data['epics_count'] == 5
            assert checkpoint_data['issues_count'] == 15
            assert checkpoint_data['report_format'] == 'markdown'
    
    @patch('github_backlog_generator.state_manager.console')
    def test_resume_prompt_display(self, mock_console):
        """Test resume prompt display functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = StateManager('owner', 'repo', Path(temp_dir))
            
            # Create resumable state
            test_phases = [{'title': 'Test'}]
            manager.initialize_state(test_phases, 'test', {})
            manager.update_step(ExecutionStep.PHASES_LOADED, "Phases loaded")
            
            # Mock user input
            with patch('rich.prompt.Confirm.ask', return_value=True):
                result = manager.display_resume_prompt()
                assert result is True
            
            # Verify console output was called
            assert mock_console.print.called


if __name__ == '__main__':
    pytest.main([__file__])