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
@click.argument('repo_url')
@click.pass_context
def status(ctx, repo_url: str):
    """Show the current status of backlog generation with optional cost/timing information."""
    
    cost_tracking = ctx.obj.get('cost_tracking', False)
    time_tracking = ctx.obj.get('time_tracking', False)
    
    # Parse repository URL
    match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo_url)
    if not match:
        console.print("[red]Error: Invalid GitHub URL[/red]")
        sys.exit(1)
    
    owner, repo_name = match.groups()
    
    # Initialize backlog manager with cost tracking if requested
    manager = BacklogManager(owner, repo_name, enable_cost_tracking=cost_tracking)
    
    if not manager.base_dir.exists():
        console.print(f"[red]No backlog found for {owner}/{repo_name}[/red]")
        console.print("Run 'github-backlog init' to get started.")
        sys.exit(1)
    
    # Load metadata
    metadata = manager.load_metadata()
    if metadata:
        console.print(f"\n[bold]Project: {metadata['project_data']['title']}[/bold]")
        console.print(f"Repository: {owner}/{repo_name}")
        console.print(f"Created: {metadata['created_at'][:10]}")
    
    # Load phases
    phases = manager.load_phases()
    if not phases:
        console.print("\n[yellow]No phases generated yet.[/yellow]")
        return
    
    # Show status table
    console.print("\n[bold]Generation Status:[/bold]\n")
    
    table = Table(show_header=True)
    table.add_column("Phase", style="cyan", width=5)
    table.add_column("Title", style="green", width=30)
    table.add_column("Epics", style="yellow", width=10)
    table.add_column("Issues", style="magenta", width=10)
    table.add_column("Status", width=15)
    
    milestone_mapping = manager.get_milestone_mapping()
    
    for phase in phases:
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