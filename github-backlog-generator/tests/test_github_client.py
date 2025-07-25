"""Unit tests for GitHub client module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from github_backlog_generator.github_client import GitHubClient


class TestGitHubClient:
    """Test cases for GitHubClient class."""
    
    @pytest.fixture
    def mock_github(self):
        """Create a mock GitHub instance."""
        with patch('github_backlog_generator.github_client.Github') as mock:
            yield mock
    
    @pytest.fixture
    def github_client(self, mock_github):
        """Create a GitHubClient instance with mocked PyGithub."""
        mock_instance = MagicMock()
        mock_github.return_value = mock_instance
        return GitHubClient("test-token")
    
    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        repo = MagicMock()
        repo.name = "test-repo"
        repo.owner.login = "test-owner"
        repo.default_branch = "main"
        return repo
    
    @pytest.fixture
    def mock_readme(self):
        """Create a mock readme file."""
        readme = MagicMock()
        readme.decoded_content = b"# Test Project\nA test project for unit testing"
        return readme
    
    def test_init(self, mock_github):
        """Test GitHubClient initialization."""
        client = GitHubClient("test-token")
        mock_github.assert_called_once_with("test-token")
        assert client.github is not None
    
    def test_get_repo(self, github_client, mock_repo):
        """Test getting a repository."""
        github_client.github.get_repo.return_value = mock_repo
        
        repo = github_client.get_repo("test-owner/test-repo")
        
        assert repo.name == "test-repo"
        assert repo.owner.login == "test-owner"
        github_client.github.get_repo.assert_called_once_with("test-owner/test-repo")
    
    def test_get_readme(self, github_client, mock_repo, mock_readme):
        """Test fetching README content."""
        mock_repo.get_readme.return_value = mock_readme
        
        content = github_client.get_readme(mock_repo)
        
        assert content == "# Test Project\nA test project for unit testing"
        mock_repo.get_readme.assert_called_once()
    
    def test_get_readme_not_found(self, github_client, mock_repo):
        """Test handling missing README."""
        mock_repo.get_readme.side_effect = Exception("404 Not Found")
        
        content = github_client.get_readme(mock_repo)
        
        assert content == ""
        mock_repo.get_readme.assert_called_once()
    
    def test_create_milestone(self, github_client, mock_repo):
        """Test creating a milestone."""
        mock_milestone = MagicMock()
        mock_milestone.number = 1
        mock_milestone.title = "Phase 1 - Discovery"
        mock_repo.create_milestone.return_value = mock_milestone
        
        phase_data = {
            'title': 'Phase 1 - Discovery',
            'description': 'Initial discovery phase',
            'dueDate': '2024-02-01T00:00:00'
        }
        
        milestone = github_client.create_milestone(mock_repo, phase_data)
        
        assert milestone.number == 1
        assert milestone.title == "Phase 1 - Discovery"
        
        # Verify create_milestone was called with correct args
        call_args = mock_repo.create_milestone.call_args
        assert call_args.kwargs['title'] == 'Phase 1 - Discovery'
        assert call_args.kwargs['description'] == 'Initial discovery phase'
        assert 'due_on' in call_args.kwargs
    
    def test_create_milestone_no_due_date(self, github_client, mock_repo):
        """Test creating milestone without due date."""
        mock_milestone = MagicMock()
        mock_repo.create_milestone.return_value = mock_milestone
        
        phase_data = {
            'title': 'Phase 1',
            'description': 'Test phase'
            # No dueDate
        }
        
        milestone = github_client.create_milestone(mock_repo, phase_data)
        
        call_args = mock_repo.create_milestone.call_args
        assert call_args.kwargs.get('due_on') is None
    
    def test_create_epic_issue(self, github_client, mock_repo):
        """Test creating an epic issue."""
        mock_issue = MagicMock()
        mock_issue.number = 42
        mock_issue.title = "[EPIC] Build Authentication"
        mock_repo.create_issue.return_value = mock_issue
        
        mock_milestone = MagicMock()
        mock_milestone.number = 1
        
        mock_label = MagicMock()
        mock_label.name = "epic"
        mock_repo.get_label.return_value = mock_label
        
        epic_data = {
            'title': 'Build Authentication',
            'description': 'Implement auth system',
            'tasks': [
                {'title': 'Task 1', 'description': 'First task'},
                {'title': 'Task 2', 'description': 'Second task'}
            ]
        }
        
        epic = github_client.create_epic_issue(mock_repo, epic_data, mock_milestone)
        
        assert epic.number == 42
        assert epic.title == "[EPIC] Build Authentication"
        
        # Verify issue creation
        call_args = mock_repo.create_issue.call_args
        assert call_args.kwargs['title'] == '[EPIC] Build Authentication'
        assert 'Team Composition' in call_args.kwargs['body']
        assert '- [ ] Task 1:' in call_args.kwargs['body']
        assert '- [ ] Task 2:' in call_args.kwargs['body']
        assert call_args.kwargs['milestone'] == mock_milestone
        assert mock_label in call_args.kwargs['labels']
    
    def test_create_epic_issue_no_label(self, github_client, mock_repo):
        """Test creating epic when 'epic' label doesn't exist."""
        mock_issue = MagicMock()
        mock_repo.create_issue.return_value = mock_issue
        
        # Simulate label not found
        mock_repo.get_label.side_effect = Exception("404 Not Found")
        
        epic_data = {'title': 'Test Epic', 'description': 'Test', 'tasks': []}
        milestone = MagicMock()
        
        epic = github_client.create_epic_issue(mock_repo, epic_data, milestone)
        
        # Should still create issue, just without label
        call_args = mock_repo.create_issue.call_args
        assert call_args.kwargs['labels'] == []
    
    def test_create_task_issue(self, github_client, mock_repo):
        """Test creating a task issue."""
        mock_issue = MagicMock()
        mock_issue.number = 100
        mock_issue.title = "Implement login form"
        mock_repo.create_issue.return_value = mock_issue
        
        mock_milestone = MagicMock()
        mock_milestone.number = 1
        
        mock_epic = MagicMock()
        mock_epic.number = 42
        
        task_data = {
            'title': 'Implement login form',
            'description': '### Description\nImplement the login form',
            'acceptanceCriteria': ['Form validates email', 'Shows errors'],
            'technicalNotes': 'Use React Hook Form',
            'dependencies': ['Design system ready'],
            'suggestedRole': 'Frontend Developer',
            'priority': 'high',
            'estimatedEffort': 'medium'
        }
        
        issue = github_client.create_task_issue(
            mock_repo, task_data, mock_milestone, mock_epic
        )
        
        assert issue.number == 100
        assert issue.title == "Implement login form"
        
        # Verify issue body format
        call_args = mock_repo.create_issue.call_args
        body = call_args.kwargs['body']
        assert '### Description' in body
        assert 'Implement the login form' in body
        assert '**Epic:** #42' in body
        assert '### Acceptance Criteria' in body
        assert '- [ ] Form validates email' in body
        assert '### Technical Notes' in body
        assert 'React Hook Form' in body
        assert '### Dependencies' in body
        assert '**Assigned Role:** Frontend Developer' in body
        assert '**Priority:** high' in body
        assert '**Estimated Effort:** medium' in body
    
    def test_create_task_issue_with_labels(self, github_client, mock_repo):
        """Test creating task issue with priority and role labels."""
        mock_issue = MagicMock()
        mock_repo.create_issue.return_value = mock_issue
        
        # Mock labels
        priority_label = MagicMock()
        priority_label.name = "priority:high"
        
        role_label = MagicMock()
        role_label.name = "role:backend"
        
        # First call returns priority label, second returns role label
        mock_repo.get_label.side_effect = [priority_label, role_label]
        
        task_data = {
            'title': 'Test Task',
            'description': 'Test',
            'acceptanceCriteria': [],
            'priority': 'high',
            'suggestedRole': 'Backend Developer'
        }
        
        github_client.create_task_issue(
            mock_repo, task_data, MagicMock(), MagicMock()
        )
        
        call_args = mock_repo.create_issue.call_args
        labels = call_args.kwargs['labels']
        assert priority_label in labels
        assert role_label in labels
    
    def test_parse_github_url(self, github_client):
        """Test parsing various GitHub URL formats."""
        # Standard HTTPS URL
        owner, repo = github_client.parse_github_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"
        
        # With .git extension
        owner, repo = github_client.parse_github_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"
        
        # SSH URL
        owner, repo = github_client.parse_github_url("git@github.com:owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"
        
        # With trailing slash
        owner, repo = github_client.parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"
        
        # Just owner/repo format
        owner, repo = github_client.parse_github_url("owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_github_url_invalid(self, github_client):
        """Test parsing invalid GitHub URLs."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            github_client.parse_github_url("not-a-url")
        
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            github_client.parse_github_url("https://example.com/repo")
        
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            github_client.parse_github_url("")