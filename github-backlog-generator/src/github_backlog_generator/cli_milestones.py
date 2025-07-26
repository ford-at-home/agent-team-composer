"""GitHub Backlog Generator CLI - Milestone-only generation command."""

import os
import re
import sys
from datetime import datetime, timedelta

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .readme_parser import ReadmeParser
from .github_client import GitHubClient

console = Console()

# Import BacklogManager to read AI-generated phases
from pathlib import Path
import json

def load_generated_phases(owner: str, repo_name: str):
    """Load AI-generated phases from local storage."""
    # Create .backlog directory inside github-backlog-generator directory
    generator_dir = Path(__file__).parent.parent.parent
    base_dir = generator_dir / f".backlog-{owner}-{repo_name}"
    phases_file = base_dir / "phases" / "phases.json"
    
    if not phases_file.exists():
        raise FileNotFoundError(f"No phases found. Please run 'github-backlog init {owner}/{repo_name}' first.")
    
    with open(phases_file, 'r') as f:
        data = json.load(f)
        return data['phases']


@click.command()
@click.argument('repo_url')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--dry-run', is_flag=True, help='Show what would be created without actually creating')
def milestones(repo_url: str, github_token: str, dry_run: bool):
    """Create all 8 phase milestones for a GitHub repository.
    
    This command creates ONLY the milestones, without any epics or issues.
    Use the main 'generate' command to populate milestones with content.
    
    REPO_URL: GitHub repository URL (e.g., https://github.com/owner/repo)
    """
    
    # Load environment variables
    load_dotenv()
    
    # Validate GitHub token
    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        console.print("[red]Error: GITHUB_TOKEN not found![/red]")
        console.print("Please set it in .env file or pass with --github-token")
        sys.exit(1)
    
    with console.status("[bold green]Processing repository...") as status:
        # Initialize GitHub client
        github_client = GitHubClient(github_token)
        
        # Parse repository URL
        status.update("Parsing repository URL...")
        try:
            owner, repo_name = github_client.parse_repo_url(repo_url)
            console.print(f"[green]✓[/green] Repository: {owner}/{repo_name}")
        except Exception as e:
            console.print(f"[red]Error parsing repository URL: {e}[/red]")
            sys.exit(1)
        
        # Validate access
        status.update("Validating repository access...")
        if not github_client.validate_access(owner, repo_name):
            console.print("[red]Error: No write access to repository![/red]")
            console.print("Make sure your GitHub token has 'repo' scope")
            sys.exit(1)
        console.print("[green]✓[/green] Repository access validated")
    
    # Load AI-generated phases
    try:
        phases = load_generated_phases(owner, repo_name)
        console.print(f"[green]✓[/green] Loaded {len(phases)} AI-generated phases")
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Run 'github-backlog init <repo-url>' first to generate phases.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error loading phases: {e}[/red]")
        sys.exit(1)
    
    # Display what will be created
    console.print(f"\n[bold]The following {len(phases)} AI-generated milestones will be created:[/bold]\n")
    
    table = Table(show_header=True)
    table.add_column("Phase", style="cyan", width=5)
    table.add_column("Title", style="green")
    table.add_column("Due Date", style="yellow")
    
    for i, phase in enumerate(phases, 1):
        due_date = datetime.fromisoformat(phase['dueDate'].replace('Z', '+00:00')).strftime("%Y-%m-%d")
        table.add_row(str(i), phase['title'], due_date)
    
    console.print(table)
    console.print()
    
    if dry_run:
        console.print("[yellow]Dry run mode:[/yellow] Milestones will not be created.")
        console.print("Remove --dry-run flag to create milestones in GitHub.")
        return
    
    # Confirm creation
    confirm = input("Create these milestones? (yes/no): ")
    if confirm.lower() != 'yes':
        console.print("Aborted.")
        sys.exit(0)
    
    # Create milestones
    console.print("\n[bold]Creating milestones...[/bold]\n")
    
    created_count = 0
    milestone_urls = []
    
    with console.status("[bold green]Creating milestones...") as status:
        for phase_num, phase in enumerate(phases, 1):
            try:
                phase_data = {
                    'id': phase['id'],
                    'title': phase['title'],
                    'description': phase['description'],
                    'dueDate': phase['dueDate']
                }
                
                urls = github_client.create_milestones(owner, repo_name, [phase_data])
                milestone_urls.extend(urls)
                created_count += 1
                console.print(f"[green]✓[/green] Phase {phase_num}: {phase['title']}")
                
            except Exception as e:
                console.print(f"[red]✗[/red] Phase {phase_num}: {e}")
    
    # Summary
    console.print(f"\n[bold green]Successfully created {created_count} milestones![/bold green]\n")
    
    if milestone_urls:
        console.print("[bold]Milestone URLs:[/bold]")
        for url in milestone_urls:
            console.print(f"  • {url}")
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Review the milestones on GitHub")
    console.print("2. Use 'github-backlog generate --phase N' to populate each milestone with epics and issues")
    console.print("3. Or use 'github-backlog generate --all-phases' to populate all milestones at once")


if __name__ == '__main__':
    milestones()