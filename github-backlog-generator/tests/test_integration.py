"""Integration tests for the complete workflow."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from github_backlog_generator.cli import main
from github_backlog_generator.unified_generator import UnifiedGenerator


class TestIntegration:
    """Integration tests for the complete backlog generation workflow."""
    
    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_generators(self):
        """Mock all generator classes."""
        with patch('github_backlog_generator.unified_generator.PhaseGenerator') as mock_phase, \
             patch('github_backlog_generator.unified_generator.EpicGenerator') as mock_epic, \
             patch('github_backlog_generator.unified_generator.TaskGenerator') as mock_task, \
             patch('github_backlog_generator.unified_generator.ReadmeParser') as mock_parser, \
             patch('github_backlog_generator.unified_generator.GitHubClient') as mock_github:
            
            yield {
                'phase': mock_phase,
                'epic': mock_epic,
                'task': mock_task,
                'parser': mock_parser,
                'github': mock_github
            }
    
    def test_cli_generate_command(self, runner, mock_env_vars):
        """Test the CLI generate command."""
        with patch('github_backlog_generator.cli.UnifiedGenerator') as mock_generator:
            # Mock the generator instance
            generator_instance = MagicMock()
            mock_generator.return_value = generator_instance
            
            # Mock phase selection
            generator_instance.select_phase.return_value = 1
            
            # Mock phase generation
            generator_instance.generate_phase.return_value = {
                'phase': {'title': 'Test Phase'},
                'epics': [{'title': 'Test Epic'}]
            }
            
            # Test dry run
            result = runner.invoke(main, ['generate', 'https://github.com/test/repo', '--dry-run'])
            assert result.exit_code == 0
            assert 'Phase generated successfully!' in result.output
    
    def test_unified_generator_workflow(self, mock_generators, mock_env_vars):
        """Test the complete unified generator workflow."""
        # Setup mocks
        mock_readme_content = "# Test Project\nA test project"
        mock_project_data = {
            'title': 'Test Project',
            'description': 'A test project',
            'domain': 'general',
            'features': ['feature1'],
            'techStack': ['Python']
        }
        
        # Configure parser mock
        parser_instance = mock_generators['parser'].return_value
        parser_instance.parse.return_value = mock_project_data
        
        # Configure GitHub mock
        github_instance = mock_generators['github'].return_value
        mock_repo = MagicMock()
        github_instance.get_repo.return_value = mock_repo
        github_instance.get_readme.return_value = mock_readme_content
        
        # Configure phase generator mock
        phase_generator = mock_generators['phase'].return_value
        phase_generator.generate_phases.return_value = [
            {
                'id': 'discovery',
                'title': 'Discovery Phase',
                'description': 'Initial discovery',
                'suggestedRoles': ['PM'],
                'dueDate': '2024-02-01'
            }
        ]
        
        # Configure epic generator mock
        epic_generator = mock_generators['epic'].return_value
        epic_generator.generate_epics_for_phase.return_value = [
            {
                'title': 'Research Epic',
                'description': 'User research',
                'suggestedRoles': ['Researcher'],
                'tasks': [
                    {
                        'title': 'Interview users',
                        'description': 'Conduct interviews',
                        'suggestedRole': 'Researcher'
                    }
                ]
            }
        ]
        
        # Configure task generator mock
        task_generator = mock_generators['task'].return_value
        task_generator.generate_task_description.return_value = {
            'title': 'Interview users',
            'description': 'Detailed description',
            'acceptanceCriteria': ['Criteria 1'],
            'technicalNotes': 'Notes',
            'dependencies': []
        }
        
        # Create unified generator
        generator = UnifiedGenerator('test-anthropic-key', 'test-github-token')
        
        # Test phase generation
        result = generator.generate_phase('https://github.com/test/repo', 1)
        
        assert result is not None
        assert 'phase' in result
        assert 'epics' in result
        assert result['phase']['title'] == 'Discovery Phase'
        assert len(result['epics']) == 1
        assert result['epics'][0]['title'] == 'Research Epic'
    
    def test_github_integration(self, mock_generators, mock_env_vars):
        """Test GitHub issue creation integration."""
        # Setup phase data
        phase_data = {
            'phase': {
                'title': 'Test Phase',
                'description': 'Test description',
                'dueDate': '2024-02-01'
            },
            'epics': [
                {
                    'title': 'Test Epic',
                    'description': 'Epic description',
                    'tasks': [
                        {
                            'title': 'Test Task',
                            'description': 'Task description',
                            'acceptanceCriteria': ['AC1'],
                            'priority': 'high'
                        }
                    ]
                }
            ]
        }
        
        # Configure GitHub mock
        github_instance = mock_generators['github'].return_value
        mock_repo = MagicMock()
        github_instance.get_repo.return_value = mock_repo
        
        mock_milestone = MagicMock()
        mock_milestone.number = 1
        github_instance.create_milestone.return_value = mock_milestone
        
        mock_epic_issue = MagicMock()
        mock_epic_issue.number = 42
        github_instance.create_epic_issue.return_value = mock_epic_issue
        
        mock_task_issue = MagicMock()
        mock_task_issue.number = 100
        github_instance.create_task_issue.return_value = mock_task_issue
        
        # Create unified generator
        generator = UnifiedGenerator('test-anthropic-key', 'test-github-token')
        
        # Test creating GitHub issues
        generator.create_github_issues('test/repo', phase_data)
        
        # Verify calls
        github_instance.create_milestone.assert_called_once()
        github_instance.create_epic_issue.assert_called_once()
        github_instance.create_task_issue.assert_called_once()
    
    @pytest.mark.parametrize("phase_number,expected_phase_count", [
        (1, 6),  # Standard phases
        (2, 6),
        (3, 6),
    ])
    def test_phase_selection(self, mock_generators, mock_env_vars, phase_number, expected_phase_count):
        """Test phase selection and generation."""
        # Configure phase generator to return multiple phases
        phases = []
        for i in range(expected_phase_count):
            phases.append({
                'id': f'phase-{i+1}',
                'title': f'Phase {i+1}',
                'description': f'Description {i+1}',
                'suggestedRoles': ['Role1']
            })
        
        phase_generator = mock_generators['phase'].return_value
        phase_generator.generate_phases.return_value = phases
        
        # Configure other mocks
        mock_generators['parser'].return_value.parse.return_value = {'title': 'Test'}
        mock_generators['github'].return_value.get_readme.return_value = "# Test"
        mock_generators['epic'].return_value.generate_epics_for_phase.return_value = []
        
        generator = UnifiedGenerator('test-key', 'test-token')
        
        # Mock user input for phase selection
        with patch('builtins.input', return_value=str(phase_number)):
            selected = generator.select_phase('test/repo')
            assert selected == phase_number
    
    def test_error_handling(self, mock_generators, mock_env_vars):
        """Test error handling throughout the workflow."""
        # Test API error handling
        phase_generator = mock_generators['phase'].return_value
        phase_generator.generate_phases.side_effect = Exception("API Error")
        
        generator = UnifiedGenerator('test-key', 'test-token')
        
        with pytest.raises(Exception, match="API Error"):
            generator.generate_phase('test/repo', 1)
        
        # Test GitHub error handling
        github_instance = mock_generators['github'].return_value
        github_instance.get_repo.side_effect = Exception("Repository not found")
        
        generator = UnifiedGenerator('test-key', 'test-token')
        
        with pytest.raises(Exception, match="Repository not found"):
            generator.generate_phase('test/repo', 1)
    
    def test_json_export(self, mock_generators, mock_env_vars, tmp_path):
        """Test exporting phase data to JSON."""
        phase_data = {
            'phase': {'title': 'Test Phase'},
            'epics': [{'title': 'Test Epic'}]
        }
        
        # Configure mocks to return phase data
        mock_generators['parser'].return_value.parse.return_value = {'title': 'Test'}
        mock_generators['github'].return_value.get_readme.return_value = "# Test"
        mock_generators['phase'].return_value.generate_phases.return_value = [phase_data['phase']]
        mock_generators['epic'].return_value.generate_epics_for_phase.return_value = phase_data['epics']
        
        generator = UnifiedGenerator('test-key', 'test-token')
        
        # Generate phase
        result = generator.generate_phase('test/repo', 1)
        
        # Export to JSON
        output_file = tmp_path / "phase.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Verify JSON file
        assert output_file.exists()
        with open(output_file) as f:
            loaded_data = json.load(f)
        
        assert loaded_data['phase']['title'] == 'Test Phase'
        assert len(loaded_data['epics']) == 1