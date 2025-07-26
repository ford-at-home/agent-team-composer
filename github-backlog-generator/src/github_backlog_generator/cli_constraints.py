"""CLI usage constraints and validation."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import click
from rich.console import Console

from .phase_schema import PhaseSchema, PhaseSchemaError

console = Console()


class CLIConstraintError(Exception):
    """Exception raised for CLI constraint violations."""
    pass


class CLIConstraints:
    """Manages CLI usage constraints and validation."""
    
    @staticmethod
    def validate_repository_format(repo: str) -> Tuple[str, str]:
        """Validate and parse repository format."""
        if not repo or '/' not in repo:
            raise CLIConstraintError(
                f"Invalid repository format '{repo}'. Use format 'owner/repo'"
            )
        
        parts = repo.split('/')
        if len(parts) != 2:
            raise CLIConstraintError(
                f"Invalid repository format '{repo}'. Use format 'owner/repo'"
            )
        
        owner, repo_name = parts
        if not owner or not repo_name:
            raise CLIConstraintError(
                f"Invalid repository format '{repo}'. Both owner and repo name are required"
            )
        
        # Validate GitHub naming conventions
        if not CLIConstraints.is_valid_github_name(owner):
            raise CLIConstraintError(
                f"Invalid owner name '{owner}'. Must contain only alphanumeric characters, hyphens, and underscores"
            )
        
        if not CLIConstraints.is_valid_github_name(repo_name):
            raise CLIConstraintError(
                f"Invalid repository name '{repo_name}'. Must contain only alphanumeric characters, hyphens, periods, and underscores"
            )
        
        return owner, repo_name
    
    @staticmethod
    def is_valid_github_name(name: str) -> bool:
        """Check if a name follows GitHub naming conventions."""
        if not name or len(name) > 39:  # GitHub username/repo name limit
            return False
        
        # Must start and end with alphanumeric
        if not (name[0].isalnum() and name[-1].isalnum()):
            return False
        
        # Can contain alphanumeric, hyphens, periods, and underscores
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._')
        return all(c in allowed_chars for c in name)
    
    @staticmethod
    def validate_phases_file(phases_file: str) -> str:
        """Validate phases file exists and is readable."""
        if not phases_file:
            raise CLIConstraintError("Phases file path is required")
        
        phases_path = Path(phases_file)
        
        if not phases_path.exists():
            raise CLIConstraintError(f"Phases file not found: {phases_file}")
        
        if not phases_path.is_file():
            raise CLIConstraintError(f"Phases path is not a file: {phases_file}")
        
        if not phases_path.suffix.lower() == '.json':
            console.print(f"[yellow]Warning: Phases file '{phases_file}' does not have .json extension[/yellow]")
        
        # Test readability
        try:
            with open(phases_path, 'r', encoding='utf-8') as f:
                f.read(1)  # Just try to read one character
        except PermissionError:
            raise CLIConstraintError(f"Permission denied reading phases file: {phases_file}")
        except Exception as e:
            raise CLIConstraintError(f"Cannot read phases file: {phases_file} - {e}")
        
        return str(phases_path.absolute())
    
    @staticmethod
    def validate_phases_json_content(phases_file: str) -> List[Dict[str, Any]]:
        """Validate phases JSON content and return normalized phases."""
        try:
            # Load and validate the JSON structure
            phases_data = PhaseSchema.load_and_validate(phases_file)
            
            # Normalize phases for use
            normalized_phases = PhaseSchema.normalize_phases(phases_data)
            
            console.print(f"[green]✓[/green] Phases file validated: {len(normalized_phases)} phases found")
            return normalized_phases
            
        except PhaseSchemaError as e:
            raise CLIConstraintError(f"Invalid phases file: {e}")
        except json.JSONDecodeError as e:
            raise CLIConstraintError(f"Invalid JSON in phases file: {e}")
        except Exception as e:
            raise CLIConstraintError(f"Error reading phases file: {e}")
    
    @staticmethod
    def validate_api_key(api_key: Optional[str] = None) -> str:
        """Validate Anthropic API key is available."""
        if api_key:
            key = api_key
        else:
            key = os.getenv('ANTHROPIC_API_KEY')
        
        if not key:
            raise CLIConstraintError(
                "ANTHROPIC_API_KEY not found. Set it as an environment variable or pass via --api-key"
            )
        
        if not key.startswith('sk-'):
            raise CLIConstraintError(
                "Invalid ANTHROPIC_API_KEY format. Must start with 'sk-'"
            )
        
        if len(key) < 20:
            raise CLIConstraintError(
                "ANTHROPIC_API_KEY appears to be too short. Please check your key"
            )
        
        return key
    
    @staticmethod
    def validate_github_token(github_token: Optional[str] = None) -> str:
        """Validate GitHub token is available."""
        if github_token:
            token = github_token
        else:
            token = os.getenv('GITHUB_TOKEN')
        
        if not token:
            raise CLIConstraintError(
                "GITHUB_TOKEN not found. Set it as an environment variable or pass via --github-token"
            )
        
        # Basic GitHub token format validation
        if token.startswith('ghp_') and len(token) != 40:
            console.print("[yellow]Warning: GitHub personal access token format may be incorrect[/yellow]")
        elif token.startswith('github_pat_') and len(token) < 50:
            console.print("[yellow]Warning: GitHub fine-grained token format may be incorrect[/yellow]")
        
        return token
    
    @staticmethod
    def validate_output_file_path(output_file: str) -> str:
        """Validate output file path is writable."""
        if not output_file:
            raise CLIConstraintError("Output file path is required")
        
        output_path = Path(output_file)
        
        # Check if parent directory exists
        parent_dir = output_path.parent
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"[dim]Created directory: {parent_dir}[/dim]")
            except Exception as e:
                raise CLIConstraintError(f"Cannot create output directory {parent_dir}: {e}")
        
        # Check if we can write to the file
        try:
            # Test write access by creating a temporary file
            test_file = output_path.with_suffix('.tmp')
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            raise CLIConstraintError(f"Cannot write to output file {output_file}: {e}")
        
        return str(output_path.absolute())
    
    @staticmethod
    def check_concurrent_execution(owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Check for concurrent execution and provide helpful error message."""
        from .state_manager import create_state_manager
        
        try:
            state_manager = create_state_manager(owner, repo)
            concurrent_info = state_manager.check_concurrent_execution()
            
            if concurrent_info:
                console.print(f"\n[red]⚠️  Concurrent Execution Detected[/red]")
                console.print(f"Another process is already running on {owner}/{repo}")
                console.print(f"[dim]Process ID: {concurrent_info.get('pid')}[/dim]")
                console.print(f"[dim]Started: {concurrent_info.get('locked_at')}[/dim]")
                console.print(f"[dim]Command: {concurrent_info.get('command', 'Unknown')}[/dim]")
                console.print("")
                console.print("[yellow]Options:[/yellow]")
                console.print("• Wait for the other process to complete")
                console.print("• Use --force-restart to override (may cause issues)")
                console.print("• Kill the other process manually if it's stuck")
                
                return concurrent_info
                
        except Exception as e:
            console.print(f"[yellow]Warning: Could not check for concurrent execution: {e}[/yellow]")
        
        return None
    
    @staticmethod
    def validate_command_combination(ctx: click.Context, 
                                   phases_file: Optional[str] = None,
                                   dry_run: bool = False,
                                   force_restart: bool = False) -> Dict[str, Any]:
        """Validate command parameter combinations."""
        validation_info = {
            'warnings': [],
            'suggestions': []
        }
        
        # Check for conflicting options
        if dry_run and force_restart:
            validation_info['warnings'].append(
                "--force-restart has no effect in dry-run mode"
            )
        
        # Check for missing dependencies
        if phases_file and not Path(phases_file).exists():
            validation_info['warnings'].append(
                f"Phases file '{phases_file}' not found - will use default phases"
            )
        
        # Provide helpful suggestions
        if not dry_run:
            validation_info['suggestions'].append(
                "Consider using --dry-run first to preview changes"
            )
        
        if not phases_file:
            validation_info['suggestions'].append(
                "Use --phases to provide custom project phases"
            )
        
        return validation_info
    
    @staticmethod
    def enforce_minimum_requirements():
        """Enforce minimum system requirements."""
        # Check Python version
        if sys.version_info < (3, 8):
            raise CLIConstraintError(
                f"Python 3.8+ required. Current version: {sys.version_info.major}.{sys.version_info.minor}"
            )
        
        # Check for required environment or suggest setup
        required_packages = ['anthropic', 'click', 'rich']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            raise CLIConstraintError(
                f"Missing required packages: {', '.join(missing_packages)}. "
                f"Run: pip install {' '.join(missing_packages)}"
            )
    
    @staticmethod
    def display_constraint_violations(violations: List[str]):
        """Display constraint violation messages in a user-friendly way."""
        console.print("\n[red]❌ CLI Constraint Violations:[/red]")
        
        for i, violation in enumerate(violations, 1):
            console.print(f"  {i}. {violation}")
        
        console.print("\n[yellow]Please fix these issues and try again.[/yellow]")


# Decorator for command constraint validation
def validate_constraints(
    require_repo: bool = False,
    require_api_key: bool = False,
    require_github_token: bool = False,
    require_phases_file: bool = False,
    check_concurrent: bool = False
):
    """Decorator to validate CLI constraints before command execution."""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            violations = []
            
            try:
                # Enforce minimum requirements
                CLIConstraints.enforce_minimum_requirements()
                
                # Repository validation
                if require_repo and 'repo' in kwargs:
                    try:
                        owner, repo_name = CLIConstraints.validate_repository_format(kwargs['repo'])
                        kwargs['owner'] = owner
                        kwargs['repo_name'] = repo_name
                    except CLIConstraintError as e:
                        violations.append(str(e))
                
                # API key validation
                if require_api_key:
                    try:
                        api_key = CLIConstraints.validate_api_key(kwargs.get('api_key'))
                        kwargs['api_key'] = api_key
                    except CLIConstraintError as e:
                        violations.append(str(e))
                
                # GitHub token validation
                if require_github_token:
                    try:
                        github_token = CLIConstraints.validate_github_token(kwargs.get('github_token'))
                        kwargs['github_token'] = github_token
                    except CLIConstraintError as e:
                        violations.append(str(e))
                
                # Phases file validation
                if require_phases_file and 'phases' in kwargs and kwargs['phases']:
                    try:
                        phases_file = CLIConstraints.validate_phases_file(kwargs['phases'])
                        phases = CLIConstraints.validate_phases_json_content(phases_file)
                        kwargs['phases_file'] = phases_file
                        kwargs['phases_data'] = phases
                    except CLIConstraintError as e:
                        violations.append(str(e))
                
                # Concurrent execution check
                if check_concurrent and 'owner' in kwargs and 'repo_name' in kwargs:
                    if not kwargs.get('force_restart', False):
                        concurrent_info = CLIConstraints.check_concurrent_execution(
                            kwargs['owner'], kwargs['repo_name']
                        )
                        if concurrent_info:
                            violations.append("Concurrent execution detected")
                
                # Display violations and exit if any
                if violations:
                    CLIConstraints.display_constraint_violations(violations)
                    sys.exit(1)
                
                # Execute the original function
                return func(*args, **kwargs)
                
            except CLIConstraintError as e:
                console.print(f"\n[red]❌ CLI Constraint Error:[/red] {e}")
                sys.exit(1)
            except Exception as e:
                console.print(f"\n[red]❌ Unexpected error during constraint validation:[/red] {e}")
                sys.exit(1)
        
        return wrapper
    return decorator