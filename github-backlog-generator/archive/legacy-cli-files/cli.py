"""GitHub Backlog Generator CLI - Main entry point."""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .readme_parser import ReadmeParser
from .unified_generator import UnifiedGenerator
from .epic_generator import EpicGenerator
from .task_generator import TaskGenerator
from .github_client import GitHubClient

console = Console()

# Define the 8 standard phases
STANDARD_PHASES = [
    "Discovery & Requirements",
    "Technical Planning & Architecture", 
    "UI/UX Design & Prototyping",
    "Core Development",
    "System Integration & Testing",
    "Quality Assurance & Testing",
    "Deployment & Distribution",
    "Launch & Documentation"
]


@click.command()
@click.argument('repo_url')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--dry-run', is_flag=True, help='Generate phase without creating milestone')
@click.option('--output', '-o', help='Save phase to JSON file')
@click.option('--all-phases', is_flag=True, help='Create all 8 phases instead of just one')
@click.option('--phase', '-p', type=int, help='Specific phase number to generate (1-8)')
def main(repo_url: str, api_key: str, github_token: str, dry_run: bool, output: str, all_phases: bool, phase: int):
    """Generate a project milestone from a GitHub repository's README.
    
    REPO_URL: GitHub repository URL (e.g., https://github.com/owner/repo or owner/repo)
    """
    
    # Load environment variables
    load_dotenv()
    
    # Validate API keys
    if not api_key:
        api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found![/red]")
        console.print("Please set it in .env file or pass with --api-key")
        sys.exit(1)
    
    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token and not dry_run:
        console.print("[red]Error: GITHUB_TOKEN not found![/red]")
        console.print("Please set it in .env file or pass with --github-token")
        console.print("Or use --dry-run to generate phase without creating milestone")
        sys.exit(1)
    
    with console.status("[bold green]Processing repository...") as status:
        # Initialize GitHub client
        github_client = GitHubClient(github_token) if github_token else None
        
        # Parse repository URL
        status.update("Parsing repository URL...")
        try:
            owner, repo_name = github_client.parse_repo_url(repo_url) if github_client else (None, None)
            if not github_client:
                # For dry run, just parse the URL manually
                match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo_url)
                if match:
                    owner, repo_name = match.groups()
                else:
                    raise ValueError("Invalid GitHub URL")
            
            console.print(f"[green]✓[/green] Repository: {owner}/{repo_name}")
        except Exception as e:
            console.print(f"[red]Error parsing repository URL: {e}[/red]")
            sys.exit(1)
        
        # Validate access (if not dry run)
        if github_client and not dry_run:
            status.update("Validating repository access...")
            if not github_client.validate_access(owner, repo_name):
                console.print("[red]Error: No write access to repository![/red]")
                console.print("Make sure your GitHub token has 'repo' scope")
                sys.exit(1)
            console.print("[green]✓[/green] Repository access validated")
        
        # Sparse checkout README
        status.update("Fetching README from repository...")
        try:
            if github_client:
                readme_content = github_client.sparse_checkout_readme(owner, repo_name)
            else:
                # For dry run without token, try to fetch via raw GitHub URL
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
        
        # Parse README
        status.update("Analyzing README content...")
        parser = ReadmeParser()
        try:
            project_data = parser.parse_readme_content(readme_content)
            console.print("[green]✓[/green] README analyzed successfully")
        except Exception as e:
            console.print(f"[red]Error parsing README: {e}[/red]")
            sys.exit(1)
    
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
    info_table.add_row("Tech Stack", ', '.join(project_data['techStack'][:5]) + ('...' if len(project_data['techStack']) > 5 else ''))
    
    console.print(info_table)
    console.print()
    
    # Determine which phases to create
    if all_phases:
        phases_to_create = list(range(1, 9))  # All 8 phases
        console.print("[bold]Creating all 8 phases:[/bold]\n")
        for i, phase_name in enumerate(STANDARD_PHASES, 1):
            console.print(f"  {i}. {phase_name}")
        console.print()
        
        if not dry_run and github_client:
            console.print(f"[bold yellow]WARNING:[/bold yellow] This will create approximately:")
            console.print(f"  • 8 milestones")
            console.print(f"  • 40-80 epic issues")
            console.print(f"  • 200-800 task issues")
            console.print(f"\nThis may take 15-30 minutes to complete.")
            
            confirm = input("\nContinue? (yes/no): ")
            if confirm.lower() != 'yes':
                console.print("Aborted.")
                sys.exit(0)
    elif phase:
        # Specific phase requested via command line
        if 1 <= phase <= 8:
            phases_to_create = [phase]
            console.print(f"[green]Selected:[/green] Phase {phase} - {STANDARD_PHASES[phase - 1]}")
        else:
            console.print(f"[red]Error: Phase must be between 1 and 8[/red]")
            sys.exit(1)
    else:
        # Display phases and ask for selection
        console.print("[bold]Select a phase to generate:[/bold]\n")
        for i, phase_name in enumerate(STANDARD_PHASES, 1):
            console.print(f"  {i}. {phase_name}")
        
        console.print()
        
        # Get user selection
        while True:
            try:
                selection = input("Enter phase number (1-8): ")
                phase_num = int(selection)
                if 1 <= phase_num <= 8:
                    break
                else:
                    console.print("[red]Please enter a number between 1 and 8[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")
        
        phases_to_create = [phase_num]
    
    # Define phase descriptions once
    phase_descriptions = {
        1: "This phase focuses on understanding the project requirements, user needs, and technical constraints. The goal is to establish a clear vision and roadmap.",
        2: "This phase involves designing the system architecture, selecting technologies, and planning the technical implementation approach.",
        3: "This phase centers on creating the user experience, visual design, and interactive prototypes to validate design decisions.",
        4: "This phase is where the main development work happens, building the core features and functionality of the system.",
        5: "This phase focuses on integrating different system components and ensuring they work together seamlessly.",
        6: "This phase involves comprehensive testing to ensure quality, performance, and reliability of the system.",
        7: "This phase handles packaging, deployment setup, and distribution mechanisms for the application.",
        8: "This phase covers documentation, training materials, and go-to-market activities for the launch."
    }
    
    # Initialize milestone_mapping for single phase mode
    milestone_mapping = {}
    
    # Track overall progress
    total_phases = len(phases_to_create)
    
    # NEW WORKFLOW: When --all-phases is used, create all milestones first
    if all_phases and not dry_run and github_client:
        console.print("\n[bold cyan]Step 1: Creating all milestones first...[/bold cyan]\n")
        
        milestone_mapping = {}  # phase_num -> milestone_number
        
        with console.status("[bold green]Creating milestones...") as status:
            for phase_num in phases_to_create:
                selected_phase = STANDARD_PHASES[phase_num - 1]
                phase_description = phase_descriptions.get(phase_num, "")
                
                try:
                    # Create milestone with phase data
                    phase_data = {
                        'id': f'phase-{phase_num}',
                        'title': selected_phase,
                        'description': phase_description,
                        'dueDate': (datetime.now() + timedelta(days=phase_num * 14)).isoformat()
                    }
                    
                    milestone_urls = github_client.create_milestones(owner, repo_name, [phase_data])
                    console.print(f"[green]✓[/green] Milestone {phase_num}: {selected_phase}")
                    
                    # Extract milestone number from URL
                    milestone_match = re.search(r'/milestone/(\d+)$', milestone_urls[0])
                    if milestone_match:
                        milestone_mapping[phase_num] = int(milestone_match.group(1))
                    
                except Exception as e:
                    console.print(f"[red]✗[/red] Failed to create milestone {phase_num}: {e}")
        
        console.print(f"\n[green]✓[/green] Created {len(milestone_mapping)} milestones successfully!")
        console.print("\n[bold cyan]Step 2: Populating milestones with epics and issues...[/bold cyan]")
    
    # Process each phase
    for phase_idx, phase_num in enumerate(phases_to_create, 1):
        selected_phase = STANDARD_PHASES[phase_num - 1]
        phase_description = phase_descriptions.get(phase_num, "")
        
        if all_phases:
            console.print(f"\n[bold cyan]Processing Phase {phase_num}/{total_phases}: {selected_phase}[/bold cyan]")
        else:
            console.print(f"\n[green]Selected:[/green] Phase {phase_num} - {selected_phase}")
        
        # Generate multiple epics for this phase
        with console.status(f"[bold green]Generating epics for Phase {phase_num}...") as status:
            epic_generator = EpicGenerator(api_key)
            
            try:
                epics = epic_generator.generate_epics_for_phase(
                    phase_num, selected_phase, phase_description, project_data
                )
                console.print(f"[green]✓[/green] Generated {len(epics)} epics for Phase {phase_num}")
            except Exception as e:
                console.print(f"[red]Error generating epics: {e}[/red]")
                if all_phases:
                    console.print("Continuing with next phase...")
                    continue
                else:
                    sys.exit(1)
        
        # Display the generated epics (only if single phase)
        if not all_phases:
            console.print(f"\n[bold]Generated Epics for Phase {phase_num}: {selected_phase}[/bold]\n")
            
            # Display each epic
            for i, epic in enumerate(epics, 1):
                epic_panel_content = f"[bold]Description:[/bold] {epic['description']}\n\n"
                epic_panel_content += f"[bold]Roles:[/bold] {', '.join(epic['suggestedRoles'])}\n\n"
                epic_panel_content += f"[bold]Tasks ({len(epic['tasks'])}):[/bold]\n"
                
                for j, task in enumerate(epic['tasks'], 1):
                    epic_panel_content += f"  {j}. {task['title']} ({task['suggestedRole']})\n"
                
                console.print(Panel(
                    epic_panel_content,
                    title=f"[Epic {i}] {epic['title']}",
                    title_align="left",
                    border_style="cyan"
                ))
                console.print()  # Add spacing between epics
        
        # Save to file if requested
        if output and not all_phases:
            output_data = {
                'repository': f"{owner}/{repo_name}",
                'project': {
                    'title': project_data['title'],
                    'domain': project_data['domain'],
                    'complexity': project_data['complexity']
                },
                'phase': {
                    'number': phase_num,
                    'title': selected_phase,
                    'description': phase_description,
                    'epics': epics
                }
            }
            
            with open(output, 'w') as f:
                json.dump(output_data, f, indent=2)
            console.print(f"\n[green]✓[/green] Phase with {len(epics)} epics saved to {output}")
        
        # Create milestone in GitHub (if not dry run)
        if not dry_run and github_client:
            # For all-phases mode, milestone already exists
            if all_phases and phase_num in milestone_mapping:
                console.print(f"\n[bold]Populating Phase {phase_num}: {selected_phase}[/bold]")
                milestone_number = milestone_mapping[phase_num]
            else:
                # Single phase mode - create milestone now
                console.print("\n[bold]Creating Complete Backlog in GitHub:[/bold]")
                console.print("[dim]This will create: 1 milestone, ~5-10 epics, ~5-10 tasks per epic[/dim]\n")
                
                with console.status("[bold green]Creating milestone...") as status:
                    try:
                        # Create milestone with phase data
                        phase_data = {
                            'id': f'phase-{phase_num}',
                            'title': selected_phase,
                            'description': phase_description,
                            'dueDate': (datetime.now() + timedelta(days=phase_num * 14)).isoformat()
                        }
                        
                        milestone_urls = github_client.create_milestones(owner, repo_name, [phase_data])
                        console.print(f"[green]✓[/green] Milestone created successfully!\n")
                        
                        for url in milestone_urls:
                            console.print(f"  • {url}")
                        
                        # Extract milestone number from URL
                        milestone_match = re.search(r'/milestone/(\d+)$', milestone_urls[0])
                        if milestone_match:
                            milestone_number = int(milestone_match.group(1))
                        else:
                            raise Exception("Could not extract milestone number")
                    except Exception as e:
                        console.print(f"[red]Error creating milestone: {e}[/red]")
                        console.print("\nPhase was generated successfully but milestone could not be created.")
                        console.print("You can save the phase with --output and create milestone manually.")
                        sys.exit(1)
            
            # Now create epics and tasks for this milestone
            with console.status(f"[bold green]Creating content for Phase {phase_num}...") as status:
                if 'milestone_number' in locals():
                        
                        # Create epic issues
                        status.update("Creating epic issues...")
                        
                        created_epics = []
                        for i, epic in enumerate(epics, 1):
                            try:
                                # Create epic-specific phase data
                                epic_phase_data = {
                                    'id': f'phase-{phase_num}',
                                    'title': epic['title'],
                                    'description': epic['description']
                                }
                                
                                # Format epic data to match expected structure
                                epic_data = {
                                    'roles': epic['suggestedRoles'],
                                    'tasks': epic['tasks']
                                }
                                
                                epic_result = github_client.create_epic_only(
                                    owner, repo_name, epic_phase_data, epic_data, milestone_number
                                )
                                created_epics.append(epic_result['url'])
                                console.print(f"  [green]✓[/green] Created Epic {i}: {epic['title']}")
                                
                                # Always create tasks
                                status.update(f"Generating tasks for Epic {i}...")
                                task_generator = TaskGenerator(api_key)
                                
                                try:
                                    # Generate tasks for this epic
                                    tasks = task_generator.generate_tasks_for_epic(
                                        epic, selected_phase, project_data
                                    )
                                    console.print(f"    Generated {len(tasks)} tasks")
                                    
                                    # Create task issues
                                    for j, task in enumerate(tasks, 1):
                                        status.update(f"Creating task {j}/{len(tasks)} for Epic {i}...")
                                        
                                        # Generate detailed description for the task
                                        task_desc = task_generator.generate_task_description(
                                            task, epic, selected_phase, project_data
                                        )
                                        
                                        # Merge task data with description
                                        full_task_data = {**task, **task_desc}
                                        
                                        # Create the task issue
                                        task_url = github_client.create_task_issue(
                                            owner, repo_name, full_task_data,
                                            epic_result['number'], f'phase-{phase_num}', milestone_number
                                        )
                                        console.print(f"    [green]✓[/green] Created Task {j}: {task['title']}")
                                        
                                except Exception as e:
                                    console.print(f"    [red]✗[/red] Failed to create tasks: {e}")
                            except Exception as e:
                                console.print(f"  [red]✗[/red] Failed to create Epic {i}: {e}")
                        
                        # Count total tasks created
                        total_tasks = sum(len(epic.get('tasks', [])) for epic in epics)
                        console.print(f"\n[green]✓[/green] Phase {phase_num} created successfully!")
                        console.print(f"  • 1 milestone")
                        console.print(f"  • {len(created_epics)} epics") 
                        console.print(f"  • ~{total_tasks} tasks (across all epics)")
    
    # Final summary for all phases
    if all_phases and not dry_run and github_client:
        console.print(f"\n[bold green]All phases created successfully![/bold green]")
        console.print(f"Total created:")
        console.print(f"  • {total_phases} milestones")
        console.print(f"  • ~{total_phases * 5}-{total_phases * 10} epics")
        console.print(f"  • ~{total_phases * 25}-{total_phases * 100} tasks")
    
    elif dry_run:
        console.print("\n[yellow]Dry run mode:[/yellow] Milestone was not created.")
        console.print("Remove --dry-run flag to create milestone in GitHub.")


if __name__ == '__main__':
    main()