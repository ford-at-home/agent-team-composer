"""GitHub Backlog Generator CLI - Unified version with cost tracking and modular workflow."""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .readme_parser import ReadmeParser
from .phase_generator import PhaseGenerator
from .epic_generator import EpicGenerator
from .task_generator import TaskGenerator
from .github_client import GitHubClient
from .cost_tracker import CostTracker, OperationTracker, create_cost_tracker
from .phase_schema import PhaseSchema, PhaseSchemaError, load_phases_from_file
from .phase_preprocessor import PhasePreprocessor, preprocess_phases_with_llm
from .state_manager import StateManager, ExecutionStep, StateManagerError, create_state_manager
from .cli_constraints import CLIConstraints, CLIConstraintError, validate_constraints

console = Console()


def resolve_phase_id(phase_input: str, available_phases: List[Dict[str, Any]]) -> int:
    """Resolve phase input to phase number based on available phases."""
    if not phase_input.isdigit():
        # Show available phases
        phase_list = [f"{i}. {phase['title']}" for i, phase in enumerate(available_phases, 1)]
        raise click.BadParameter(f"Phase must be a number. Available phases:\n" + "\n".join(phase_list))
    
    phase_num = int(phase_input)
    if 1 <= phase_num <= len(available_phases):
        return phase_num
    else:
        phase_list = [f"{i}. {phase['title']}" for i, phase in enumerate(available_phases, 1)]
        raise click.BadParameter(f"Phase number must be between 1 and {len(available_phases)}. Available phases:\n" + "\n".join(phase_list))


def resolve_epic_id(epic_input: str, available_epics: List[Dict[str, Any]]) -> int:
    """Resolve epic input to epic number based on available epics."""
    if not epic_input.isdigit():
        # Show available epics
        epic_list = [f"{i}. {epic.get('title', f'Epic {i}')}" for i, epic in enumerate(available_epics, 1)]
        raise click.BadParameter(f"Epic must be a number. Available epics:\n" + "\n".join(epic_list))
    
    epic_num = int(epic_input)
    if 1 <= epic_num <= len(available_epics):
        return epic_num
    else:
        epic_list = [f"{i}. {epic.get('title', f'Epic {i}')}" for i, epic in enumerate(available_epics, 1)]
        raise click.BadParameter(f"Epic number must be between 1 and {len(available_epics)}. Available epics:\n" + "\n".join(epic_list))


class BacklogManager:
    """Manages the local file structure for generated backlogs with optional cost tracking."""
    
    def __init__(self, owner: str, repo: str, enable_cost_tracking: bool = False):
        self.owner = owner
        self.repo = repo
        # Create .backlog directory inside github-backlog-generator directory
        generator_dir = Path(__file__).parent.parent.parent
        self.base_dir = generator_dir / f".backlog-{owner}-{repo}"
        self.base_dir.mkdir(exist_ok=True)
        
        # Store project metadata
        self.metadata_file = self.base_dir / "metadata.json"
        self.phases_dir = self.base_dir / "phases"
        self.phases_dir.mkdir(exist_ok=True)
        
        # Initialize cost tracker if enabled
        self.cost_tracker = create_cost_tracker(self.base_dir) if enable_cost_tracking else None
    
    def save_metadata(self, project_data: Dict[str, Any]):
        """Save project metadata."""
        metadata = {
            'owner': self.owner,
            'repo': self.repo,
            'project_data': project_data,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_metadata(self) -> Optional[Dict[str, Any]]:
        """Load project metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_phases(self, phases: List[Dict[str, Any]]):
        """Save all phases data."""
        phases_file = self.phases_dir / "phases.json"
        phases_data = {
            'phases': phases,
            'generated_at': datetime.now().isoformat()
        }
        with open(phases_file, 'w') as f:
            json.dump(phases_data, f, indent=2)
        
        # Create directory for each phase
        for i, phase in enumerate(phases, 1):
            phase_dir = self.phases_dir / f"phase{i}"
            phase_dir.mkdir(exist_ok=True)
            
            # Save individual phase data
            phase_file = phase_dir / "phase.json"
            with open(phase_file, 'w') as f:
                json.dump(phase, f, indent=2)
    
    def load_phases(self) -> Optional[List[Dict[str, Any]]]:
        """Load phases data."""
        phases_file = self.phases_dir / "phases.json"
        if phases_file.exists():
            with open(phases_file, 'r') as f:
                return json.load(f)['phases']
        return None
    
    def save_epics(self, phase_num: int, epics: List[Dict[str, Any]]):
        """Save epics for a specific phase."""
        phase_dir = self.phases_dir / f"phase{phase_num}"
        phase_dir.mkdir(exist_ok=True)
        
        epics_file = phase_dir / "epics.json"
        epics_data = {
            'phase_num': phase_num,
            'epics': epics,
            'generated_at': datetime.now().isoformat()
        }
        with open(epics_file, 'w') as f:
            json.dump(epics_data, f, indent=2)
        
        # Create directory for each epic
        for i, epic in enumerate(epics, 1):
            epic_dir = phase_dir / f"epic{i}"
            epic_dir.mkdir(exist_ok=True)
            
            # Save individual epic data
            epic_file = epic_dir / "epic.json"
            with open(epic_file, 'w') as f:
                json.dump(epic, f, indent=2)
    
    def load_epics(self, phase_num: int) -> Optional[List[Dict[str, Any]]]:
        """Load epics for a specific phase."""
        epics_file = self.phases_dir / f"phase{phase_num}" / "epics.json"
        if epics_file.exists():
            with open(epics_file, 'r') as f:
                return json.load(f)['epics']
        return None
    
    def save_issues(self, phase_num: int, epic_num: int, issues: List[Dict[str, Any]]):
        """Save issues for a specific epic."""
        epic_dir = self.phases_dir / f"phase{phase_num}" / f"epic{epic_num}"
        epic_dir.mkdir(exist_ok=True, parents=True)
        
        issues_file = epic_dir / "issues.json"
        issues_data = {
            'phase_num': phase_num,
            'epic_num': epic_num,
            'issues': issues,
            'generated_at': datetime.now().isoformat()
        }
        with open(issues_file, 'w') as f:
            json.dump(issues_data, f, indent=2)
    
    def load_issues(self, phase_num: int, epic_num: int) -> Optional[List[Dict[str, Any]]]:
        """Load issues for a specific epic."""
        issues_file = self.phases_dir / f"phase{phase_num}" / f"epic{epic_num}" / "issues.json"
        if issues_file.exists():
            with open(issues_file, 'r') as f:
                return json.load(f)['issues']
        return None
    
    def get_milestone_mapping(self) -> Dict[int, int]:
        """Load milestone mapping from file."""
        mapping_file = self.base_dir / "milestone_mapping.json"
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.get('milestones', {}).items()}
        return {}
    
    def save_milestone_mapping(self, mapping: Dict[int, int]):
        """Save milestone mapping to file."""
        mapping_file = self.base_dir / "milestone_mapping.json"
        data = {
            'milestones': mapping,
            'updated_at': datetime.now().isoformat()
        }
        with open(mapping_file, 'w') as f:
            json.dump(data, f, indent=2)


@click.group()
@click.option('--cost', is_flag=True, help='Track and display API costs')
@click.option('--time', is_flag=True, help='Track and display operation timing')
@click.pass_context
def cli(ctx, cost: bool, time: bool):
    """GitHub Backlog Generator - Unified CLI with optional cost and timing tracking."""
    load_dotenv()
    
    # Store flags in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['cost_tracking'] = cost
    ctx.obj['time_tracking'] = time


@cli.command()
@click.argument('repo_url')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--dry-run', is_flag=True, help='Generate without creating GitHub items')
@click.pass_context
def init(ctx, repo_url: str, api_key: str, github_token: str, dry_run: bool):
    """Initialize project and generate all phases with optional cost/timing tracking."""
    
    cost_tracking = ctx.obj.get('cost_tracking', False)
    time_tracking = ctx.obj.get('time_tracking', False)
    
    # Start session timing
    session_start = time.time()
    
    # Validate API keys
    if not api_key:
        api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found![/red]")
        sys.exit(1)
    
    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
    
    with console.status("[bold green]Processing repository...") as status:
        # Initialize GitHub client
        github_client = GitHubClient(github_token) if github_token else None
        
        # Parse repository URL
        status.update("Parsing repository URL...")
        try:
            if github_client:
                owner, repo_name = github_client.parse_repo_url(repo_url)
            else:
                match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo_url)
                if match:
                    owner, repo_name = match.groups()
                else:
                    raise ValueError("Invalid GitHub URL")
            
            console.print(f"[green]✓[/green] Repository: {owner}/{repo_name}")
        except Exception as e:
            console.print(f"[red]Error parsing repository URL: {e}[/red]")
            sys.exit(1)
        
        # Initialize backlog manager with cost tracking
        manager = BacklogManager(owner, repo_name, enable_cost_tracking=cost_tracking or time_tracking)
        
        # Fetch README
        readme_start = time.time()
        status.update("Fetching README from repository...")
        try:
            if github_client:
                readme_content = github_client.sparse_checkout_readme(owner, repo_name)
            else:
                import requests
                response = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/README.md")
                if response.status_code == 404:
                    response = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo_name}/master/README.md")
                response.raise_for_status()
                readme_content = response.text
            
            console.print("[green]✓[/green] README fetched successfully")
        except Exception as e:
            console.print(f"[red]Error fetching README: {e}[/red]")
            sys.exit(1)
        
        readme_duration = time.time() - readme_start
        
        # Parse README
        parsing_start = time.time()
        status.update("Analyzing README content...")
        parser = ReadmeParser()
        try:
            if manager.cost_tracker:
                with OperationTracker(manager.cost_tracker, 'readme_analysis'):
                    project_data = parser.parse_readme_content(readme_content)
            else:
                project_data = parser.parse_readme_content(readme_content)
                
            console.print("[green]✓[/green] README analyzed successfully")
            
            # Save project metadata
            manager.save_metadata(project_data)
        except Exception as e:
            console.print(f"[red]Error parsing README: {e}[/red]")
            sys.exit(1)
        
        parsing_duration = time.time() - parsing_start
    
    # Display project info
    console.print("\n[bold]Project Information:[/bold]")
    info_table = Table(show_header=False, box=None)
    info_table.add_column("Field", style="cyan")
    info_table.add_column("Value")
    
    info_table.add_row("Repository", f"{owner}/{repo_name}")
    info_table.add_row("Title", project_data['title'])
    info_table.add_row("Domain", project_data['domain'])
    info_table.add_row("Complexity", project_data['complexity'])
    info_table.add_row("Features", str(len(project_data['features'])))
    
    console.print(info_table)
    
    # Generate phases using AI with cost tracking
    console.print("\n[bold]Generating AI-driven phases...[/bold]\n")
    
    phases_start = time.time()
    try:
        phase_generator = PhaseGenerator(api_key)
        
        if manager.cost_tracker:
            with OperationTracker(manager.cost_tracker, 'phase_generation'):
                generated_phases = phase_generator.generate_phases(project_data)
        else:
            generated_phases = phase_generator.generate_phases(project_data)
        
        # Convert to expected format with numbering
        phases = []
        for i, phase in enumerate(generated_phases, 1):
            phase_data = {
                'number': i,
                'title': phase['title'],
                'description': phase['description'],
                'id': phase['id'],
                'dueDate': phase.get('dueDate', (datetime.now() + timedelta(days=i * 14)).isoformat()),
                'suggestedRoles': phase.get('suggestedRoles', [])
            }
            phases.append(phase_data)
            console.print(f"[green]✓[/green] Phase {i}: {phase_data['title']}")
        
        console.print(f"\n[cyan]Generated {len(phases)} AI-customized phases![/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error: AI phase generation failed: {e}[/red]")
        sys.exit(1)
    
    phases_duration = time.time() - phases_start
    
    # Save phases
    manager.save_phases(phases)
    
    console.print(f"\n[bold green]Initialization complete![/bold green]")
    console.print(f"\nLocal directory created: [cyan]{manager.base_dir}[/cyan]")
    
    # Display timing and cost information if requested
    session_duration = time.time() - session_start
    
    if time_tracking:
        console.print(f"\n[bold]⏱️  Timing Report:[/bold]")
        console.print(f"README Fetch: {readme_duration:.2f}s")
        console.print(f"README Parse: {parsing_duration:.2f}s") 
        console.print(f"Phase Generation: {phases_duration:.2f}s")
        console.print(f"Total Session: {session_duration:.2f}s")
    
    if cost_tracking and manager.cost_tracker:
        console.print(f"\n[bold]💰 Cost Report:[/bold]")
        console.print(manager.cost_tracker.format_cost_report())
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Create milestones: github-backlog milestones")
    console.print("2. Generate epics: github-backlog generate --phase N")
    console.print("3. Generate issues: github-backlog generate --phase N --epic M")


@cli.command()
@click.argument('repo_url')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--dry-run', is_flag=True, help='Show what would be created')
@click.pass_context
def milestones(ctx, repo_url: str, github_token: str, dry_run: bool):
    """Create all GitHub milestones from generated phases."""
    
    time_tracking = ctx.obj.get('time_tracking', False)
    session_start = time.time()
    
    # Validate GitHub token
    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        console.print("[red]Error: GITHUB_TOKEN not found![/red]")
        sys.exit(1)
    
    # Initialize GitHub client
    github_client = GitHubClient(github_token)
    
    # Parse repository URL
    try:
        owner, repo_name = github_client.parse_repo_url(repo_url)
        console.print(f"[green]✓[/green] Repository: {owner}/{repo_name}")
    except Exception as e:
        console.print(f"[red]Error parsing repository URL: {e}[/red]")
        sys.exit(1)
    
    # Initialize backlog manager
    manager = BacklogManager(owner, repo_name)
    
    # Load phases
    phases = manager.load_phases()
    if not phases:
        console.print("[red]Error: No phases found. Run 'github-backlog init' first.[/red]")
        sys.exit(1)
    
    # Display what will be created
    console.print("\n[bold]Creating milestones for all phases:[/bold]\n")
    
    table = Table(show_header=True)
    table.add_column("Phase", style="cyan", width=5)
    table.add_column("Title", style="green")
    table.add_column("Due Date", style="yellow")
    
    for phase in phases:
        due_date = datetime.fromisoformat(phase['dueDate']).strftime("%Y-%m-%d")
        table.add_row(str(phase['number']), phase['title'], due_date)
    
    console.print(table)
    
    if dry_run:
        console.print("\n[yellow]Dry run mode:[/yellow] Milestones will not be created.")
        return
    
    # Create milestones
    console.print("\n[bold]Creating milestones...[/bold]\n")
    
    milestone_mapping = {}
    creation_start = time.time()
    
    with console.status("[bold green]Creating milestones...") as status:
        for phase in phases:
            try:
                phase_data = {
                    'id': phase['id'],
                    'title': phase['title'],
                    'description': phase['description'],
                    'dueDate': phase['dueDate']
                }
                
                urls = github_client.create_milestones(owner, repo_name, [phase_data])
                
                # Extract milestone number
                milestone_match = re.search(r'/milestone/(\d+)$', urls[0])
                if milestone_match:
                    milestone_mapping[phase['number']] = int(milestone_match.group(1))
                
                console.print(f"[green]✓[/green] Phase {phase['number']}: {phase['title']}")
                
            except Exception as e:
                console.print(f"[red]✗[/red] Phase {phase['number']}: {e}")
    
    creation_duration = time.time() - creation_start
    
    # Save milestone mapping
    if milestone_mapping:
        manager.save_milestone_mapping(milestone_mapping)
        console.print(f"\n[green]✓[/green] Created {len(milestone_mapping)} milestones successfully!")
    
    # Display timing if requested
    if time_tracking:
        session_duration = time.time() - session_start
        console.print(f"\n[bold]⏱️  Timing Report:[/bold]")
        console.print(f"Milestone Creation: {creation_duration:.2f}s")
        console.print(f"Total Session: {session_duration:.2f}s")


@cli.command()
@click.argument('repo_url')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--phase', '-p', type=str, help='Phase number (run without --phase to see available phases)')
@click.option('--epic', '-e', type=str, help='Epic number (run without --epic to see available epics)')
@click.option('--dry-run', is_flag=True, help='Generate without creating GitHub items')
@click.option('--all-epics', is_flag=True, help='Generate issues for all epics in the phase')
@click.pass_context
def generate(ctx, repo_url: str, api_key: str, github_token: str, phase: Optional[str], epic: Optional[str], 
            dry_run: bool, all_epics: bool):
    """Generate epics for a phase or issues for an epic with optional cost/timing tracking."""
    
    cost_tracking = ctx.obj.get('cost_tracking', False)
    time_tracking = ctx.obj.get('time_tracking', False)
    
    if epic and all_epics:
        console.print("[red]Error: Cannot specify both --epic and --all-epics[/red]")
        sys.exit(1)
    
    # Validate API keys
    if not api_key:
        api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found![/red]")
        sys.exit(1)
    
    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
    
    # Initialize GitHub client
    github_client = GitHubClient(github_token) if github_token and not dry_run else None
    
    # Parse repository URL
    try:
        if github_client:
            owner, repo_name = github_client.parse_repo_url(repo_url)
        else:
            match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo_url)
            if match:
                owner, repo_name = match.groups()
            else:
                raise ValueError("Invalid GitHub URL")
        
        console.print(f"[green]✓[/green] Repository: {owner}/{repo_name}")
    except Exception as e:
        console.print(f"[red]Error parsing repository URL: {e}[/red]")
        sys.exit(1)
    
    # Initialize backlog manager with cost tracking
    manager = BacklogManager(owner, repo_name, enable_cost_tracking=cost_tracking or time_tracking)
    
    # Load project metadata
    metadata = manager.load_metadata()
    if not metadata:
        console.print("[red]Error: Project not initialized. Run 'github-backlog init' first.[/red]")
        sys.exit(1)
    
    project_data = metadata['project_data']
    
    # Load phases
    phases = manager.load_phases()
    if not phases:
        console.print("[red]Error: Phase data not found. Run 'github-backlog init' first.[/red]")
        sys.exit(1)
    
    # If no phase specified, show available phases
    if phase is None:
        console.print("\n[bold]Available phases:[/bold]\n")
        
        table = Table(show_header=True)
        table.add_column("Phase", style="cyan", width=5)
        table.add_column("Title", style="green")
        table.add_column("Description", style="dim")
        
        for i, phase_data in enumerate(phases, 1):
            table.add_row(str(i), phase_data['title'], phase_data['description'][:80] + "...")
        
        console.print(table)
        console.print("\n[bold]Usage:[/bold]")
        console.print(f"  github-backlog generate {repo_url} --phase N")
        console.print(f"  github-backlog generate {repo_url} --phase N --epic M")
        return
    
    # Resolve phase to number
    try:
        phase_num = resolve_phase_id(phase, phases)
    except click.BadParameter as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    
    phase_data = phases[phase_num - 1]
    
    # Load milestone mapping
    milestone_mapping = manager.get_milestone_mapping()
    
    if epic is None and not all_epics:
        # Generate epics for the phase
        console.print(f"\n[bold]Generating epics for Phase {phase_num}: {phase_data['title']}[/bold]\n")
        
        generation_start = time.time()
        with console.status("[bold green]Generating epics...") as status:
            epic_generator = EpicGenerator(api_key)
            
            try:
                if manager.cost_tracker:
                    with OperationTracker(manager.cost_tracker, 'epic_generation'):
                        epics = epic_generator.generate_epics_for_phase(
                            phase_num, phase_data['title'], phase_data['description'], project_data
                        )
                else:
                    epics = epic_generator.generate_epics_for_phase(
                        phase_num, phase_data['title'], phase_data['description'], project_data
                    )
                
                console.print(f"[green]✓[/green] Generated {len(epics)} epics")
                
                # Save epics
                manager.save_epics(phase_num, epics)
                
            except Exception as e:
                console.print(f"[red]Error generating epics: {e}[/red]")
                sys.exit(1)
        
        generation_duration = time.time() - generation_start
        
        # Display epics
        console.print("\n[bold]Generated Epics:[/bold]\n")
        for i, epic in enumerate(epics, 1):
            console.print(f"[cyan]{i}.[/cyan] {epic['title']}")
            console.print(f"   [dim]{epic['description'][:100]}...[/dim]\n")
        
        # Create epics in GitHub if not dry run
        if not dry_run and github_client and phase_num in milestone_mapping:
            console.print("\n[bold]Creating epics in GitHub...[/bold]\n")
            milestone_number = milestone_mapping[phase_num]
            
            github_start = time.time()
            with console.status("[bold green]Creating epic issues...") as status:
                for i, epic in enumerate(epics, 1):
                    try:
                        epic_phase_data = {
                            'id': f'phase-{phase_num}',
                            'title': epic['title'],
                            'description': epic['description']
                        }
                        
                        epic_data = {
                            'roles': epic['suggestedRoles'],
                            'tasks': []  # Don't create tasks yet
                        }
                        
                        result = github_client.create_epic_only(
                            owner, repo_name, epic_phase_data, epic_data, milestone_number
                        )
                        
                        # Store epic number in local data
                        epic['github_number'] = result['number']
                        epic['github_url'] = result['url']
                        
                        console.print(f"[green]✓[/green] Created Epic {i}: {epic['title']}")
                        
                    except Exception as e:
                        console.print(f"[red]✗[/red] Failed to create Epic {i}: {e}")
                
                # Save updated epics with GitHub numbers
                manager.save_epics(phase_num, epics)
            
            github_duration = time.time() - github_start
        
        # Display timing if requested
        if time_tracking:
            console.print(f"\n[bold]⏱️  Timing Report:[/bold]")
            console.print(f"Epic Generation: {generation_duration:.2f}s")
            if 'github_duration' in locals():
                console.print(f"GitHub Creation: {github_duration:.2f}s")
        
        # Display cost information if requested
        if cost_tracking and manager.cost_tracker:
            console.print(f"\n[bold]💰 Cost Report:[/bold]")
            console.print(manager.cost_tracker.format_cost_report())
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"Generate issues for specific epic: github-backlog generate {repo_url} --phase {phase_num} --epic N")
        console.print(f"Generate issues for all epics: github-backlog generate {repo_url} --phase {phase_num} --all-epics")
    
    else:
        # Generate issues for epic(s) - rest of the function remains the same
        epics_to_process = []
        
        # Load epics
        epics = manager.load_epics(phase_num)
        if not epics:
            console.print(f"[red]Error: No epics found for phase {phase_num}. Generate epics first.[/red]")
            sys.exit(1)
        
        if all_epics:
            epics_to_process = [(i+1, epic) for i, epic in enumerate(epics)]
            console.print(f"\n[bold]Generating issues for all {len(epics)} epics in Phase {phase_num}[/bold]\n")
        else:
            # Resolve epic to number
            try:
                epic_num = resolve_epic_id(epic, epics)
            except click.BadParameter as e:
                console.print(f"[red]Error: {e}[/red]")
                sys.exit(1)
            
            epics_to_process = [(epic_num, epics[epic_num - 1])]
            console.print(f"\n[bold]Generating issues for Epic {epic_num}: {epics[epic_num - 1]['title']}[/bold]\n")
        
        # Generate issues for each epic
        task_generator = TaskGenerator(api_key)
        
        total_generation_start = time.time()
        for epic_num, epic_data in epics_to_process:
            console.print(f"\n[cyan]Epic {epic_num}: {epic_data['title']}[/cyan]")
            
            epic_start = time.time()
            with console.status(f"[bold green]Generating issues for Epic {epic_num}...") as status:
                try:
                    # Generate tasks with cost tracking
                    if manager.cost_tracker:
                        with OperationTracker(manager.cost_tracker, 'task_generation'):
                            tasks = task_generator.generate_tasks_for_epic(
                                epic_data, phase_data['title'], project_data
                            )
                    else:
                        tasks = task_generator.generate_tasks_for_epic(
                            epic_data, phase_data['title'], project_data
                        )
                    
                    console.print(f"[green]✓[/green] Generated {len(tasks)} issues")
                    
                    # Generate detailed descriptions with cost tracking
                    issues = []
                    for task in tasks:
                        if manager.cost_tracker:
                            with OperationTracker(manager.cost_tracker, 'task_description'):
                                desc = task_generator.generate_task_description(
                                    task, epic_data, phase_data['title'], project_data
                                )
                        else:
                            desc = task_generator.generate_task_description(
                                task, epic_data, phase_data['title'], project_data
                            )
                        full_issue = {**task, **desc}
                        issues.append(full_issue)
                    
                    # Save issues
                    manager.save_issues(phase_num, epic_num, issues)
                    
                    # Display issues
                    for i, issue in enumerate(issues, 1):
                        console.print(f"  {i}. {issue['title']} ({issue['priority']})")
                    
                    # Create issues in GitHub if not dry run
                    if not dry_run and github_client and phase_num in milestone_mapping:
                        milestone_number = milestone_mapping[phase_num]
                        epic_github_number = epic_data.get('github_number')
                        
                        if not epic_github_number:
                            console.print(f"  [yellow]Warning: Epic not found in GitHub, skipping issue creation[/yellow]")
                            continue
                        
                        status.update(f"Creating issues in GitHub for Epic {epic_num}...")
                        
                        for i, issue in enumerate(issues, 1):
                            try:
                                task_url = github_client.create_task_issue(
                                    owner, repo_name, issue,
                                    epic_github_number, f'phase-{phase_num}', milestone_number
                                )
                                console.print(f"  [green]✓[/green] Created Issue {i}: {issue['title']}")
                            except Exception as e:
                                console.print(f"  [red]✗[/red] Failed to create Issue {i}: {e}")
                    
                except Exception as e:
                    console.print(f"[red]Error generating issues: {e}[/red]")
            
            epic_duration = time.time() - epic_start
            if time_tracking:
                console.print(f"  [dim]Epic {epic_num} completed in {epic_duration:.2f}s[/dim]")
        
        total_generation_duration = time.time() - total_generation_start
        
        # Display final timing and cost reports
        if time_tracking:
            console.print(f"\n[bold]⏱️  Total Generation Time: {total_generation_duration:.2f}s[/bold]")
        
        if cost_tracking and manager.cost_tracker:
            console.print(f"\n[bold]💰 Final Cost Report:[/bold]")
            console.print(manager.cost_tracker.format_cost_report())
        
        console.print(f"\n[green]✓[/green] Issue generation complete!")


@cli.command()
@click.argument('repo_url', required=False)
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table', 
              help='Output format: table or json')
@click.pass_context
def status(ctx, repo_url: Optional[str], output: str):
    """Show hierarchical status of phases, epics, and issues with output format options."""
    
    cost_tracking = ctx.obj.get('cost_tracking', False)
    time_tracking = ctx.obj.get('time_tracking', False)
    
    # Auto-detect repo URL from existing project if not provided
    if not repo_url:
        from pathlib import Path
        generator_dir = Path(__file__).parent.parent.parent
        backlog_dirs = list(generator_dir.glob('.backlog-*'))
        
        if backlog_dirs:
            dir_name = backlog_dirs[0].name
            parts = dir_name.replace('.backlog-', '').split('-', 1)
            if len(parts) == 2:
                owner, repo_name = parts
                repo_url = f"https://github.com/{owner}/{repo_name}"
                console.print(f"[cyan]Auto-detected repository: {repo_url}[/cyan]")
        
        if not repo_url:
            console.print("[red]Error: No repository URL provided and no initialized project found.[/red]")
            console.print("Usage: github-backlog-generator status <repo_url> [--output json|table]")
            sys.exit(1)
    
    # Parse repository URL
    match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo_url)
    if not match:
        console.print("[red]Error: Invalid GitHub URL[/red]")
        sys.exit(1)
    
    owner, repo_name = match.groups()
    manager = BacklogManager(owner, repo_name, enable_cost_tracking=cost_tracking)
    
    if not manager.base_dir.exists():
        console.print(f"[red]No backlog found for {owner}/{repo_name}[/red]")
        console.print("Run 'github-backlog-generator init' to get started.")
        sys.exit(1)
    
    # Load metadata and phases
    metadata = manager.load_metadata()
    phases_data = manager.load_phases()
    
    if not phases_data:
        console.print("[yellow]No phases generated yet.[/yellow]")
        return
    
    # Build hierarchical structure
    status_data = {
        'project': {
            'title': metadata['project_data']['title'] if metadata else f"{owner}/{repo_name}",
            'repository': f"{owner}/{repo_name}",
            'created': metadata['created_at'][:10] if metadata else 'unknown'
        },
        'phases': []
    }
    
    for phase in phases_data:
        phase_num = phase['number']
        epics_data = manager.load_epics(phase_num)
        
        phase_info = {
            'number': phase_num,
            'title': phase['title'],
            'epics': []
        }
        
        if epics_data:
            for i, epic in enumerate(epics_data, 1):
                issues_data = manager.load_issues(phase_num, i)
                
                epic_info = {
                    'number': i,
                    'title': epic['title'],
                    'issues': []
                }
                
                if issues_data:
                    for issue in issues_data:
                        epic_info['issues'].append({
                            'title': issue['title'],
                            'priority': issue.get('priority', 'medium')
                        })
                
                phase_info['epics'].append(epic_info)
        
        status_data['phases'].append(phase_info)
    
    # Output based on format
    if output == 'json':
        console.print(json.dumps(status_data, indent=2))
    else:
        # Table format with both old and new information
        console.print(f"\n[bold]Project: {status_data['project']['title']}[/bold]")
        console.print(f"Repository: {status_data['project']['repository']}")
        console.print(f"Created: {status_data['project']['created']}")
        
        # Original table format for backward compatibility
        console.print("\n[bold]Generation Status:[/bold]\n")
        table = Table(show_header=True)
        table.add_column("Phase", style="cyan", width=5)
        table.add_column("Title", style="green", width=30)
        table.add_column("Epics", style="yellow", width=10)
        table.add_column("Issues", style="magenta", width=10)
        table.add_column("Status", width=15)
        
        milestone_mapping = manager.get_milestone_mapping()
        
        for phase in phases_data:
            phase_num = phase['number']
            epics = manager.load_epics(phase_num)
            
            epic_count = len(epics) if epics else 0
            issue_count = 0
            
            if epics:
                for i in range(1, len(epics) + 1):
                    issues = manager.load_issues(phase_num, i)
                    if issues:
                        issue_count += len(issues)
            
            # Determine status
            if phase_num in milestone_mapping:
                if issue_count > 0:
                    status = "✓ Complete"
                elif epic_count > 0:
                    status = "◐ Epics only"
                else:
                    status = "○ Milestone only"
            else:
                if epic_count > 0:
                    status = "◔ Generated"
                else:
                    status = "◯ Not started"
            
            table.add_row(
                str(phase_num),
                phase['title'],
                str(epic_count) if epic_count > 0 else "-",
                str(issue_count) if issue_count > 0 else "-",
                status
            )
        
        console.print(table)
        
        # Show hierarchical structure
        console.print("\n[bold]Hierarchical Structure:[/bold]\n")
        
        for phase in status_data['phases']:
            console.print(f"[cyan]📅 Phase {phase['number']}: {phase['title']}[/cyan]")
            
            if phase['epics']:
                for epic in phase['epics']:
                    console.print(f"  [green]📋 Epic {epic['number']}: {epic['title']}[/green]")
                    
                    if epic['issues']:
                        for issue in epic['issues']:
                            priority_color = "red" if issue['priority'] == 'high' else "yellow" if issue['priority'] == 'medium' else "dim"
                            console.print(f"    [white]✅ {issue['title']}[/white] [{priority_color}]({issue['priority']})[/{priority_color}]")
                    else:
                        console.print("    [dim]   (no issues generated)[/dim]")
            else:
                console.print("  [dim](no epics generated)[/dim]")
            console.print()
        
        # Show cost and timing information if available and requested
        if (cost_tracking or time_tracking) and manager.cost_tracker:
            if cost_tracking:
                console.print(f"\n{manager.cost_tracker.format_cost_report()}")
            elif time_tracking:
                console.print(f"\n{manager.cost_tracker.format_timing_report()}")
        
        # Show directory structure
        console.print(f"\n[bold]Local directory:[/bold] {manager.base_dir}")
        console.print("\nUse 'tree' command to explore the file structure.")


@cli.command()
@click.argument('repo_url', required=False)
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--dry-run', is_flag=True, help='Show what would be created')
@click.pass_context
def phases(ctx, repo_url: Optional[str], github_token: str, dry_run: bool):
    """Create all GitHub milestones from generated phases (alias for milestones command)."""
    
    # Auto-detect repo URL from existing project if not provided
    if not repo_url:
        # Look for existing backlog directories
        from pathlib import Path
        generator_dir = Path(__file__).parent.parent.parent
        backlog_dirs = list(generator_dir.glob('.backlog-*'))
        
        if backlog_dirs:
            # Extract repo info from directory name
            dir_name = backlog_dirs[0].name
            parts = dir_name.replace('.backlog-', '').split('-', 1)
            if len(parts) == 2:
                owner, repo_name = parts
                repo_url = f"https://github.com/{owner}/{repo_name}"
                console.print(f"[cyan]Auto-detected repository: {repo_url}[/cyan]")
        
        if not repo_url:
            console.print("[red]Error: No repository URL provided and no initialized project found.[/red]")
            console.print("Usage: github-backlog-generator phases <repo_url>")
            console.print("   or: github-backlog-generator phases (in initialized project directory)")
            sys.exit(1)
    
    # Call the existing milestones command with the same parameters
    ctx.invoke(milestones, repo_url=repo_url, github_token=github_token, dry_run=dry_run)


@cli.command()
@click.argument('repo_url', required=False)
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--phase', '-p', type=str, help='Phase number (generate epics for specific phase)')
@click.option('--dry-run', is_flag=True, help='Generate without creating GitHub items')
@click.pass_context
def epics(ctx, repo_url: Optional[str], api_key: str, github_token: str, phase: Optional[str], dry_run: bool):
    """Generate epics for all phases or a specific phase."""
    
    # Auto-detect repo URL from existing project if not provided
    if not repo_url:
        from pathlib import Path
        generator_dir = Path(__file__).parent.parent.parent
        backlog_dirs = list(generator_dir.glob('.backlog-*'))
        
        if backlog_dirs:
            dir_name = backlog_dirs[0].name
            parts = dir_name.replace('.backlog-', '').split('-', 1)
            if len(parts) == 2:
                owner, repo_name = parts
                repo_url = f"https://github.com/{owner}/{repo_name}"
                console.print(f"[cyan]Auto-detected repository: {repo_url}[/cyan]")
        
        if not repo_url:
            console.print("[red]Error: No repository URL provided and no initialized project found.[/red]")
            console.print("Usage: github-backlog-generator epics <repo_url> [--phase N]")
            sys.exit(1)
    
    if phase:
        # Generate epics for specific phase
        ctx.invoke(generate, repo_url=repo_url, api_key=api_key, github_token=github_token, 
                  phase=phase, epic=None, dry_run=dry_run, all_epics=False)
    else:
        # Generate epics for all phases
        console.print("[bold]Generating epics for all phases...[/bold]\n")
        
        # Parse repository URL to get manager
        match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo_url)
        if not match:
            console.print("[red]Error: Invalid GitHub URL[/red]")
            sys.exit(1)
        
        owner, repo_name = match.groups()
        manager = BacklogManager(owner, repo_name)
        
        # Load phases to determine how many there are
        phases_data = manager.load_phases()
        if not phases_data:
            console.print("[red]Error: No phases found. Run 'github-backlog-generator init' first.[/red]")
            sys.exit(1)
        
        # Generate epics for each phase
        for i in range(1, len(phases_data) + 1):
            console.print(f"\n[cyan]Phase {i}: {phases_data[i-1]['title']}[/cyan]")
            try:
                ctx.invoke(generate, repo_url=repo_url, api_key=api_key, github_token=github_token, 
                          phase=str(i), epic=None, dry_run=dry_run, all_epics=False)
            except Exception as e:
                console.print(f"[yellow]Warning: Phase {i} completed with issues: {e}[/yellow]")
                
        console.print(f"\n[green]✓[/green] Epic generation complete for all {len(phases_data)} phases!")


@cli.command()
@click.argument('repo_url', required=False)
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--phase', '-p', type=str, help='Phase number (generate issues for specific phase)')
@click.option('--epic', '-e', type=str, help='Epic number (generate issues for specific epic)')
@click.option('--dry-run', is_flag=True, help='Generate without creating GitHub items')
@click.pass_context
def issues(ctx, repo_url: Optional[str], api_key: str, github_token: str, 
          phase: Optional[str], epic: Optional[str], dry_run: bool):
    """Generate issues for all epics across all phases, or for specific phase/epic combinations."""
    
    # Auto-detect repo URL from existing project if not provided
    if not repo_url:
        from pathlib import Path
        generator_dir = Path(__file__).parent.parent.parent
        backlog_dirs = list(generator_dir.glob('.backlog-*'))
        
        if backlog_dirs:
            dir_name = backlog_dirs[0].name
            parts = dir_name.replace('.backlog-', '').split('-', 1)
            if len(parts) == 2:
                owner, repo_name = parts  
                repo_url = f"https://github.com/{owner}/{repo_name}"
                console.print(f"[cyan]Auto-detected repository: {repo_url}[/cyan]")
        
        if not repo_url:
            console.print("[red]Error: No repository URL provided and no initialized project found.[/red]")
            console.print("Usage: github-backlog-generator issues <repo_url> [--phase N] [--epic N]")
            sys.exit(1)
    
    if phase and epic:
        # Generate issues for specific phase and epic
        ctx.invoke(generate, repo_url=repo_url, api_key=api_key, github_token=github_token,
                  phase=phase, epic=epic, dry_run=dry_run, all_epics=False)
    elif phase and not epic:
        # Generate issues for all epics in specific phase
        ctx.invoke(generate, repo_url=repo_url, api_key=api_key, github_token=github_token,
                  phase=phase, epic=None, dry_run=dry_run, all_epics=True)
    else:
        # Generate issues for all epics across all phases
        console.print("[bold]Generating issues for all epics across all phases...[/bold]\n")
        
        # Parse repository URL to get manager
        match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo_url)
        if not match:
            console.print("[red]Error: Invalid GitHub URL[/red]")
            sys.exit(1)
        
        owner, repo_name = match.groups()
        manager = BacklogManager(owner, repo_name)
        
        # Load phases to determine how many there are
        phases_data = manager.load_phases()
        if not phases_data:
            console.print("[red]Error: No phases found. Run 'github-backlog-generator init' first.[/red]")
            sys.exit(1)
        
        # Generate issues for each phase with all epics
        for i in range(1, len(phases_data) + 1):
            console.print(f"\n[cyan]Phase {i}: {phases_data[i-1]['title']}[/cyan]")
            try:
                ctx.invoke(generate, repo_url=repo_url, api_key=api_key, github_token=github_token,
                          phase=str(i), epic=None, dry_run=dry_run, all_epics=True)
            except Exception as e:
                console.print(f"[yellow]Warning: Phase {i} completed with issues: {e}[/yellow]")
        
        console.print(f"\n[green]✓[/green] Issue generation complete for all phases!")



@cli.command(name='generate-phases')
@click.option('--output', '-o', default='phases.json', help='Output file path')
@click.option('--show', is_flag=True, help='Display sample content instead of writing file')
def generate_phases_template(output: str, show: bool):
    """Generate a sample phases.json file for customization."""
    
    if show:
        # Display sample content
        sample_content = PhaseSchema.create_sample_phases_json()
        console.print("\n[bold]Sample phases.json content:[/bold]\n")
        console.print(sample_content)
        return
    
    try:
        # Create the sample file
        created_path = PhaseSchema.create_sample_phases_json(output)
        console.print(f"\n[green]✓[/green] Sample phases.json created at: [cyan]{created_path}[/cyan]")
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Edit the phases.json file to customize your project phases")
        console.print("2. Run: github-backlog-generator run --phases ./phases.json --repo owner/repo")
        
        # Display a preview
        raw_data = PhaseSchema.load_and_validate(created_path)
        phases = PhaseSchema.normalize_phases(raw_data)
        PhaseSchema.display_phases_summary(phases)
        
    except Exception as e:
        console.print(f"[red]Error creating phases file:[/red] {e}")
        sys.exit(1)


@cli.command(name='create-milestones')
@click.option('--phases', type=click.Path(exists=True), help='Path to phases.json file (optional if project initialized)')
@click.option('--repo', help='GitHub repository (owner/repo or full URL)')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--dry-run', is_flag=True, help='Preview operations without creating GitHub items')
@click.pass_context
def create_milestones(ctx, phases: Optional[str], repo: Optional[str], github_token: str, dry_run: bool):
    """Create GitHub milestones from phases."""
    
    cost_tracking = ctx.obj.get('cost_tracking', False)
    time_tracking = ctx.obj.get('time_tracking', False)
    
    console.print("[bold]🎯 Creating GitHub Milestones[/bold]\n")
    
    # Determine repository
    if not repo:
        # Try to auto-detect
        from pathlib import Path
        generator_dir = Path(__file__).parent.parent.parent
        backlog_dirs = list(generator_dir.glob('.backlog-*'))
        
        if backlog_dirs:
            dir_name = backlog_dirs[0].name
            parts = dir_name.replace('.backlog-', '').split('-', 1)
            if len(parts) == 2:
                owner, repo_name = parts
                repo = f"https://github.com/{owner}/{repo_name}"
                console.print(f"[cyan]Auto-detected repository: {repo}[/cyan]")
        
        if not repo:
            console.print("[red]Error: No repository specified and no initialized project found.[/red]")
            console.print("Usage: github-backlog-generator create-milestones --repo owner/repo")
            sys.exit(1)
    
    # Load phases
    if phases:
        # Load from specified file
        try:
            custom_phases = load_phases_from_file(phases)
            console.print(f"[green]✓[/green] Loaded {len(custom_phases)} phases from {phases}")
        except Exception as e:
            console.print(f"[red]Error loading phases:[/red] {e}")
            sys.exit(1)
    else:
        # Try to load from existing project
        try:
            match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo)
            if match:
                owner, repo_name = match.groups()
            else:
                owner, repo_name = repo.split('/', 1)
            
            manager = BacklogManager(owner, repo_name)
            custom_phases = manager.load_phases()
            
            if not custom_phases:
                console.print("[red]Error: No phases found in project. Use --phases to specify a phases.json file.[/red]")
                sys.exit(1)
                
            console.print(f"[green]✓[/green] Loaded {len(custom_phases)} phases from project")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
    
    # Call existing milestones functionality
    ctx.invoke(milestones, repo_url=repo, github_token=github_token, dry_run=dry_run)


@cli.command(name='create-epics')
@click.option('--phases', type=click.Path(exists=True), help='Path to phases.json file (optional if project initialized)')
@click.option('--repo', help='GitHub repository (owner/repo or full URL)')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--phase', '-p', type=str, help='Phase number (generate epics for specific phase)')
@click.option('--dry-run', is_flag=True, help='Preview operations without creating GitHub items')
@click.pass_context
def create_epics(ctx, phases: Optional[str], repo: Optional[str], api_key: str, github_token: str, phase: Optional[str], dry_run: bool):
    """Create epics for phases."""
    
    console.print("[bold]📋 Creating Epics[/bold]\n")
    
    # Determine repository
    if not repo:
        # Try to auto-detect
        from pathlib import Path
        generator_dir = Path(__file__).parent.parent.parent
        backlog_dirs = list(generator_dir.glob('.backlog-*'))
        
        if backlog_dirs:
            dir_name = backlog_dirs[0].name
            parts = dir_name.replace('.backlog-', '').split('-', 1)
            if len(parts) == 2:
                owner, repo_name = parts
                repo = f"https://github.com/{owner}/{repo_name}"
                console.print(f"[cyan]Auto-detected repository: {repo}[/cyan]")
        
        if not repo:
            console.print("[red]Error: No repository specified and no initialized project found.[/red]")
            console.print("Usage: github-backlog-generator create-epics --repo owner/repo")
            sys.exit(1)
    
    # Validate API key
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found![/red]")
        sys.exit(1)
    
    # Load phases if specified
    if phases:
        try:
            custom_phases = load_phases_from_file(phases)
            
            # Save to project for consistency
            match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo)
            if match:
                owner, repo_name = match.groups()
            else:
                owner, repo_name = repo.split('/', 1)
            
            manager = BacklogManager(owner, repo_name)
            manager.save_phases(custom_phases)
            console.print(f"[green]✓[/green] Loaded and saved {len(custom_phases)} phases")
        except Exception as e:
            console.print(f"[red]Error loading phases:[/red] {e}")
            sys.exit(1)
    
    # Call existing epics functionality
    ctx.invoke(epics, repo_url=repo, api_key=api_key, github_token=github_token, phase=phase, dry_run=dry_run)


@cli.command(name='create-issues')
@click.option('--phases', type=click.Path(exists=True), help='Path to phases.json file (optional if project initialized)')
@click.option('--repo', help='GitHub repository (owner/repo or full URL)')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--phase', '-p', type=str, help='Phase number (generate issues for specific phase)')
@click.option('--epic', '-e', type=str, help='Epic number (generate issues for specific epic)')
@click.option('--dry-run', is_flag=True, help='Preview operations without creating GitHub items')
@click.pass_context
def create_issues(ctx, phases: Optional[str], repo: Optional[str], api_key: str, github_token: str, 
                 phase: Optional[str], epic: Optional[str], dry_run: bool):
    """Create issues for epics."""
    
    console.print("[bold]✅ Creating Issues[/bold]\n")
    
    # Determine repository
    if not repo:
        # Try to auto-detect
        from pathlib import Path
        generator_dir = Path(__file__).parent.parent.parent
        backlog_dirs = list(generator_dir.glob('.backlog-*'))
        
        if backlog_dirs:
            dir_name = backlog_dirs[0].name
            parts = dir_name.replace('.backlog-', '').split('-', 1)
            if len(parts) == 2:
                owner, repo_name = parts
                repo = f"https://github.com/{owner}/{repo_name}"
                console.print(f"[cyan]Auto-detected repository: {repo}[/cyan]")
        
        if not repo:
            console.print("[red]Error: No repository specified and no initialized project found.[/red]")
            console.print("Usage: github-backlog-generator create-issues --repo owner/repo")
            sys.exit(1)
    
    # Validate API key
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found![/red]")
        sys.exit(1)
    
    # Load phases if specified
    if phases:
        try:
            custom_phases = load_phases_from_file(phases)
            
            # Save to project for consistency
            match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo)
            if match:
                owner, repo_name = match.groups()
            else:
                owner, repo_name = repo.split('/', 1)
            
            manager = BacklogManager(owner, repo_name)
            manager.save_phases(custom_phases)
            console.print(f"[green]✓[/green] Loaded and saved {len(custom_phases)} phases")
        except Exception as e:
            console.print(f"[red]Error loading phases:[/red] {e}")
            sys.exit(1)
    
    # Call existing issues functionality
    ctx.invoke(issues, repo_url=repo, api_key=api_key, github_token=github_token, 
              phase=phase, epic=epic, dry_run=dry_run)


@cli.command()
@click.option('--phases', type=click.Path(), required=True, help='Path to phases.json file')
@click.option('--repo', required=True, help='GitHub repository (owner/repo or full URL)')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--dry-run', is_flag=True, help='Preview operations without creating GitHub items')
@click.option('--secrets-from-env', is_flag=True, help='Load secrets from environment variables')
@click.option('--preprocess-phases', is_flag=True, default=True, help='Enable LLM preprocessing of phases 2-n (default: enabled)')
@click.option('--skip-preprocessing', is_flag=True, help='Skip LLM preprocessing entirely')
@click.option('--force-restart', is_flag=True, help='Force restart even if resumable state exists')
@click.option('--no-resume', is_flag=True, help='Disable resume prompts and start fresh')
@click.pass_context
@validate_constraints(
    require_repo=True,
    require_api_key=True, 
    require_github_token=True,
    require_phases_file=True,
    check_concurrent=True
)
def run(ctx, phases: str, repo: str, api_key: str, github_token: str, dry_run: bool, secrets_from_env: bool, preprocess_phases: bool, skip_preprocessing: bool, force_restart: bool, no_resume: bool, **kwargs):
    """Run the complete backlog generation workflow with custom phases."""
    
    cost_tracking = ctx.obj.get('cost_tracking', False)
    time_tracking = ctx.obj.get('time_tracking', False)
    
    console.print("[bold]🚀 GitHub Backlog Generator - Full Workflow[/bold]\n")
    
    # Extract validated data from constraints decorator
    owner = kwargs.get('owner')
    repo_name = kwargs.get('repo_name')
    custom_phases = kwargs.get('phases_data')
    
    console.print(f"[green]✓[/green] Repository: {owner}/{repo_name}")
    console.print(f"[green]✓[/green] Phases: {len(custom_phases)} loaded and validated")
    
    # Display constraint validation summary
    validation_info = CLIConstraints.validate_command_combination(
        ctx, phases, dry_run, force_restart
    )
    
    if validation_info['warnings']:
        for warning in validation_info['warnings']:
            console.print(f"[yellow]⚠️  {warning}[/yellow]")
    
    if validation_info['suggestions'] and not dry_run:
        console.print(f"\n[dim]💡 Suggestions:[/dim]")
        for suggestion in validation_info['suggestions']:
            console.print(f"[dim]  • {suggestion}[/dim]")
    
    # Build repository URL for GitHub operations
    repo_url = f"https://github.com/{owner}/{repo_name}"
    
    # Initialize components
    github_client = GitHubClient(github_token) if github_token else None
    manager = BacklogManager(owner, repo_name, enable_cost_tracking=cost_tracking or time_tracking)
    
    # Initialize state manager with lock
    try:
        state_manager = create_state_manager(owner, repo_name)
        
        # Check for concurrent execution
        if not force_restart:
            concurrent_info = state_manager.check_concurrent_execution()
            if concurrent_info:
                console.print(f"[red]❌ Another process is already running on {owner}/{repo_name}[/red]")
                console.print(f"Process ID: {concurrent_info.get('pid')}")
                console.print(f"Started: {concurrent_info.get('locked_at')}")
                console.print(f"Command: {concurrent_info.get('command', 'unknown')}")
                console.print("\nUse --force-restart to override (may cause conflicts)")
                sys.exit(1)
        
        # Check for resumable state
        resume_execution = False
        if not force_restart and not no_resume and state_manager.can_resume():
            if state_manager.display_resume_prompt():
                resume_execution = True
                console.print("[green]✓[/green] Resuming from previous execution")
            else:
                console.print("[yellow]Starting fresh execution[/yellow]")
                state_manager.clear_state()
        elif force_restart:
            console.print("[yellow]Force restart requested, clearing previous state[/yellow]")
            state_manager.clear_state()
        
    except StateManagerError as e:
        console.print(f"[red]State management error:[/red] {e}")
        sys.exit(1)
    
    start_time = time.time()
    
    console.print(f"\n[bold]📋 Workflow Plan:[/bold]")
    console.print(f"1. Process {len(custom_phases)} custom phases")
    if preprocess_phases and not skip_preprocessing:
        console.print("   └── Apply LLM preprocessing to phases 2-n")
    console.print("2. Create GitHub milestones")
    console.print("3. Generate epics for all phases")
    console.print("4. Generate issues for all epics")
    console.print("5. Generate summary report")
    
    if dry_run:
        console.print(f"\n[yellow]DRY RUN MODE:[/yellow] No GitHub items will be created")
    
    console.print(f"\n{'='*60}")
    
    # Execute with state management
    try:
        with state_manager:
            # Initialize or resume state
            if not resume_execution:
                execution_options = {
                    'phases_file': phases,
                    'repo': repo,
                    'dry_run': dry_run,
                    'preprocess_phases': preprocess_phases and not skip_preprocessing,
                    'cost_tracking': cost_tracking,
                    'time_tracking': time_tracking
                }
                
                state = state_manager.initialize_state(
                    phases=custom_phases,
                    command='run',
                    options=execution_options
                )
                
                console.print(f"[dim]Execution ID: {state['execution_id']}[/dim]")
            else:
                state = state_manager.load_state()
                custom_phases = state['phases']  # Use phases from state
                console.print(f"[dim]Resuming execution ID: {state['execution_id']}[/dim]")
            
            current_step = state_manager.get_current_step()
            
            # Step 1: Process phases (skip if already completed)
            if not state_manager.is_step_completed(ExecutionStep.PHASES_LOADED):
                console.print("\n[bold cyan]Step 1: Processing Custom Phases[/bold cyan]")
                manager.save_phases(custom_phases)
                state_manager.update_step(
                    ExecutionStep.PHASES_LOADED,
                    f"Loaded {len(custom_phases)} custom phases",
                    {'phases_count': len(custom_phases)}
                )
                console.print(f"[green]✓[/green] Saved {len(custom_phases)} phases")
            else:
                console.print("\n[dim]Step 1: Custom phases already processed (skipped)[/dim]")
            
            # Step 1b: Preprocess phases (skip if already completed or disabled)
            if (preprocess_phases and not skip_preprocessing and 
                not state_manager.is_step_completed(ExecutionStep.PHASES_PREPROCESSED)):
                
                console.print("[cyan]Applying LLM preprocessing to phases 2-n...[/cyan]")
                
                project_context = None
                if manager.load_metadata():
                    project_context = manager.load_metadata().get('project_data', {})
                
                try:
                    if manager.cost_tracker:
                        with OperationTracker(manager.cost_tracker, 'phase_preprocessing'):
                            final_phases = preprocess_phases_with_llm(
                                phases=custom_phases,
                                api_key=api_key,
                                project_context=project_context
                            )
                    else:
                        final_phases = preprocess_phases_with_llm(
                            phases=custom_phases,
                            api_key=api_key,
                            project_context=project_context
                        )
                    
                    manager.save_phases(final_phases)
                    state_manager.update_step(
                        ExecutionStep.PHASES_PREPROCESSED,
                        "Phase preprocessing completed",
                        {'preprocessed_phases': len(final_phases)}
                    )
                    console.print(f"[green]✓[/green] Phase preprocessing completed")
                    
                except Exception as e:
                    console.print(f"[yellow]Warning: Phase preprocessing failed, using original phases[/yellow]")
                    console.print(f"[dim]Error: {e}[/dim]")
                    final_phases = custom_phases
                    
                    state_manager.update_step(
                        ExecutionStep.PHASES_PREPROCESSED,
                        f"Phase preprocessing failed: {e}",
                        {'preprocessing_error': str(e)}
                    )
            elif state_manager.is_step_completed(ExecutionStep.PHASES_PREPROCESSED):
                console.print("[dim]Phase preprocessing already completed (skipped)[/dim]")
                final_phases = custom_phases
            else:
                console.print("[dim]Phase preprocessing disabled[/dim]")
                final_phases = custom_phases
            
            # Step 2: Create milestones (skip if already completed)
            if not state_manager.is_step_completed(ExecutionStep.MILESTONES_CREATED):
                console.print("\n[bold cyan]Step 2: Creating GitHub Milestones[/bold cyan]")
                ctx.invoke(phases, repo_url=repo_url, github_token=github_token, dry_run=dry_run)
                state_manager.update_step(
                    ExecutionStep.MILESTONES_CREATED,
                    "GitHub milestones created"
                )
            else:
                console.print("\n[dim]Step 2: GitHub milestones already created (skipped)[/dim]")
            
            # Step 3: Generate epics (skip if already completed)
            if not state_manager.is_step_completed(ExecutionStep.EPICS_GENERATED):
                console.print("\n[bold cyan]Step 3: Generating Epics[/bold cyan]")
                ctx.invoke(epics, repo_url=repo_url, api_key=api_key, github_token=github_token, phase=None, dry_run=dry_run)
                state_manager.update_step(
                    ExecutionStep.EPICS_GENERATED,
                    "Epics generated for all phases"
                )
            else:
                console.print("\n[dim]Step 3: Epics already generated (skipped)[/dim]")
            
            # Step 4: Generate issues (skip if already completed)
            if not state_manager.is_step_completed(ExecutionStep.ISSUES_GENERATED):
                console.print("\n[bold cyan]Step 4: Generating Issues[/bold cyan]")
                ctx.invoke(issues, repo_url=repo_url, api_key=api_key, github_token=github_token, phase=None, epic=None, dry_run=dry_run)
                state_manager.update_step(
                    ExecutionStep.ISSUES_GENERATED,
                    "Issues generated for all epics"
                )
            else:
                console.print("\n[dim]Step 4: Issues already generated (skipped)[/dim]")
            
            # Step 5: Mark as completed
            console.print("\n[bold cyan]Step 5: Workflow Complete[/bold cyan]")
            state_manager.update_step(
                ExecutionStep.COMPLETED,
                "Full workflow completed successfully"
            )
            
            total_time = time.time() - start_time
            
            console.print(f"\n[bold green]🎉 Workflow completed successfully![/bold green]")
            console.print(f"⏱️  Total time: {total_time:.2f}s")
            console.print(f"📊 Repository: {owner}/{repo_name}")
            console.print(f"📋 Phases processed: {len(final_phases)}")
            
            if cost_tracking and manager.cost_tracker:
                console.print(f"\n[bold]💰 Cost Report:[/bold]")
                console.print(manager.cost_tracker.format_cost_report())
            
            # Show final status
            console.print(f"\n[bold]📈 Final Status:[/bold]")
            ctx.invoke(enhanced_status, repo_url=repo_url, output='table')
            
            # Clean up state on successful completion
            state_manager.clear_state()
            
    except KeyboardInterrupt:
        console.print(f"\n[yellow]⚠️  Execution interrupted by user[/yellow]")
        console.print(f"⏱️  Time elapsed: {time.time() - start_time:.2f}s")
        console.print(f"[cyan]💾 State saved for resumption[/cyan]")
        console.print(f"Run the same command again to resume from the last checkpoint")
        sys.exit(130)  # Standard exit code for SIGINT
        
    except Exception as e:
        # Save error state before exiting
        try:
            error_info = {
                'error': str(e),
                'error_type': type(e).__name__,
                'failed_at_step': state_manager.get_current_step().value if state_manager.get_current_step() else 'unknown'
            }
            state_manager.update_step(
                state_manager.get_current_step() or ExecutionStep.INIT,
                f"Execution failed: {e}",
                error_info
            )
        except:
            pass  # Don't fail on state save failure
        
        console.print(f"\n[red]❌ Workflow failed:[/red] {e}")
        console.print(f"⏱️  Time elapsed: {time.time() - start_time:.2f}s")
        console.print(f"[cyan]💾 State saved for resumption[/cyan]")
        
        if hasattr(e, '__traceback__'):
            import traceback
            console.print(f"\n[dim]Debug info:[/dim]")
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        sys.exit(1)


@cli.command()
@click.option('--repo', '-r', required=True, help='Repository in format owner/repo')
@click.option('--output-format', '-f', type=click.Choice(['table', 'json', 'markdown']), default='table', 
              help='Output format for summary')
@click.option('--output-file', '-o', help='Save summary to file (format inferred from extension)')
@click.option('--include-costs', is_flag=True, help='Include detailed cost breakdown')
@click.option('--include-timing', is_flag=True, help='Include timing information from state')
@validate_constraints(require_repo=True)
def summarize(repo: str, output_format: str, output_file: str, include_costs: bool, include_timing: bool, **kwargs):
    """Generate enhanced summary with detailed metrics and cost estimates."""
    
    # Extract validated data from constraints decorator
    owner = kwargs.get('owner')
    repo_name = kwargs.get('repo_name')
    
    console.print(f"\n[bold cyan]📊 Enhanced Summary Report[/bold cyan]")
    console.print(f"[cyan]Repository: {owner}/{repo_name}[/cyan]")
    console.print("=" * 50)
    
    # Validate output file if provided
    if output_file:
        try:
            output_file = CLIConstraints.validate_output_file_path(output_file)
        except CLIConstraintError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    try:
        # Initialize managers
        manager = RepositoryManager(owner, repo_name)
        
        # Try to load state for timing information
        state_manager = create_state_manager(owner, repo_name)
        execution_state = state_manager.load_state() if state_manager else None
        
        # Load phases and calculate basic metrics
        phases = manager.load_phases()
        if not phases:
            console.print("[yellow]No phases found. Run the workflow first.[/yellow]")
            sys.exit(1)
        
        # Load epics and issues
        epics = manager.load_epics()
        issues = manager.load_issues()
        
        # Calculate metrics
        total_phases = len(phases)
        total_epics = len(epics) if epics else 0
        total_issues = len(issues) if issues else 0
        
        # Calculate timing information
        timing_info = {}
        if include_timing and execution_state:
            timing_info = calculate_timing_metrics(execution_state)
        
        # Calculate cost information
        cost_info = {}
        if include_costs:
            cost_info = calculate_cost_estimates(manager, phases, epics, issues)
        
        # Generate summary data
        summary_data = {
            'repository': {
                'owner': owner,
                'name': repo_name,
                'url': f"https://github.com/{owner}/{repo_name}"
            },
            'metrics': {
                'phases': total_phases,
                'epics': total_epics,
                'issues': total_issues,
                'items_per_phase': round(total_issues / total_phases, 2) if total_phases > 0 else 0,
                'epics_per_phase': round(total_epics / total_phases, 2) if total_phases > 0 else 0
            },
            'phases_breakdown': [
                {
                    'number': phase.get('number', i+1),
                    'title': phase['title'],
                    'epics_count': count_epics_for_phase(epics, phase.get('number', i+1)),
                    'issues_count': count_issues_for_phase(issues, phase.get('number', i+1)),
                    'estimated_effort': estimate_phase_effort(phase, epics, issues)
                }
                for i, phase in enumerate(phases)
            ],
            'generation_info': {
                'generated_at': datetime.now().isoformat(),
                'tool_version': '2.0.0',
                'state_available': execution_state is not None
            }
        }
        
        # Add timing information if available
        if timing_info:
            summary_data['timing'] = timing_info
        
        # Add cost information if requested
        if cost_info:
            summary_data['costs'] = cost_info
        
        # Output based on format
        if output_format == 'json':
            output_json_summary(summary_data, output_file)
        elif output_format == 'markdown':
            output_markdown_summary(summary_data, output_file)
        else:
            output_table_summary(summary_data, output_file)
        
        console.print(f"\n[green]✓ Enhanced summary generated successfully[/green]")
        if output_file:
            console.print(f"[dim]Saved to: {output_file}[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error generating summary: {e}[/red]")
        if hasattr(e, '__traceback__'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


def calculate_timing_metrics(execution_state: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate timing metrics from execution state."""
    timing_info = {
        'execution_id': execution_state.get('execution_id'),
        'started_at': execution_state.get('started_at'),
        'last_updated': execution_state.get('last_updated'),
        'current_step': execution_state.get('current_step'),
        'completed_steps': execution_state.get('completed_steps', [])
    }
    
    # Calculate total execution time if available
    if execution_state.get('started_at') and execution_state.get('last_updated'):
        try:
            start_time = datetime.fromisoformat(execution_state['started_at'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(execution_state['last_updated'].replace('Z', '+00:00'))
            total_seconds = (end_time - start_time).total_seconds()
            timing_info['total_execution_time_seconds'] = total_seconds
            timing_info['total_execution_time_formatted'] = format_duration(total_seconds)
        except:
            pass
    
    # Add step timing if available in execution log
    if 'execution_log' in execution_state:
        step_durations = []
        log_entries = execution_state['execution_log']
        
        for i in range(1, len(log_entries)):
            try:
                prev_time = datetime.fromisoformat(log_entries[i-1]['timestamp'].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(log_entries[i]['timestamp'].replace('Z', '+00:00'))
                duration = (curr_time - prev_time).total_seconds()
                
                step_durations.append({
                    'step': log_entries[i]['step'],
                    'duration_seconds': duration,
                    'duration_formatted': format_duration(duration)
                })
            except:
                continue
        
        timing_info['step_durations'] = step_durations
    
    return timing_info


def calculate_cost_estimates(manager, phases: List[Dict], epics: List[Dict], issues: List[Dict]) -> Dict[str, Any]:
    """Calculate cost estimates based on generated content."""
    
    # Try to load actual cost data from manager
    actual_costs = {}
    if hasattr(manager, 'cost_tracker') and manager.cost_tracker:
        try:
            actual_costs = manager.cost_tracker.get_summary()
        except:
            pass
    
    # Estimate costs based on content if no actual data
    estimated_costs = {
        'phase_generation': estimate_operation_cost('phases', len(phases)),
        'epic_generation': estimate_operation_cost('epics', len(epics)),
        'issue_generation': estimate_operation_cost('issues', len(issues)),
        'preprocessing': estimate_operation_cost('preprocessing', max(0, len(phases) - 1))
    }
    
    total_estimated = sum(estimated_costs.values())
    
    cost_info = {
        'estimated_breakdown': estimated_costs,
        'total_estimated_cost': total_estimated,
        'actual_costs_available': bool(actual_costs),
        'currency': 'USD'
    }
    
    if actual_costs:
        cost_info['actual_breakdown'] = actual_costs
        cost_info['total_actual_cost'] = actual_costs.get('total_cost', 0)
    
    return cost_info


def estimate_operation_cost(operation_type: str, item_count: int) -> float:
    """Estimate cost for an operation type based on item count."""
    base_costs = {
        'phases': 0.015,     # ~$0.015 per phase
        'epics': 0.025,      # ~$0.025 per epic  
        'issues': 0.020,     # ~$0.020 per issue
        'preprocessing': 0.010  # ~$0.010 per preprocessed phase
    }
    
    return base_costs.get(operation_type, 0.020) * item_count


def count_epics_for_phase(epics: List[Dict], phase_number: int) -> int:
    """Count epics belonging to a specific phase."""
    if not epics:
        return 0
    
    return sum(1 for epic in epics if epic.get('phase') == phase_number)


def count_issues_for_phase(issues: List[Dict], phase_number: int) -> int:
    """Count issues belonging to a specific phase."""
    if not issues:
        return 0
    
    return sum(1 for issue in issues if issue.get('phase') == phase_number)


def estimate_phase_effort(phase: Dict, epics: List[Dict], issues: List[Dict]) -> str:
    """Estimate effort for a phase based on its content."""
    phase_number = phase.get('number', 0)
    epic_count = count_epics_for_phase(epics, phase_number)
    issue_count = count_issues_for_phase(issues, phase_number)
    
    # Simple effort estimation based on issue count
    if issue_count <= 5:
        return "Small (1-2 weeks)"
    elif issue_count <= 15:
        return "Medium (3-6 weeks)"
    elif issue_count <= 30:
        return "Large (6-12 weeks)"
    else:
        return "Extra Large (12+ weeks)"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def output_table_summary(summary_data: Dict, output_file: str = None):
    """Output summary in table format."""
    
    # Main metrics table
    metrics_table = Table(title="📊 Project Metrics", show_header=True)
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green")
    
    metrics = summary_data['metrics']
    metrics_table.add_row("Total Phases", str(metrics['phases']))
    metrics_table.add_row("Total Epics", str(metrics['epics']))
    metrics_table.add_row("Total Issues", str(metrics['issues']))
    metrics_table.add_row("Issues per Phase", str(metrics['items_per_phase']))
    metrics_table.add_row("Epics per Phase", str(metrics['epics_per_phase']))
    
    console.print(metrics_table)
    
    # Phase breakdown table
    phase_table = Table(title="📋 Phase Breakdown", show_header=True)
    phase_table.add_column("Phase", style="cyan")
    phase_table.add_column("Title", style="white")
    phase_table.add_column("Epics", style="yellow")
    phase_table.add_column("Issues", style="green")
    phase_table.add_column("Est. Effort", style="magenta")
    
    for phase_info in summary_data['phases_breakdown']:
        phase_table.add_row(
            str(phase_info['number']),
            phase_info['title'],
            str(phase_info['epics_count']),
            str(phase_info['issues_count']),
            phase_info['estimated_effort']
        )
    
    console.print(phase_table)
    
    # Timing information if available
    if 'timing' in summary_data:
        timing_info = summary_data['timing']
        console.print(f"\n[bold]⏱️  Execution Timing:[/bold]")
        console.print(f"Started: {timing_info.get('started_at', 'Unknown')}")
        console.print(f"Last Updated: {timing_info.get('last_updated', 'Unknown')}")
        if 'total_execution_time_formatted' in timing_info:
            console.print(f"Total Time: {timing_info['total_execution_time_formatted']}")
        console.print(f"Current Step: {timing_info.get('current_step', 'Unknown')}")
        console.print(f"Completed Steps: {len(timing_info.get('completed_steps', []))}")
    
    # Cost information if available
    if 'costs' in summary_data:
        cost_info = summary_data['costs']
        console.print(f"\n[bold]💰 Cost Analysis:[/bold]")
        
        if cost_info.get('actual_costs_available'):
            console.print(f"Total Actual Cost: ${cost_info['total_actual_cost']:.4f}")
        else:
            console.print(f"Estimated Total Cost: ${cost_info['total_estimated_cost']:.4f}")
        
        console.print("Breakdown:")
        breakdown = cost_info.get('actual_breakdown', cost_info['estimated_breakdown'])
        for operation, cost in breakdown.items():
            console.print(f"  {operation}: ${cost:.4f}")


def output_json_summary(summary_data: Dict, output_file: str = None):
    """Output summary in JSON format."""
    
    json_output = json.dumps(summary_data, indent=2, ensure_ascii=False)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
    else:
        console.print(json_output)


def output_markdown_summary(summary_data: Dict, output_file: str = None):
    """Output summary in Markdown format."""
    
    repo_info = summary_data['repository']
    metrics = summary_data['metrics']
    
    md_lines = [
        f"# Project Summary: {repo_info['owner']}/{repo_info['name']}",
        "",
        f"**Repository URL:** {repo_info['url']}",
        f"**Generated:** {summary_data['generation_info']['generated_at']}",
        f"**Tool Version:** {summary_data['generation_info']['tool_version']}",
        "",
        "## 📊 Project Metrics",
        "",
        f"- **Total Phases:** {metrics['phases']}",
        f"- **Total Epics:** {metrics['epics']}",  
        f"- **Total Issues:** {metrics['issues']}",
        f"- **Issues per Phase:** {metrics['items_per_phase']}",
        f"- **Epics per Phase:** {metrics['epics_per_phase']}",
        "",
        "## 📋 Phase Breakdown",
        "",
        "| Phase | Title | Epics | Issues | Est. Effort |",
        "|-------|-------|--------|--------|-------------|"
    ]
    
    for phase_info in summary_data['phases_breakdown']:
        md_lines.append(
            f"| {phase_info['number']} | {phase_info['title']} | "
            f"{phase_info['epics_count']} | {phase_info['issues_count']} | "
            f"{phase_info['estimated_effort']} |"
        )
    
    # Add timing information if available
    if 'timing' in summary_data:
        timing_info = summary_data['timing']
        md_lines.extend([
            "",
            "## ⏱️ Execution Timing",
            "",
            f"- **Started:** {timing_info.get('started_at', 'Unknown')}",
            f"- **Last Updated:** {timing_info.get('last_updated', 'Unknown')}",
            f"- **Current Step:** {timing_info.get('current_step', 'Unknown')}",
            f"- **Completed Steps:** {len(timing_info.get('completed_steps', []))}"
        ])
        
        if 'total_execution_time_formatted' in timing_info:
            md_lines.append(f"- **Total Time:** {timing_info['total_execution_time_formatted']}")
    
    # Add cost information if available
    if 'costs' in summary_data:
        cost_info = summary_data['costs']
        md_lines.extend([
            "",
            "## 💰 Cost Analysis",
            ""
        ])
        
        if cost_info.get('actual_costs_available'):
            md_lines.append(f"**Total Actual Cost:** ${cost_info['total_actual_cost']:.4f}")
        else:
            md_lines.append(f"**Estimated Total Cost:** ${cost_info['total_estimated_cost']:.4f}")
        
        md_lines.append("")
        md_lines.append("### Cost Breakdown")
        md_lines.append("")
        
        breakdown = cost_info.get('actual_breakdown', cost_info['estimated_breakdown'])
        for operation, cost in breakdown.items():
            md_lines.append(f"- **{operation.replace('_', ' ').title()}:** ${cost:.4f}")
    
    md_content = "\n".join(md_lines)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    else:
        console.print(md_content)


@cli.command()
@click.option('--model', help='Show pricing for specific model')
def pricing(model: str):
    """Display current Anthropic API pricing information."""
    
    from .cost_tracker import CostTracker
    
    console.print("\n[bold purple]💰 ANTHROPIC CLAUDE API PRICING (2024)[/bold purple]")
    console.print("[purple]" + "=" * 50 + "[/purple]")
    
    current_model = os.getenv('GITHUB_BACKLOG_MODEL', 'claude-3-5-sonnet-20241022')
    if model:
        current_model = model
    
    console.print(f"\n[cyan]Current/Selected Model: {current_model}[/cyan]\n")
    
    # Display pricing table
    table = Table(show_header=True)
    table.add_column("Model", style="cyan")
    table.add_column("Input (per 1M tokens)", style="green")
    table.add_column("Output (per 1M tokens)", style="yellow")
    table.add_column("Typical Operation Cost", style="magenta")
    
    tracker = CostTracker()
    for model_name, pricing in tracker.MODEL_PRICING.items():
        # Calculate typical operation cost (assuming 3000 input, 1500 output tokens)
        typical_cost = tracker.calculate_cost(model_name, 3000, 1500)
        
        table.add_row(
            model_name,
            f"${pricing['input']:.3f}",
            f"${pricing['output']:.3f}",
            f"${typical_cost:.4f}"
        )
    
    console.print(table)
    
    console.print(f"\n[yellow]Cost Estimation Guidelines:[/yellow]")
    console.print("• 1 token ≈ 4 characters or 0.75 words in English")
    console.print("• README Analysis: ~2,500 tokens → $0.01-0.02")
    console.print("• Phase Generation: ~8,000 tokens → $0.02-0.05")
    console.print("• Epic Generation: ~6,000 tokens → $0.03-0.06")
    console.print("• Task Generation: ~4,000 tokens → $0.02-0.04")
    
    console.print(f"\n[green]Project Size Estimates:[/green]")
    console.print("• Small Project (1-20 features): $0.50 - $2.00")
    console.print("• Medium Project (21-50 features): $2.00 - $8.00")
    console.print("• Large Project (50+ features): $8.00 - $20.00")


if __name__ == '__main__':
    cli()