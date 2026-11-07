"""Tests for the new CLI commands: phases, epics, issues, status."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from github_backlog_generator.cli import cli, BacklogManager


@pytest.fixture
def temp_backlog_dir():
    """Create a temporary backlog directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock backlog structure
        backlog_dir = temp_path / ".backlog-testowner-testrepo"
        backlog_dir.mkdir()
        
        # Create metadata.json
        metadata = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'project_data': {
                'title': 'Test Project',
                'domain': 'software',
                'complexity': 'medium'
            },
            'created_at': '2024-01-01T00:00:00',
            'last_updated': '2024-01-01T00:00:00'
        }
        
        with open(backlog_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        # Create phases directory and data
        phases_dir = backlog_dir / "phases"
        phases_dir.mkdir()
        
        phases_data = {
            'phases': [
                {
                    'number': 1,
                    'title': 'Discovery & Planning',
                    'description': 'Requirements gathering and feasibility',
                    'id': 'discovery-planning'
                },
                {
                    'number': 2,
                    'title': 'Design & Architecture',
                    'description': 'System design and technical planning',
                    'id': 'design-architecture'
                }
            ],
            'generated_at': '2024-01-01T00:00:00'
        }
        
        with open(phases_dir / "phases.json", 'w') as f:
            json.dump(phases_data, f)
        
        # Create phase directories
        for i in [1, 2]:
            phase_dir = phases_dir / f"phase{i}"
            phase_dir.mkdir()
            
            with open(phase_dir / "phase.json", 'w') as f:
                json.dump(phases_data['phases'][i-1], f)
        
        # Create sample epics for phase 1
        phase1_dir = phases_dir / "phase1"
        epics_data = {
            'phase_num': 1,
            'epics': [
                {
                    'title': 'User Research Epic',
                    'description': 'Conduct user research and analysis',
                    'suggestedRoles': ['researcher', 'designer']
                },
                {
                    'title': 'Requirements Definition Epic',
                    'description': 'Define and document requirements',
                    'suggestedRoles': ['analyst', 'product_owner']
                }
            ],
            'generated_at': '2024-01-01T00:00:00'
        }
        
        with open(phase1_dir / "epics.json", 'w') as f:
            json.dump(epics_data, f)
        
        # Create epic directories and sample issues
        for i, epic in enumerate(epics_data['epics'], 1):
            epic_dir = phase1_dir / f"epic{i}"
            epic_dir.mkdir()
            
            with open(epic_dir / "epic.json", 'w') as f:
                json.dump(epic, f)
            
            # Create sample issues for epic 1
            if i == 1:
                issues_data = {
                    'phase_num': 1,
                    'epic_num': 1,
                    'issues': [
                        {
                            'title': 'Conduct user interviews',
                            'priority': 'high',
                            'description': 'Interview target users'
                        },
                        {
                            'title': 'Analyze user feedback',
                            'priority': 'medium',
                            'description': 'Process interview data'
                        }
                    ],
                    'generated_at': '2024-01-01T00:00:00'
                }
                
                with open(epic_dir / "issues.json", 'w') as f:
                    json.dump(issues_data, f)
        
        yield temp_path


class TestPhasesCommand:
    """Test the phases command."""
    
    def test_phases_command_with_url(self, temp_backlog_dir):
        """Test phases command with explicit repo URL."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.milestones') as mock_milestones:
            with patch('github_backlog_generator.cli.Path') as mock_path:
                mock_path.return_value.parent.parent.parent = temp_backlog_dir
                
                result = runner.invoke(cli, [
                    'phases', 
                    'https://github.com/testowner/testrepo',
                    '--dry-run'
                ])
                
                assert result.exit_code == 0
                mock_milestones.assert_called_once()
    
    def test_phases_command_auto_detect(self, temp_backlog_dir):
        """Test phases command with auto-detection."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.milestones') as mock_milestones:
            with patch('github_backlog_generator.cli.Path') as mock_path:
                mock_path.return_value.parent.parent.parent = temp_backlog_dir
                mock_path.return_value.glob.return_value = [temp_backlog_dir / ".backlog-testowner-testrepo"]
                
                result = runner.invoke(cli, ['phases', '--dry-run'])
                
                assert result.exit_code == 0
                assert "Auto-detected repository" in result.output
                mock_milestones.assert_called_once()


class TestEpicsCommand:
    """Test the epics command."""
    
    def test_epics_command_specific_phase(self, temp_backlog_dir):
        """Test epics command for specific phase."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.generate') as mock_generate:
            with patch('github_backlog_generator.cli.Path') as mock_path:
                mock_path.return_value.parent.parent.parent = temp_backlog_dir
                mock_path.return_value.glob.return_value = [temp_backlog_dir / ".backlog-testowner-testrepo"]
                
                result = runner.invoke(cli, [
                    'epics', 
                    '--phase', '1',
                    '--dry-run'
                ])
                
                assert result.exit_code == 0
                mock_generate.assert_called_once()
    
    def test_epics_command_all_phases(self, temp_backlog_dir):
        """Test epics command for all phases."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.generate') as mock_generate:
            with patch('github_backlog_generator.cli.BacklogManager') as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.load_phases.return_value = [
                    {'number': 1, 'title': 'Phase 1'},
                    {'number': 2, 'title': 'Phase 2'}
                ]
                mock_manager_class.return_value = mock_manager
                
                with patch('github_backlog_generator.cli.Path') as mock_path:
                    mock_path.return_value.parent.parent.parent = temp_backlog_dir
                    mock_path.return_value.glob.return_value = [temp_backlog_dir / ".backlog-testowner-testrepo"]
                    
                    result = runner.invoke(cli, [
                        'epics',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert "Generating epics for all phases" in result.output
                    # Should call generate twice (once for each phase)
                    assert mock_generate.call_count == 2


class TestIssuesCommand:
    """Test the issues command."""
    
    def test_issues_command_specific_phase_and_epic(self, temp_backlog_dir):
        """Test issues command for specific phase and epic."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.generate') as mock_generate:
            with patch('github_backlog_generator.cli.Path') as mock_path:
                mock_path.return_value.parent.parent.parent = temp_backlog_dir
                mock_path.return_value.glob.return_value = [temp_backlog_dir / ".backlog-testowner-testrepo"]
                
                result = runner.invoke(cli, [
                    'issues',
                    '--phase', '1',
                    '--epic', '1',
                    '--dry-run'
                ])
                
                assert result.exit_code == 0
                mock_generate.assert_called_once()
    
    def test_issues_command_all_epics_in_phase(self, temp_backlog_dir):
        """Test issues command for all epics in a phase."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.generate') as mock_generate:
            with patch('github_backlog_generator.cli.Path') as mock_path:
                mock_path.return_value.parent.parent.parent = temp_backlog_dir
                mock_path.return_value.glob.return_value = [temp_backlog_dir / ".backlog-testowner-testrepo"]
                
                result = runner.invoke(cli, [
                    'issues',
                    '--phase', '1',
                    '--dry-run'
                ])
                
                assert result.exit_code == 0
                mock_generate.assert_called_once()
    
    def test_issues_command_all_phases(self, temp_backlog_dir):
        """Test issues command for all phases."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.generate') as mock_generate:
            with patch('github_backlog_generator.cli.BacklogManager') as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.load_phases.return_value = [
                    {'number': 1, 'title': 'Phase 1'},
                    {'number': 2, 'title': 'Phase 2'}
                ]
                mock_manager_class.return_value = mock_manager
                
                with patch('github_backlog_generator.cli.Path') as mock_path:
                    mock_path.return_value.parent.parent.parent = temp_backlog_dir
                    mock_path.return_value.glob.return_value = [temp_backlog_dir / ".backlog-testowner-testrepo"]
                    
                    result = runner.invoke(cli, [
                        'issues',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert "Generating issues for all epics across all phases" in result.output
                    # Should call generate twice (once for each phase)
                    assert mock_generate.call_count == 2


class TestStatusCommand:
    """Test the enhanced status command."""
    
    def test_status_command_table_format(self, temp_backlog_dir):
        """Test status command with table output."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.BacklogManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.base_dir.exists.return_value = True
            mock_manager.load_metadata.return_value = {
                'project_data': {'title': 'Test Project'},
                'created_at': '2024-01-01T00:00:00'
            }
            mock_manager.load_phases.return_value = [
                {'number': 1, 'title': 'Phase 1'},
                {'number': 2, 'title': 'Phase 2'}
            ]
            mock_manager.load_epics.return_value = [
                {'title': 'Epic 1'},
                {'title': 'Epic 2'}
            ]
            mock_manager.load_issues.return_value = [
                {'title': 'Issue 1', 'priority': 'high'},
                {'title': 'Issue 2', 'priority': 'medium'}
            ]
            mock_manager.get_milestone_mapping.return_value = {}
            mock_manager_class.return_value = mock_manager
            
            with patch('github_backlog_generator.cli.Path') as mock_path:
                mock_path.return_value.parent.parent.parent = temp_backlog_dir
                mock_path.return_value.glob.return_value = [temp_backlog_dir / ".backlog-testowner-testrepo"]
                
                result = runner.invoke(cli, [
                    'status',
                    '--output', 'table'
                ])
                
                assert result.exit_code == 0
                assert "Test Project" in result.output
                assert "Generation Status:" in result.output
                assert "Hierarchical Structure:" in result.output
    
    def test_status_command_json_format(self, temp_backlog_dir):
        """Test status command with JSON output."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.BacklogManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.base_dir.exists.return_value = True
            mock_manager.load_metadata.return_value = {
                'project_data': {'title': 'Test Project'},
                'created_at': '2024-01-01T00:00:00'
            }
            mock_manager.load_phases.return_value = [
                {'number': 1, 'title': 'Phase 1'}
            ]
            mock_manager.load_epics.return_value = [
                {'title': 'Epic 1'}
            ]
            mock_manager.load_issues.return_value = [
                {'title': 'Issue 1', 'priority': 'high'}
            ]
            mock_manager_class.return_value = mock_manager
            
            with patch('github_backlog_generator.cli.Path') as mock_path:
                mock_path.return_value.parent.parent.parent = temp_backlog_dir
                mock_path.return_value.glob.return_value = [temp_backlog_dir / ".backlog-testowner-testrepo"]
                
                result = runner.invoke(cli, [
                    'status',
                    '--output', 'json'
                ])
                
                assert result.exit_code == 0
                
                # Parse JSON output and verify structure
                output_data = json.loads(result.output)
                assert 'project' in output_data
                assert 'phases' in output_data
                assert output_data['project']['title'] == 'Test Project'
                assert len(output_data['phases']) == 1
                assert output_data['phases'][0]['title'] == 'Phase 1'
    
    def test_status_command_no_project_found(self, temp_backlog_dir):
        """Test status command when no project is found."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.Path') as mock_path:
            mock_path.return_value.parent.parent.parent = temp_backlog_dir
            mock_path.return_value.glob.return_value = []  # No backlog dirs found
            
            result = runner.invoke(cli, ['status'])
            
            assert result.exit_code == 1
            assert "No repository URL provided and no initialized project found" in result.output


class TestAutoDetection:
    """Test auto-detection functionality across commands."""
    
    def test_auto_detection_multiple_projects(self, temp_backlog_dir):
        """Test auto-detection when multiple project directories exist."""
        # Create second backlog directory
        second_backlog = temp_backlog_dir / ".backlog-owner2-repo2"
        second_backlog.mkdir()
        
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.milestones') as mock_milestones:
            with patch('github_backlog_generator.cli.Path') as mock_path:
                mock_path.return_value.parent.parent.parent = temp_backlog_dir
                mock_path.return_value.glob.return_value = [
                    temp_backlog_dir / ".backlog-testowner-testrepo",
                    second_backlog
                ]
                
                result = runner.invoke(cli, ['phases', '--dry-run'])
                
                assert result.exit_code == 0
                # Should pick the first one found
                assert "testowner" in result.output or "owner2" in result.output
                mock_milestones.assert_called_once()


class TestErrorHandling:
    """Test error handling for new commands."""
    
    def test_invalid_github_url(self):
        """Test handling of invalid GitHub URLs."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'phases', 
            'invalid-url',
            '--dry-run'
        ])
        
        assert result.exit_code == 1
        assert "Invalid GitHub URL" in result.output
    
    def test_no_phases_found(self, temp_backlog_dir):
        """Test handling when no phases are found."""
        runner = CliRunner()
        
        # Create empty backlog directory
        empty_backlog = temp_backlog_dir / ".backlog-empty-repo"
        empty_backlog.mkdir()
        
        with patch('github_backlog_generator.cli.BacklogManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.load_phases.return_value = None
            mock_manager_class.return_value = mock_manager
            
            result = runner.invoke(cli, [
                'epics',
                'https://github.com/empty/repo',
                '--dry-run'
            ])
            
            assert result.exit_code == 1
            assert "No phases found" in result.output


if __name__ == '__main__':
    pytest.main([__file__])