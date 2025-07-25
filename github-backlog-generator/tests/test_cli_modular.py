"""Tests for the modular CLI."""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock
from unittest.mock import Mock, MagicMock, patch, call

import pytest
from click.testing import CliRunner

from github_backlog_generator.cli_modular import cli, BacklogManager


class TestBacklogManager:
    """Test the BacklogManager class."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Create a BacklogManager instance with temp directory."""
        # Use tmp_path as parent directory
        with patch('github_backlog_generator.cli_modular.Path') as mock_path:
            # Make Path() return paths under tmp_path
            def path_side_effect(path_str):
                if path_str.startswith('.backlog-'):
                    return tmp_path / path_str
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            manager = BacklogManager("test-owner", "test-repo")
            manager.base_dir = tmp_path / ".backlog-test-owner-test-repo"
            manager.base_dir.mkdir(exist_ok=True)
            manager.metadata_file = manager.base_dir / "metadata.json"
            manager.phases_dir = manager.base_dir / "phases"
            manager.phases_dir.mkdir(exist_ok=True)
            return manager
    
    def test_init(self, tmp_path):
        """Test BacklogManager initialization."""
        with patch('github_backlog_generator.cli_modular.Path') as mock_path:
            mock_path.return_value = tmp_path / ".backlog-test-owner-test-repo"
            manager = BacklogManager("test-owner", "test-repo")
            
            assert manager.owner == "test-owner"
            assert manager.repo == "test-repo"
    
    def test_save_and_load_metadata(self, manager):
        """Test saving and loading project metadata."""
        project_data = {
            'title': 'Test Project',
            'domain': 'web',
            'complexity': 'medium',
            'features': ['feature1', 'feature2']
        }
        
        manager.save_metadata(project_data)
        assert manager.metadata_file.exists()
        
        loaded = manager.load_metadata()
        assert loaded['owner'] == 'test-owner'
        assert loaded['repo'] == 'test-repo'
        assert loaded['project_data'] == project_data
        assert 'created_at' in loaded
        assert 'last_updated' in loaded
    
    def test_save_and_load_phases(self, manager):
        """Test saving and loading phases."""
        phases = [
            {
                'number': 1,
                'title': 'Discovery',
                'description': 'Research phase',
                'id': 'phase-1',
                'dueDate': datetime.now().isoformat()
            },
            {
                'number': 2,
                'title': 'Planning',
                'description': 'Planning phase',
                'id': 'phase-2',
                'dueDate': datetime.now().isoformat()
            }
        ]
        
        manager.save_phases(phases)
        
        # Check phases.json exists
        phases_file = manager.phases_dir / "phases.json"
        assert phases_file.exists()
        
        # Check individual phase directories
        assert (manager.phases_dir / "phase1").exists()
        assert (manager.phases_dir / "phase2").exists()
        assert (manager.phases_dir / "phase1" / "phase.json").exists()
        assert (manager.phases_dir / "phase2" / "phase.json").exists()
        
        # Load and verify
        loaded = manager.load_phases()
        assert loaded == phases
    
    def test_save_and_load_epics(self, manager):
        """Test saving and loading epics."""
        epics = [
            {
                'title': 'Epic 1',
                'description': 'First epic',
                'suggestedRoles': ['Developer'],
                'tasks': []
            },
            {
                'title': 'Epic 2',
                'description': 'Second epic',
                'suggestedRoles': ['Designer'],
                'tasks': []
            }
        ]
        
        manager.save_epics(1, epics)
        
        # Check files exist
        epics_file = manager.phases_dir / "phase1" / "epics.json"
        assert epics_file.exists()
        assert (manager.phases_dir / "phase1" / "epic1").exists()
        assert (manager.phases_dir / "phase1" / "epic2").exists()
        
        # Load and verify
        loaded = manager.load_epics(1)
        assert loaded == epics
    
    def test_save_and_load_issues(self, manager):
        """Test saving and loading issues."""
        issues = [
            {
                'title': 'Issue 1',
                'description': 'First issue',
                'priority': 'high'
            },
            {
                'title': 'Issue 2',
                'description': 'Second issue',
                'priority': 'medium'
            }
        ]
        
        manager.save_issues(1, 1, issues)
        
        # Check file exists
        issues_file = manager.phases_dir / "phase1" / "epic1" / "issues.json"
        assert issues_file.exists()
        
        # Load and verify
        loaded = manager.load_issues(1, 1)
        assert loaded == issues
    
    def test_milestone_mapping(self, manager):
        """Test milestone mapping save and load."""
        mapping = {1: 101, 2: 102, 3: 103}
        
        manager.save_milestone_mapping(mapping)
        loaded = manager.get_milestone_mapping()
        
        assert loaded == mapping
    
    def test_load_nonexistent_data(self, manager):
        """Test loading data that doesn't exist."""
        assert manager.load_metadata() is None
        assert manager.load_phases() is None
        assert manager.load_epics(1) is None
        assert manager.load_issues(1, 1) is None
        assert manager.get_milestone_mapping() == {}


class TestCLICommands:
    """Test CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_env(self):
        """Mock environment variables."""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test-api-key',
            'GITHUB_TOKEN': 'test-github-token'
        }):
            yield
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'GitHub Backlog Generator' in result.output
    
    @patch('github_backlog_generator.cli_modular.GitHubClient')
    @patch('github_backlog_generator.cli_modular.ReadmeParser')
    def test_init_command(self, mock_parser, mock_github, runner, mock_env, tmp_path):
        """Test init command."""
        # Setup mocks
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.parse_repo_url.return_value = ('owner', 'repo')
        mock_github_instance.sparse_checkout_readme.return_value = "# Test README"
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse_readme_content.return_value = {
            'title': 'Test Project',
            'domain': 'web',
            'complexity': 'medium',
            'features': ['feature1', 'feature2'],
            'techStack': ['Python', 'React']
        }
        
        with patch('github_backlog_generator.cli_modular.BacklogManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.base_dir = Path('.backlog-owner-repo')
            
            result = runner.invoke(cli, ['init', 'https://github.com/owner/repo'])
            
            assert result.exit_code == 0
            assert 'Repository: owner/repo' in result.output
            assert 'Initialization complete!' in result.output
            
            # Verify manager methods were called
            mock_manager.save_metadata.assert_called_once()
            mock_manager.save_phases.assert_called_once()
    
    def test_init_command_no_api_key(self, runner):
        """Test init command without API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(cli, ['init', 'https://github.com/owner/repo'])
            assert result.exit_code == 1
            assert 'ANTHROPIC_API_KEY not found' in result.output
    
    @patch('github_backlog_generator.cli_modular.GitHubClient')
    def test_milestones_command(self, mock_github, runner, mock_env):
        """Test milestones command."""
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.parse_repo_url.return_value = ('owner', 'repo')
        mock_github_instance.create_milestones.return_value = [
            'https://github.com/owner/repo/milestone/1'
        ]
        
        with patch('github_backlog_generator.cli_modular.BacklogManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_phases.return_value = [
                {
                    'number': 1,
                    'title': 'Discovery',
                    'description': 'Research phase',
                    'id': 'phase-1',
                    'dueDate': datetime.now().isoformat()
                }
            ]
            
            # Test dry run
            result = runner.invoke(cli, ['milestones', 'https://github.com/owner/repo', '--dry-run'])
            assert result.exit_code == 0
            assert 'Dry run mode' in result.output
            
            # Test actual creation
            result = runner.invoke(cli, ['milestones', 'https://github.com/owner/repo'], input='yes\n')
            assert result.exit_code == 0
            assert 'Created 1 milestones successfully!' in result.output
            mock_manager.save_milestone_mapping.assert_called()
    
    def test_milestones_command_no_phases(self, runner, mock_env):
        """Test milestones command without phases."""
        with patch('github_backlog_generator.cli_modular.GitHubClient'):
            with patch('github_backlog_generator.cli_modular.BacklogManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                mock_manager.load_phases.return_value = None
                
                result = runner.invoke(cli, ['milestones', 'https://github.com/owner/repo'])
                assert result.exit_code == 1
                assert 'No phases found' in result.output
    
    @patch('github_backlog_generator.cli_modular.GitHubClient')
    @patch('github_backlog_generator.cli_modular.EpicGenerator')
    def test_generate_epics(self, mock_epic_gen, mock_github, runner, mock_env):
        """Test generate command for epics."""
        # Setup mocks
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.parse_repo_url.return_value = ('owner', 'repo')
        mock_github_instance.create_epic_only.return_value = {
            'number': 1,
            'url': 'https://github.com/owner/repo/issues/1'
        }
        
        mock_epic_gen_instance = Mock()
        mock_epic_gen.return_value = mock_epic_gen_instance
        mock_epic_gen_instance.generate_epics_for_phase.return_value = [
            {
                'title': 'Epic 1',
                'description': 'First epic',
                'suggestedRoles': ['Developer'],
                'tasks': []
            }
        ]
        
        with patch('github_backlog_generator.cli_modular.BacklogManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_metadata.return_value = {
                'project_data': {
                    'title': 'Test Project',
                    'domain': 'web',
                    'complexity': 'medium'
                }
            }
            mock_manager.load_phases.return_value = [
                {
                    'number': 1,
                    'title': 'Discovery',
                    'description': 'Research phase'
                }
            ]
            mock_manager.get_milestone_mapping.return_value = {1: 101}
            
            # Test epic generation
            result = runner.invoke(cli, ['generate', 'owner/repo', '--phase', '1'])
            
            assert result.exit_code == 0
            assert 'Generated 1 epics' in result.output
            mock_manager.save_epics.assert_called_once()
    
    @patch('github_backlog_generator.cli_modular.GitHubClient')
    @patch('github_backlog_generator.cli_modular.TaskGenerator')
    def test_generate_issues(self, mock_task_gen, mock_github, runner, mock_env):
        """Test generate command for issues."""
        # Setup mocks
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.parse_repo_url.return_value = ('owner', 'repo')
        mock_github_instance.create_task_issue.return_value = 'https://github.com/owner/repo/issues/2'
        
        mock_task_gen_instance = Mock()
        mock_task_gen.return_value = mock_task_gen_instance
        mock_task_gen_instance.generate_tasks_for_epic.return_value = [
            {
                'title': 'Task 1',
                'suggestedRole': 'Developer',
                'priority': 'high',
                'estimatedEffort': 'medium'
            }
        ]
        mock_task_gen_instance.generate_task_description.return_value = {
            'description': 'Task description',
            'acceptanceCriteria': ['AC1', 'AC2'],
            'technicalNotes': 'Technical notes',
            'dependencies': []
        }
        
        with patch('github_backlog_generator.cli_modular.BacklogManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_metadata.return_value = {
                'project_data': {'title': 'Test Project'}
            }
            mock_manager.load_phases.return_value = [
                {'number': 1, 'title': 'Discovery', 'description': 'Research'}
            ]
            mock_manager.load_epics.return_value = [
                {
                    'title': 'Epic 1',
                    'description': 'First epic',
                    'suggestedRoles': ['Developer'],
                    'github_number': 1
                }
            ]
            mock_manager.get_milestone_mapping.return_value = {1: 101}
            
            # Test single epic
            result = runner.invoke(cli, ['generate', 'owner/repo', '--phase', '1', '--epic', '1'])
            assert result.exit_code == 0
            assert 'Generated 1 issues' in result.output
            mock_manager.save_issues.assert_called_once()
            
            # Test all epics
            result = runner.invoke(cli, ['generate', 'owner/repo', '--phase', '1', '--all-epics'])
            assert result.exit_code == 0
            assert 'Generating issues for all 1 epics' in result.output
    
    def test_generate_invalid_phase(self, runner, mock_env):
        """Test generate command with invalid phase."""
        result = runner.invoke(cli, ['generate', 'owner/repo', '--phase', '9'])
        assert result.exit_code == 1
        assert 'Phase must be between 1 and 8' in result.output
    
    def test_generate_both_epic_and_all_epics(self, runner, mock_env):
        """Test generate command with both --epic and --all-epics."""
        result = runner.invoke(cli, ['generate', 'owner/repo', '--phase', '1', '--epic', '1', '--all-epics'])
        assert result.exit_code == 1
        assert 'Cannot specify both --epic and --all-epics' in result.output
    
    def test_status_command(self, runner):
        """Test status command."""
        with patch('github_backlog_generator.cli_modular.BacklogManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.base_dir = Path('.backlog-owner-repo')
            mock_manager.base_dir.exists.return_value = True
            mock_manager.load_metadata.return_value = {
                'project_data': {'title': 'Test Project'},
                'created_at': datetime.now().isoformat()
            }
            mock_manager.load_phases.return_value = [
                {
                    'number': 1,
                    'title': 'Discovery',
                    'description': 'Research phase'
                }
            ]
            mock_manager.load_epics.return_value = [{'title': 'Epic 1'}]
            mock_manager.load_issues.return_value = [{'title': 'Issue 1'}]
            mock_manager.get_milestone_mapping.return_value = {1: 101}
            
            result = runner.invoke(cli, ['status', 'https://github.com/owner/repo'])
            
            assert result.exit_code == 0
            assert 'Project: Test Project' in result.output
            assert 'Generation Status' in result.output
    
    def test_status_no_backlog(self, runner):
        """Test status command when no backlog exists."""
        with patch('github_backlog_generator.cli_modular.BacklogManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.base_dir = Path('.backlog-owner-repo')
            mock_manager.base_dir.exists.return_value = False
            
            result = runner.invoke(cli, ['status', 'https://github.com/owner/repo'])
            
            assert result.exit_code == 1
            assert 'No backlog found' in result.output


class TestIntegration:
    """Integration tests for the full workflow."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_apis(self):
        """Mock all external APIs."""
        with patch('github_backlog_generator.cli_modular.GitHubClient') as mock_github:
            with patch('github_backlog_generator.cli_modular.ReadmeParser') as mock_parser:
                with patch('github_backlog_generator.cli_modular.EpicGenerator') as mock_epic_gen:
                    with patch('github_backlog_generator.cli_modular.TaskGenerator') as mock_task_gen:
                        # Setup GitHub client
                        mock_github_instance = Mock()
                        mock_github.return_value = mock_github_instance
                        mock_github_instance.parse_repo_url.return_value = ('test-owner', 'test-repo')
                        mock_github_instance.sparse_checkout_readme.return_value = "# Test README"
                        mock_github_instance.create_milestones.return_value = ['https://github.com/test-owner/test-repo/milestone/1']
                        mock_github_instance.create_epic_only.return_value = {
                            'number': 1,
                            'url': 'https://github.com/test-owner/test-repo/issues/1'
                        }
                        mock_github_instance.create_task_issue.return_value = 'https://github.com/test-owner/test-repo/issues/2'
                        
                        # Setup parser
                        mock_parser_instance = Mock()
                        mock_parser.return_value = mock_parser_instance
                        mock_parser_instance.parse_readme_content.return_value = {
                            'title': 'Test Project',
                            'domain': 'web',
                            'complexity': 'medium',
                            'features': ['feature1'],
                            'techStack': ['Python']
                        }
                        
                        # Setup epic generator
                        mock_epic_gen_instance = Mock()
                        mock_epic_gen.return_value = mock_epic_gen_instance
                        mock_epic_gen_instance.generate_epics_for_phase.return_value = [
                            {
                                'title': 'Test Epic',
                                'description': 'Test epic description',
                                'suggestedRoles': ['Developer'],
                                'tasks': []
                            }
                        ]
                        
                        # Setup task generator
                        mock_task_gen_instance = Mock()
                        mock_task_gen.return_value = mock_task_gen_instance
                        mock_task_gen_instance.generate_tasks_for_epic.return_value = [
                            {
                                'title': 'Test Task',
                                'suggestedRole': 'Developer',
                                'priority': 'high',
                                'estimatedEffort': 'medium'
                            }
                        ]
                        mock_task_gen_instance.generate_task_description.return_value = {
                            'description': 'Test description',
                            'acceptanceCriteria': ['AC1'],
                            'technicalNotes': 'Notes',
                            'dependencies': []
                        }
                        
                        yield {
                            'github': mock_github_instance,
                            'parser': mock_parser_instance,
                            'epic_gen': mock_epic_gen_instance,
                            'task_gen': mock_task_gen_instance
                        }
    
    def test_full_workflow(self, runner, mock_apis, tmp_path):
        """Test the complete workflow from init to issue generation."""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test-api-key',
            'GITHUB_TOKEN': 'test-github-token'
        }):
            # Use temporary directory for backlog
            with runner.isolated_filesystem(temp_dir=tmp_path):
                # Step 1: Initialize
                result = runner.invoke(cli, ['init', 'https://github.com/test-owner/test-repo'])
                assert result.exit_code == 0
                assert 'Initialization complete!' in result.output
                
                # Verify directory structure
                backlog_dir = Path('.backlog-test-owner-test-repo')
                assert backlog_dir.exists()
                assert (backlog_dir / 'metadata.json').exists()
                assert (backlog_dir / 'phases' / 'phases.json').exists()
                
                # Step 2: Create milestones
                result = runner.invoke(cli, ['milestones', 'https://github.com/test-owner/test-repo'], input='yes\n')
                assert result.exit_code == 0
                assert 'Created 1 milestones successfully!' in result.output
                
                # Step 3: Generate epics
                result = runner.invoke(cli, ['generate', 'test-owner/test-repo', '--phase', '1'])
                assert result.exit_code == 0
                assert 'Generated 1 epics' in result.output
                
                # Verify epic files
                assert (backlog_dir / 'phases' / 'phase1' / 'epics.json').exists()
                assert (backlog_dir / 'phases' / 'phase1' / 'epic1' / 'epic.json').exists()
                
                # Step 4: Generate issues
                result = runner.invoke(cli, ['generate', 'test-owner/test-repo', '--phase', '1', '--epic', '1'])
                assert result.exit_code == 0
                assert 'Generated 1 issues' in result.output
                
                # Verify issue files
                assert (backlog_dir / 'phases' / 'phase1' / 'epic1' / 'issues.json').exists()
                
                # Step 5: Check status
                result = runner.invoke(cli, ['status', 'test-owner/test-repo'])
                assert result.exit_code == 0
                assert 'Project: Test Project' in result.output
                assert 'Complete' in result.output