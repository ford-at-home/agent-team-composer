"""GitHub Client - Handles repo operations and milestone creation."""

import re
import tempfile
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from github import Github
from github.GithubException import GithubException, RateLimitExceededException


def github_retry(max_retries=5, base_delay=1.0):
    """Decorator for GitHub API calls with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitExceededException as e:
                    if attempt == max_retries - 1:
                        raise
                    # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                    delay = base_delay * (2 ** attempt)
                    print(f"Rate limit hit. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                except GithubException as e:
                    # Check if it's a secondary rate limit
                    if e.status == 403 and "secondary rate limit" in str(e.data.get('message', '')).lower():
                        if attempt == max_retries - 1:
                            raise
                        delay = base_delay * (2 ** attempt) * 2  # Longer delay for secondary rate limits
                        print(f"Secondary rate limit hit. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(delay)
                    else:
                        raise  # Re-raise if it's not a rate limit issue
            return None
        return wrapper
    return decorator


class GitHubClient:
    """Client for GitHub operations."""
    
    def __init__(self, token: str):
        self.github = Github(token)
    
    def parse_repo_url(self, url: str) -> Tuple[str, str]:
        """Parse GitHub URL to extract owner and repo name."""
        # Handle various GitHub URL formats
        patterns = [
            r'github\.com[:/]([^/]+)/([^/\.]+)(?:\.git)?/?$',
            r'github\.com/([^/]+)/([^/]+)/?$',
            r'^([^/]+)/([^/]+)$'  # Simple owner/repo format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)
        
        raise ValueError(f"Invalid GitHub URL format: {url}")
    
    def sparse_checkout_readme(self, owner: str, repo: str) -> str:
        """Sparse checkout just the README file from a repo."""
        # For simplicity, let's use the GitHub API to fetch README directly
        try:
            repo_obj = self.github.get_repo(f"{owner}/{repo}")
            readme = repo_obj.get_readme()
            return readme.decoded_content.decode('utf-8')
        except GithubException:
            # Fallback to raw GitHub URL
            import requests
            for branch in ['main', 'master']:
                try:
                    response = requests.get(
                        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md",
                        headers={'Authorization': f'token {self.github._Github__auth._token}'}
                    )
                    if response.status_code == 200:
                        return response.text
                except:
                    continue
            
            raise FileNotFoundError(f"No README found in {owner}/{repo}")
    
    @github_retry()
    def create_milestones(self, owner: str, repo_name: str, phases: List[Dict[str, any]]) -> List[str]:
        """Create milestones in the GitHub repository."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            created_milestones = []
            
            # Get existing milestones to avoid duplicates
            existing_milestones = {m.title: m for m in repo.get_milestones(state='all')}
            
            for phase in phases:
                # Extract phase number from id (e.g., "phase-1" -> 1)
                phase_num = phase['id'].split('-')[1] if 'phase-' in phase['id'] else '1'
                title = f"Phase {phase_num}: {phase['title']}"
                
                # Check if milestone already exists
                # Parse due date if provided
                due_date = None
                if phase.get('dueDate'):
                    due_date = datetime.fromisoformat(phase['dueDate'].replace('Z', '+00:00'))
                
                if title in existing_milestones:
                    milestone = existing_milestones[title]
                    # Update existing milestone
                    milestone.edit(
                        title=title,
                        description=phase['description'],
                        due_on=due_date
                    )
                    created_milestones.append(f"Updated: {milestone.html_url}")
                else:
                    # Create new milestone
                    milestone = repo.create_milestone(
                        title=title,
                        description=phase['description'],
                        due_on=due_date
                    )
                    created_milestones.append(f"Created: {milestone.html_url}")
            
            return created_milestones
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
    
    def validate_access(self, owner: str, repo_name: str) -> bool:
        """Validate that we have access to create milestones in the repo."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            # Check if we have push access (required for milestones)
            return repo.permissions.push
        except GithubException:
            return False
    
    @github_retry()
    def create_epic_only(self, owner: str, repo_name: str, phase_data: Dict[str, any], 
                        epic_data: Dict[str, any], milestone_number: int) -> str:
        """Create only an epic issue in the repository."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Create Epic Issue
            epic_title = f"[Epic] {phase_data['title']}"
            
            # Build epic body with task checklist
            epic_body = f"## Epic Overview\n{phase_data['description']}\n\n"
            epic_body += f"## Team Composition\n"
            for role in epic_data['roles']:
                epic_body += f"- {role}\n"
            epic_body += "\n## Tasks\n"
            
            # Add task checklist (without issue links since they don't exist yet)
            for task in epic_data['tasks']:
                epic_body += f"- [ ] {task['title']} (@{task['suggestedRole'].split(' - ')[0]})\n"
            
            epic_body += "\n*Note: Task issues can be created later.*"
            
            # Create epic issue
            epic_labels = [
                f"phase:{phase_data.get('id', 'phase')}",
                "epic",
                "sparc-ready"
            ]
            
            epic = repo.create_issue(
                title=epic_title,
                body=epic_body,
                labels=epic_labels,
                milestone=repo.get_milestone(milestone_number)
            )
            return {'url': epic.html_url, 'number': epic.number}
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
    
    @github_retry()
    def create_task_issue(self, owner: str, repo_name: str, task_data: Dict[str, any], 
                         epic_number: int, phase_id: str, milestone_number: int) -> str:
        """Create a single task issue in the repository."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Build task body
            task_body = f"## Overview\n{task_data['description']}\n\n"
            task_body += f"## Parent Epic\nThis task is part of epic #{epic_number}\n\n"
            task_body += f"## Acceptance Criteria\n"
            for criterion in task_data['acceptanceCriteria']:
                task_body += f"- [ ] {criterion}\n"
            task_body += f"\n## Technical Notes\n{task_data['technicalNotes']}\n\n"
            
            if task_data.get('dependencies'):
                task_body += f"## Dependencies\n"
                for dep in task_data['dependencies']:
                    task_body += f"- {dep}\n"
                task_body += "\n"
            
            task_body += f"## Metadata\n"
            task_body += f"- **Assigned Role**: {task_data['suggestedRole']}\n"
            task_body += f"- **Priority**: {task_data['priority']}\n"
            task_body += f"- **Estimated Effort**: {task_data['estimatedEffort']}\n"
            task_body += f"- **Phase**: {phase_id}\n"
            task_body += f"- **Epic**: #{epic_number}\n"
            
            # Create task issue with sanitized labels
            role_label = task_data['suggestedRole'].lower().replace(' ', '-').replace('/', '-')[:50]
            task_labels = [
                f"phase:{phase_id}",
                f"role:{role_label}",
                f"priority:{task_data['priority']}",
                f"effort:{task_data['estimatedEffort']}",
                "task",
                "sparc-ready"
            ]
            
            task_issue = repo.create_issue(
                title=task_data['title'],
                body=task_body,
                labels=task_labels,
                milestone=repo.get_milestone(milestone_number)
            )
            
            return task_issue.html_url
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
    
    def create_epic_and_tasks(self, owner: str, repo_name: str, phase_data: Dict[str, any], 
                             epic_data: Dict[str, any], milestone_number: int) -> Dict[str, any]:
        """Create an epic issue and related task issues in the repository."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            created_issues = {
                'epic': None,
                'tasks': []
            }
            
            # Create Epic Issue
            epic_title = f"[Epic] {phase_data['title']}"
            
            # Build epic body with task checklist
            epic_body = f"## Epic Overview\n{phase_data['description']}\n\n"
            epic_body += f"## Team Composition\n"
            for role in epic_data['roles']:
                epic_body += f"- {role}\n"
            epic_body += "\n## Tasks\n"
            
            # Add task checklist (without issue links since they don't exist yet)
            for task in epic_data['tasks']:
                epic_body += f"- [ ] {task['title']} (@{task['suggestedRole'].split(' - ')[0]})\n"
            
            epic_body += "\n*Note: Task issues will be created and linked below.*"
            
            # Create epic issue
            epic_labels = [
                f"phase:{phase_data.get('id', 'phase')}",
                "epic",
                "sparc-ready"
            ]
            
            epic = repo.create_issue(
                title=epic_title,
                body=epic_body,
                labels=epic_labels,
                milestone=repo.get_milestone(milestone_number)
            )
            created_issues['epic'] = epic.html_url
            
            # Create individual task issues
            for i, task in enumerate(epic_data['tasks'], 1):
                task_title = task['title']
                
                # Build task body
                task_body = f"## Overview\n{task['description']}\n\n"
                task_body += f"## Parent Epic\nThis task is part of epic #{epic.number}: {epic_title}\n\n"
                task_body += f"## Assigned Role\n{task['suggestedRole']}\n\n"
                task_body += f"## Acceptance Criteria\n- [ ] Task completed according to requirements\n"
                task_body += f"- [ ] Deliverables documented\n- [ ] Reviewed and approved\n\n"
                task_body += f"## Agent Metadata\n"
                task_body += f"- Role: {task['suggestedRole'].split(' - ')[0]}\n"
                task_body += f"- Phase: {phase_data['title']}\n"
                task_body += f"- Epic: #{epic.number}"
                
                # Create task issue
                task_labels = [
                    f"phase:{phase_data.get('id', 'phase')}",
                    f"role:{task['suggestedRole'].split(' - ')[0].lower().replace(' ', '-')}",
                    "sparc-ready",
                    "task"
                ]
                
                task_issue = repo.create_issue(
                    title=task_title,
                    body=task_body,
                    labels=task_labels,
                    milestone=repo.get_milestone(milestone_number)
                )
                created_issues['tasks'].append(task_issue.html_url)
            
            return created_issues
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")