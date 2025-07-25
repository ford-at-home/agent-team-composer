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

# Phase descriptions
PHASE_DESCRIPTIONS = {
    1: "This phase focuses on understanding the project requirements, user needs, and technical constraints. The goal is to establish a clear vision and roadmap.",
    2: "This phase involves designing the system architecture, selecting technologies, and planning the technical implementation approach.",
    3: "This phase centers on creating the user experience, visual design, and interactive prototypes to validate design decisions.",
    4: "This phase is where the main development work happens, building the core features and functionality of the system.",
    5: "This phase focuses on integrating different system components and ensuring they work together seamlessly.",
    6: "This phase involves comprehensive testing to ensure quality, performance, and reliability of the system.",
    7: "This phase handles packaging, deployment setup, and distribution mechanisms for the application.",
    8: "This phase covers documentation, training materials, and go-to-market activities for the launch."
}


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
    
    # Display what will be created
    console.print("\n[bold]The following 8 milestones will be created:[/bold]\n")
    
    table = Table(show_header=True)
    table.add_column("Phase", style="cyan", width=5)
    table.add_column("Title", style="green")
    table.add_column("Due Date", style="yellow")
    
    for i in range(1, 9):
        due_date = (datetime.now() + timedelta(days=i * 14)).strftime("%Y-%m-%d")
        table.add_row(str(i), STANDARD_PHASES[i-1], due_date)
    
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
        for phase_num in range(1, 9):
            try:
                phase_data = {
                    'id': f'phase-{phase_num}',
                    'title': STANDARD_PHASES[phase_num - 1],
                    'description': PHASE_DESCRIPTIONS[phase_num],
                    'dueDate': (datetime.now() + timedelta(days=phase_num * 14)).isoformat()
                }
                
                urls = github_client.create_milestones(owner, repo_name, [phase_data])
                milestone_urls.extend(urls)
                created_count += 1
                console.print(f"[green]✓[/green] Phase {phase_num}: {STANDARD_PHASES[phase_num - 1]}")
                
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