"""Integration tests for the complete CLI workflow."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from click.testing import CliRunner

from github_backlog_generator.cli import cli


class TestCLIIntegration:
    """Integration tests for the complete CLI workflow."""
    
    def create_sample_phases_file(self) -> str:
        """Create a sample phases file for testing."""
        phases_data = {
            "metadata": {
                "title": "Test Project",
                "description": "A test project for integration testing",
                "domain": "software-development",
                "generated_at": "2024-01-01T10:00:00Z"
            },
            "phases": [
                {
                    "title": "Planning Phase",
                    "description": "Plan and analyze the project requirements",
                    "order": 1,
                    "suggestedRoles": ["analyst", "project-manager"]
                },
                {
                    "title": "Design Phase", 
                    "description": "Design the system architecture and user interfaces",
                    "order": 2,
                    "suggestedRoles": ["designer", "architect"]
                },
                {
                    "title": "Development Phase",
                    "description": "Implement the core features and functionality",
                    "order": 3,
                    "suggestedRoles": ["developer", "engineer"]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f, indent=2)
            return f.name
    
    def test_generate_phases_command_integration(self):
        """Test the generate-phases command integration."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / 'test_phases.json'
            
            result = runner.invoke(cli, [
                'generate-phases',
                '--output', str(output_file)
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            
            # Validate generated content
            with open(output_file) as f:
                data = json.load(f)
            
            assert 'phases' in data
            assert 'metadata' in data
            assert len(data['phases']) > 0
            assert all('title' in phase for phase in data['phases'])
            assert all('description' in phase for phase in data['phases'])
    
    def test_complete_workflow_dry_run(self):
        """Test the complete workflow in dry-run mode."""
        runner = CliRunner()
        phases_file = self.create_sample_phases_file()
        
        try:
            with patch.dict('os.environ', {
                'ANTHROPIC_API_KEY': 'sk-test-key-123456789012345',
                'GITHUB_TOKEN': 'ghp_test_token_123456789012345678901234567890'
            }):
                # Mock all the CLI components
                with patch('github_backlog_generator.cli.BacklogManager') as mock_manager_class, \
                     patch('github_backlog_generator.cli.GitHubClient') as mock_github_class, \
                     patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
                    
                    # Set up mocks
                    mock_manager = Mock()
                    mock_manager_class.return_value = mock_manager
                    mock_manager.cost_tracker = None
                    
                    mock_github = Mock()
                    mock_github_class.return_value = mock_github
                    
                    mock_state_mgr = Mock()
                    mock_state_mgr.load_state.return_value = None
                    mock_state_mgr.check_concurrent_execution.return_value = None
                    mock_state_manager.return_value = mock_state_mgr
                    
                    # Mock the context manager
                    mock_state_mgr.__enter__ = Mock(return_value=mock_state_mgr)
                    mock_state_mgr.__exit__ = Mock(return_value=None)
                    
                    result = runner.invoke(cli, [
                        'run',
                        '--phases', phases_file,
                        '--repo', 'test-owner/test-repo',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert 'GitHub Backlog Generator - Full Workflow' in result.output
                    assert 'test-owner/test-repo' in result.output
                    assert 'Planning Phase' in result.output
                    assert 'Design Phase' in result.output
                    assert 'Development Phase' in result.output
        
        finally:
            Path(phases_file).unlink()
    
    def test_workflow_with_preprocessing(self):
        """Test workflow with LLM preprocessing enabled."""
        runner = CliRunner()
        phases_file = self.create_sample_phases_file()
        
        try:
            with patch.dict('os.environ', {
                'ANTHROPIC_API_KEY': 'sk-test-key-123456789012345',
                'GITHUB_TOKEN': 'ghp_test_token_123456789012345678901234567890'
            }):
                with patch('github_backlog_generator.cli.BacklogManager') as mock_manager_class, \
                     patch('github_backlog_generator.cli.GitHubClient') as mock_github_class, \
                     patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager, \
                     patch('github_backlog_generator.cli.preprocess_phases_with_llm') as mock_preprocess:
                    
                    # Set up mocks
                    mock_manager = Mock()
                    mock_manager_class.return_value = mock_manager
                    mock_manager.cost_tracker = None
                    
                    mock_github = Mock()
                    mock_github_class.return_value = mock_github
                    
                    mock_state_mgr = Mock()
                    mock_state_mgr.load_state.return_value = None
                    mock_state_mgr.check_concurrent_execution.return_value = None
                    mock_state_manager.return_value = mock_state_mgr
                    mock_state_mgr.__enter__ = Mock(return_value=mock_state_mgr)
                    mock_state_mgr.__exit__ = Mock(return_value=None)
                    
                    # Mock preprocessing to return modified phases
                    mock_preprocess.return_value = [
                        {
                            'number': 1,
                            'title': 'Planning Phase',
                            'description': 'Enhanced planning phase',
                            'suggestedRoles': ['analyst', 'project-manager']
                        },
                        {
                            'number': 2,
                            'title': 'Design Phase',
                            'description': 'Enhanced design phase based on planning',
                            'suggestedRoles': ['designer', 'architect'],
                            'preprocessing': {
                                'processed_at': '2024-01-01T10:00:00',
                                'reasoning': 'Enhanced based on planning phase'
                            }
                        }
                    ]
                    
                    result = runner.invoke(cli, [
                        'run',
                        '--phases', phases_file,
                        '--repo', 'test-owner/test-repo',
                        '--preprocess-phases',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert mock_preprocess.called
        
        finally:
            Path(phases_file).unlink()
    
    def test_summarize_command_integration(self):
        """Test the summarize command integration."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_repo_manager_class, \
             patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
            
            # Set up mock repository manager
            mock_manager = Mock()
            mock_repo_manager_class.return_value = mock_manager
            
            mock_phases = [
                {'number': 1, 'title': 'Planning', 'description': 'Plan project'},
                {'number': 2, 'title': 'Development', 'description': 'Develop features'}
            ]
            mock_epics = [
                {'phase': 1, 'title': 'Planning Epic 1'},
                {'phase': 2, 'title': 'Development Epic 1'}
            ]
            mock_issues = [
                {'phase': 1, 'title': 'Planning Issue 1'},
                {'phase': 1, 'title': 'Planning Issue 2'},
                {'phase': 2, 'title': 'Development Issue 1'}
            ]
            
            mock_manager.load_phases.return_value = mock_phases
            mock_manager.load_epics.return_value = mock_epics
            mock_manager.load_issues.return_value = mock_issues
            mock_manager.cost_tracker = None
            
            # Mock state manager
            mock_state_mgr = Mock()
            mock_state_mgr.load_state.return_value = None
            mock_state_manager.return_value = mock_state_mgr
            
            result = runner.invoke(cli, [
                'summarize',
                '--repo', 'test-owner/test-repo'
            ])
            
            assert result.exit_code == 0
            assert 'Enhanced Summary Report' in result.output
            assert 'test-owner/test-repo' in result.output
            assert 'Planning' in result.output
            assert 'Development' in result.output
    
    def test_error_handling_invalid_phases_file(self):
        """Test error handling for invalid phases file."""
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            f.flush()
            
            try:
                result = runner.invoke(cli, [
                    'run',
                    '--phases', f.name,
                    '--repo', 'test-owner/test-repo'
                ])
                
                assert result.exit_code == 1
                assert 'CLI Constraint Error' in result.output or 'Invalid JSON' in result.output
            
            finally:
                Path(f.name).unlink()
    
    def test_error_handling_invalid_repository(self):
        """Test error handling for invalid repository format."""
        runner = CliRunner()
        phases_file = self.create_sample_phases_file()
        
        try:
            result = runner.invoke(cli, [
                'run',
                '--phases', phases_file,
                '--repo', 'invalid-repo-format'
            ])
            
            assert result.exit_code == 1
            assert 'CLI Constraint Error' in result.output or 'Invalid repository format' in result.output
        
        finally:
            Path(phases_file).unlink()
    
    def test_error_handling_missing_api_key(self):
        """Test error handling for missing API key."""
        runner = CliRunner()
        phases_file = self.create_sample_phases_file()
        
        try:
            with patch.dict('os.environ', {}, clear=True):
                result = runner.invoke(cli, [
                    'run',
                    '--phases', phases_file,
                    '--repo', 'test-owner/test-repo'
                ])
                
                assert result.exit_code == 1
                assert 'ANTHROPIC_API_KEY not found' in result.output
        
        finally:
            Path(phases_file).unlink()
    
    def test_concurrent_execution_prevention(self):
        """Test concurrent execution prevention."""
        runner = CliRunner()
        phases_file = self.create_sample_phases_file()
        
        try:
            with patch.dict('os.environ', {
                'ANTHROPIC_API_KEY': 'sk-test-key-123456789012345',
                'GITHUB_TOKEN': 'ghp_test_token_123456789012345678901234567890'
            }):
                with patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
                    
                    # Mock concurrent execution detection
                    mock_state_mgr = Mock()
                    mock_state_mgr.check_concurrent_execution.return_value = {
                        'pid': 12345,
                        'locked_at': '2024-01-01T10:00:00',
                        'command': 'run --repo test/repo'
                    }
                    mock_state_manager.return_value = mock_state_mgr
                    
                    result = runner.invoke(cli, [
                        'run',
                        '--phases', phases_file,
                        '--repo', 'test-owner/test-repo',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 1
                    assert 'Concurrent execution detected' in result.output
        
        finally:
            Path(phases_file).unlink()
    
    def test_force_restart_override(self):
        """Test force restart override for concurrent execution."""
        runner = CliRunner()
        phases_file = self.create_sample_phases_file()
        
        try:
            with patch.dict('os.environ', {
                'ANTHROPIC_API_KEY': 'sk-test-key-123456789012345',
                'GITHUB_TOKEN': 'ghp_test_token_123456789012345678901234567890'
            }):
                with patch('github_backlog_generator.cli.BacklogManager') as mock_manager_class, \
                     patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
                    
                    # Set up mocks
                    mock_manager = Mock()
                    mock_manager_class.return_value = mock_manager
                    mock_manager.cost_tracker = None
                    
                    mock_state_mgr = Mock()
                    mock_state_mgr.load_state.return_value = None
                    # Concurrent execution but force restart bypasses check
                    mock_state_mgr.check_concurrent_execution.return_value = None
                    mock_state_manager.return_value = mock_state_mgr
                    mock_state_mgr.__enter__ = Mock(return_value=mock_state_mgr)
                    mock_state_mgr.__exit__ = Mock(return_value=None)
                    
                    result = runner.invoke(cli, [
                        'run',
                        '--phases', phases_file,
                        '--repo', 'test-owner/test-repo',
                        '--force-restart',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert 'GitHub Backlog Generator - Full Workflow' in result.output
        
        finally:
            Path(phases_file).unlink()
    
    def test_modular_commands_integration(self):
        """Test the modular CLI commands integration."""
        runner = CliRunner()
        
        # Test create-milestones command
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_phases.return_value = [
                {'number': 1, 'title': 'Phase 1', 'description': 'Test phase'}
            ]
            
            result = runner.invoke(cli, [
                'create-milestones',
                '--repo', 'test-owner/test-repo',
                '--dry-run'
            ])
            
            assert result.exit_code == 0
            assert 'Creating GitHub Milestones' in result.output
        
        # Test create-epics command  
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_phases.return_value = [
                {'number': 1, 'title': 'Phase 1', 'description': 'Test phase'}
            ]
            
            result = runner.invoke(cli, [
                'create-epics',
                '--repo', 'test-owner/test-repo',
                '--dry-run'
            ])
            
            assert result.exit_code == 0
            assert 'Generating Epics' in result.output
        
        # Test create-issues command
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_phases.return_value = [
                {'number': 1, 'title': 'Phase 1', 'description': 'Test phase'}
            ]
            mock_manager.load_epics.return_value = [
                {'number': 1, 'title': 'Epic 1', 'phase': 1}
            ]
            
            result = runner.invoke(cli, [
                'create-issues',
                '--repo', 'test-owner/test-repo',
                '--dry-run'
            ])
            
            assert result.exit_code == 0
            assert 'Generating Issues' in result.output


class TestCLIWorkflowStates:
    """Test CLI workflow with state management."""
    
    def test_resumable_workflow(self):
        """Test resumable workflow functionality."""
        runner = CliRunner()
        phases_file = self.create_sample_phases_file()
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch.dict('os.environ', {
                    'ANTHROPIC_API_KEY': 'sk-test-key-123456789012345',
                    'GITHUB_TOKEN': 'ghp_test_token_123456789012345678901234567890'
                }):
                    with patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
                        
                        # Mock resumable state
                        mock_state_mgr = Mock()
                        mock_state_mgr.load_state.return_value = {
                            'execution_id': 'test-123',
                            'current_step': 'phases_loaded',
                            'completed_steps': ['init'],
                            'phases': [{'title': 'Test Phase'}]
                        }
                        mock_state_mgr.can_resume.return_value = True
                        mock_state_mgr.get_resume_info.return_value = {
                            'execution_id': 'test-123',
                            'current_step': 'phases_loaded',
                            'completed_steps': ['init'],
                            'phases_count': 1
                        }
                        mock_state_mgr.check_concurrent_execution.return_value = None
                        mock_state_manager.return_value = mock_state_mgr
                        mock_state_mgr.__enter__ = Mock(return_value=mock_state_mgr)
                        mock_state_mgr.__exit__ = Mock(return_value=None)
                        
                        # Mock user choosing to resume
                        with patch('github_backlog_generator.state_manager.Confirm.ask', return_value=True):
                            result = runner.invoke(cli, [
                                'run',
                                '--phases', phases_file,
                                '--repo', 'test-owner/test-repo',
                                '--dry-run'
                            ])
                            
                            assert result.exit_code == 0
        
        finally:
            Path(phases_file).unlink()
    
    def create_sample_phases_file(self) -> str:
        """Create a sample phases file for testing."""
        phases_data = {
            "phases": [
                {
                    "title": "Test Phase",
                    "description": "A test phase",
                    "order": 1
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f)
            return f.name


if __name__ == '__main__':
    pytest.main([__file__])