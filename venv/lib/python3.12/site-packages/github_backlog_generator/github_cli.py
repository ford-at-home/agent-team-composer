"""GitHub CLI wrapper - Uses gh command for GitHub operations."""

import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GitHubCLI:
    """Wrapper for GitHub CLI (gh) operations."""
    
    def __init__(self):
        # Verify gh is installed
        self._verify_gh_installed()
    
    def _verify_gh_installed(self):
        """Verify that gh CLI is installed and authenticated."""
        try:
            result = subprocess.run(['gh', 'auth', 'status'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("GitHub CLI not authenticated. Run 'gh auth login'")
        except FileNotFoundError:
            raise Exception("GitHub CLI (gh) not found. Please install it first.")
    
    def create_milestone(self, repo: str, title: str, description: str, due_date: Optional[str] = None) -> str:
        """Create a milestone using gh CLI."""
        cmd = ['gh', 'api', f'repos/{repo}/milestones', 
               '-X', 'POST',
               '-f', f'title={title}',
               '-f', f'description={description}']
        
        if due_date:
            cmd.extend(['-f', f'due_on={due_date}'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to create milestone: {result.stderr}")
        
        milestone_data = json.loads(result.stdout)
        return milestone_data['html_url'], milestone_data['number']
    
    def create_issue_from_file(self, repo: str, file_path: str, milestone: Optional[int] = None, 
                              labels: Optional[List[str]] = None) -> str:
        """Create an issue from a markdown file using gh CLI."""
        cmd = ['gh', 'issue', 'create', 
               '--repo', repo,
               '--body-file', file_path]
        
        if milestone:
            cmd.extend(['--milestone', str(milestone)])
        
        if labels:
            cmd.extend(['--label', ','.join(labels)])
        
        # Read title from file (first line)
        with open(file_path, 'r') as f:
            title = f.readline().strip().lstrip('#').strip()
        
        cmd.extend(['--title', title])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to create issue: {result.stderr}")
        
        # Extract issue URL from output
        return result.stdout.strip()
    
    def create_issues_batch(self, repo: str, issues_data: List[Dict], 
                           milestone: Optional[int] = None) -> List[str]:
        """Create multiple issues from markdown content."""
        created_issues = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, issue in enumerate(issues_data):
                # Create markdown file
                file_path = Path(tmpdir) / f"issue_{i}.md"
                
                # Write title as H1 and body
                content = f"# {issue['title']}\n\n{issue['body']}"
                file_path.write_text(content)
                
                # Create issue
                try:
                    url = self.create_issue_from_file(
                        repo, 
                        str(file_path), 
                        milestone=milestone,
                        labels=issue.get('labels', [])
                    )
                    created_issues.append(url)
                except Exception as e:
                    print(f"Warning: Failed to create issue '{issue['title']}': {e}")
        
        return created_issues