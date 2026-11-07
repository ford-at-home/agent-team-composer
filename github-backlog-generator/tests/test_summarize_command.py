"""Tests for the enhanced summary command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from click.testing import CliRunner

from github_backlog_generator.cli import (
    cli, calculate_timing_metrics, calculate_cost_estimates,
    count_epics_for_phase, count_issues_for_phase, estimate_phase_effort,
    format_duration, output_json_summary, output_markdown_summary
)


class TestSummarizeCommand:
    """Test the enhanced summarize command."""
    
    def test_summarize_command_basic_success(self):
        """Test basic summarize command execution."""
        runner = CliRunner()
        
        # Mock the repository manager and its methods
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_repo_manager_class, \
             patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
            
            # Set up mock repository manager
            mock_manager = Mock()
            mock_repo_manager_class.return_value = mock_manager
            
            # Mock phases data
            mock_phases = [
                {'number': 1, 'title': 'Planning Phase', 'description': 'Plan the project'},
                {'number': 2, 'title': 'Design Phase', 'description': 'Design the system'}
            ]
            mock_manager.load_phases.return_value = mock_phases
            mock_manager.load_epics.return_value = [
                {'phase': 1, 'title': 'Epic 1'},
                {'phase': 2, 'title': 'Epic 2'}
            ]
            mock_manager.load_issues.return_value = [
                {'phase': 1, 'title': 'Issue 1'},
                {'phase': 1, 'title': 'Issue 2'},
                {'phase': 2, 'title': 'Issue 3'}
            ]
            
            # Mock state manager
            mock_state_manager.return_value.load_state.return_value = None
            
            result = runner.invoke(cli, ['summarize', '--repo', 'owner/repo'])
            
            assert result.exit_code == 0
            assert '📊 Enhanced Summary Report' in result.output
            assert 'Planning Phase' in result.output
            assert 'Design Phase' in result.output
            assert 'Enhanced summary generated successfully' in result.output
    
    def test_summarize_command_with_costs_and_timing(self):
        """Test summarize command with cost and timing information."""
        runner = CliRunner()
        
        execution_state = {
            'execution_id': 'test-execution-123',
            'started_at': '2024-01-01T10:00:00',
            'last_updated': '2024-01-01T10:30:00',
            'current_step': 'completed',
            'completed_steps': ['init', 'phases_loaded', 'epics_generated'],
            'execution_log': [
                {'step': 'init', 'timestamp': '2024-01-01T10:00:00'},
                {'step': 'phases_loaded', 'timestamp': '2024-01-01T10:10:00'},
                {'step': 'epics_generated', 'timestamp': '2024-01-01T10:30:00'}
            ]
        }
        
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_repo_manager_class, \
             patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
            
            mock_manager = Mock()
            mock_repo_manager_class.return_value = mock_manager
            
            mock_phases = [{'number': 1, 'title': 'Test Phase', 'description': 'Test'}]
            mock_manager.load_phases.return_value = mock_phases
            mock_manager.load_epics.return_value = []
            mock_manager.load_issues.return_value = []
            
            # Mock cost tracker
            mock_cost_tracker = Mock()
            mock_cost_tracker.get_summary.return_value = {
                'total_cost': 0.0456,
                'phase_generation': 0.0200,
                'epic_generation': 0.0256
            }
            mock_manager.cost_tracker = mock_cost_tracker
            
            # Mock state manager with execution state
            mock_state_mgr = Mock()
            mock_state_mgr.load_state.return_value = execution_state
            mock_state_manager.return_value = mock_state_mgr
            
            result = runner.invoke(cli, [
                'summarize', 
                '--repo', 'owner/repo',
                '--include-costs',
                '--include-timing'
            ])
            
            assert result.exit_code == 0
            assert 'Execution Timing' in result.output
            assert 'Cost Analysis' in result.output
            assert 'test-execution-123' in result.output or '0.0456' in result.output
    
    def test_summarize_command_json_output(self):
        """Test summarize command with JSON output."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_repo_manager_class, \
             patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
            
            mock_manager = Mock()
            mock_repo_manager_class.return_value = mock_manager
            
            mock_phases = [{'number': 1, 'title': 'Test Phase', 'description': 'Test'}]
            mock_manager.load_phases.return_value = mock_phases
            mock_manager.load_epics.return_value = []
            mock_manager.load_issues.return_value = []
            
            mock_state_manager.return_value.load_state.return_value = None
            
            result = runner.invoke(cli, [
                'summarize', 
                '--repo', 'owner/repo',
                '--output-format', 'json'
            ])
            
            assert result.exit_code == 0
            # Should contain JSON structure
            assert '"repository"' in result.output
            assert '"metrics"' in result.output
            assert '"phases_breakdown"' in result.output
    
    def test_summarize_command_markdown_output(self):
        """Test summarize command with Markdown output."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_repo_manager_class, \
             patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
            
            mock_manager = Mock()
            mock_repo_manager_class.return_value = mock_manager
            
            mock_phases = [{'number': 1, 'title': 'Test Phase', 'description': 'Test'}]
            mock_manager.load_phases.return_value = mock_phases
            mock_manager.load_epics.return_value = []
            mock_manager.load_issues.return_value = []
            
            mock_state_manager.return_value.load_state.return_value = None
            
            result = runner.invoke(cli, [
                'summarize', 
                '--repo', 'owner/repo',
                '--output-format', 'markdown'
            ])
            
            assert result.exit_code == 0
            # Should contain Markdown structure
            assert '# Project Summary:' in result.output
            assert '## 📊 Project Metrics' in result.output
            assert '| Phase | Title |' in result.output
    
    def test_summarize_command_output_to_file(self):
        """Test summarize command saving to file."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / 'summary.json'
            
            with patch('github_backlog_generator.cli.RepositoryManager') as mock_repo_manager_class, \
                 patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
                
                mock_manager = Mock()
                mock_repo_manager_class.return_value = mock_manager
                
                mock_phases = [{'number': 1, 'title': 'Test Phase', 'description': 'Test'}]
                mock_manager.load_phases.return_value = mock_phases
                mock_manager.load_epics.return_value = []
                mock_manager.load_issues.return_value = []
                
                mock_state_manager.return_value.load_state.return_value = None
                
                result = runner.invoke(cli, [
                    'summarize', 
                    '--repo', 'owner/repo',
                    '--output-format', 'json',
                    '--output-file', str(output_file)
                ])
                
                assert result.exit_code == 0
                assert output_file.exists()
                
                # Verify file content
                with open(output_file) as f:
                    data = json.load(f)
                
                assert 'repository' in data
                assert 'metrics' in data
                assert data['repository']['name'] == 'repo'
    
    def test_summarize_command_no_phases_error(self):
        """Test summarize command when no phases are found."""
        runner = CliRunner()
        
        with patch('github_backlog_generator.cli.RepositoryManager') as mock_repo_manager_class, \
             patch('github_backlog_generator.cli.create_state_manager') as mock_state_manager:
            
            mock_manager = Mock()
            mock_repo_manager_class.return_value = mock_manager
            
            # No phases found
            mock_manager.load_phases.return_value = None
            mock_state_manager.return_value.load_state.return_value = None
            
            result = runner.invoke(cli, ['summarize', '--repo', 'owner/repo'])
            
            assert result.exit_code == 1
            assert 'No phases found' in result.output
    
    def test_summarize_command_invalid_repo_format(self):
        """Test summarize command with invalid repository format."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ['summarize', '--repo', 'invalid-format'])
        
        assert result.exit_code == 1
        assert 'Error parsing repository' in result.output


class TestSummarizeHelperFunctions:
    """Test helper functions for the summarize command."""
    
    def test_calculate_timing_metrics(self):
        """Test timing metrics calculation."""
        execution_state = {
            'execution_id': 'test-123',
            'started_at': '2024-01-01T10:00:00',
            'last_updated': '2024-01-01T10:30:00',
            'current_step': 'completed',
            'completed_steps': ['init', 'phases_loaded'],
            'execution_log': [
                {'step': 'init', 'timestamp': '2024-01-01T10:00:00'},
                {'step': 'phases_loaded', 'timestamp': '2024-01-01T10:10:00'},
                {'step': 'completed', 'timestamp': '2024-01-01T10:30:00'}
            ]
        }
        
        result = calculate_timing_metrics(execution_state)
        
        assert result['execution_id'] == 'test-123'
        assert result['started_at'] == '2024-01-01T10:00:00'
        assert result['current_step'] == 'completed'
        assert len(result['completed_steps']) == 2
        assert 'total_execution_time_seconds' in result
        assert 'step_durations' in result
        assert len(result['step_durations']) == 2
    
    def test_calculate_cost_estimates_with_actual_costs(self):
        """Test cost calculation with actual cost data."""
        mock_manager = Mock()
        mock_cost_tracker = Mock()
        mock_cost_tracker.get_summary.return_value = {
            'total_cost': 0.0456,
            'phase_generation': 0.0200,
            'epic_generation': 0.0256
        }
        mock_manager.cost_tracker = mock_cost_tracker
        
        phases = [{'number': 1}, {'number': 2}]
        epics = [{'phase': 1}, {'phase': 2}]
        issues = [{'phase': 1}, {'phase': 1}, {'phase': 2}]
        
        result = calculate_cost_estimates(mock_manager, phases, epics, issues)
        
        assert result['actual_costs_available'] is True
        assert result['total_actual_cost'] == 0.0456
        assert 'actual_breakdown' in result
        assert 'estimated_breakdown' in result
    
    def test_calculate_cost_estimates_estimated_only(self):
        """Test cost calculation with estimated costs only."""
        mock_manager = Mock()
        mock_manager.cost_tracker = None
        
        phases = [{'number': 1}, {'number': 2}]
        epics = [{'phase': 1}]
        issues = [{'phase': 1}, {'phase': 2}]
        
        result = calculate_cost_estimates(mock_manager, phases, epics, issues)
        
        assert result['actual_costs_available'] is False
        assert 'total_estimated_cost' in result
        assert result['estimated_breakdown']['phase_generation'] == 0.030  # 2 phases * 0.015
        assert result['estimated_breakdown']['epic_generation'] == 0.025   # 1 epic * 0.025
        assert result['estimated_breakdown']['issue_generation'] == 0.040  # 2 issues * 0.020
        assert result['estimated_breakdown']['preprocessing'] == 0.010     # 1 preprocessing * 0.010
    
    def test_count_epics_for_phase(self):
        """Test counting epics for a specific phase."""
        epics = [
            {'phase': 1, 'title': 'Epic 1'},
            {'phase': 1, 'title': 'Epic 2'},
            {'phase': 2, 'title': 'Epic 3'}
        ]
        
        assert count_epics_for_phase(epics, 1) == 2
        assert count_epics_for_phase(epics, 2) == 1
        assert count_epics_for_phase(epics, 3) == 0
        assert count_epics_for_phase(None, 1) == 0
    
    def test_count_issues_for_phase(self):
        """Test counting issues for a specific phase."""
        issues = [
            {'phase': 1, 'title': 'Issue 1'},
            {'phase': 1, 'title': 'Issue 2'},
            {'phase': 2, 'title': 'Issue 3'},
            {'phase': 2, 'title': 'Issue 4'}
        ]
        
        assert count_issues_for_phase(issues, 1) == 2
        assert count_issues_for_phase(issues, 2) == 2
        assert count_issues_for_phase(issues, 3) == 0
        assert count_issues_for_phase(None, 1) == 0
    
    def test_estimate_phase_effort(self):
        """Test phase effort estimation."""
        phase = {'number': 1, 'title': 'Test Phase'}
        epics = [{'phase': 1}]
        
        # Small effort (1-5 issues)
        issues = [{'phase': 1}, {'phase': 1}, {'phase': 1}]
        assert estimate_phase_effort(phase, epics, issues) == "Small (1-2 weeks)"
        
        # Medium effort (6-15 issues)
        issues = [{'phase': 1} for _ in range(10)]
        assert estimate_phase_effort(phase, epics, issues) == "Medium (3-6 weeks)"
        
        # Large effort (16-30 issues)
        issues = [{'phase': 1} for _ in range(25)]
        assert estimate_phase_effort(phase, epics, issues) == "Large (6-12 weeks)"
        
        # Extra large effort (30+ issues)
        issues = [{'phase': 1} for _ in range(35)]
        assert estimate_phase_effort(phase, epics, issues) == "Extra Large (12+ weeks)"
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(30.5) == "30.5s"
        assert format_duration(90) == "1.5m"
        assert format_duration(3660) == "1.0h"
        assert format_duration(7320) == "2.0h"
        assert format_duration(125.7) == "2.1m"
    
    def test_output_json_summary(self):
        """Test JSON summary output."""
        summary_data = {
            'repository': {'owner': 'test', 'name': 'repo'},
            'metrics': {'phases': 2, 'epics': 1, 'issues': 3}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_json_summary(summary_data, f.name)
            
            # Verify file was created and contains valid JSON
            with open(f.name) as read_f:
                loaded_data = json.load(read_f)
            
            assert loaded_data == summary_data
            Path(f.name).unlink()
    
    def test_output_markdown_summary(self):
        """Test Markdown summary output."""
        summary_data = {
            'repository': {'owner': 'test', 'name': 'repo', 'url': 'https://github.com/test/repo'},
            'metrics': {'phases': 2, 'epics': 1, 'issues': 3, 'items_per_phase': 1.5, 'epics_per_phase': 0.5},
            'phases_breakdown': [
                {'number': 1, 'title': 'Phase 1', 'epics_count': 1, 'issues_count': 2, 'estimated_effort': 'Small'}
            ],
            'generation_info': {'generated_at': '2024-01-01T10:00:00', 'tool_version': '2.0.0'}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            output_markdown_summary(summary_data, f.name)
            
            # Verify file was created and contains Markdown content
            content = Path(f.name).read_text()
            
            assert '# Project Summary: test/repo' in content
            assert '## 📊 Project Metrics' in content
            assert '- **Total Phases:** 2' in content
            assert '| Phase | Title | Epics | Issues | Est. Effort |' in content
            assert '| 1 | Phase 1 | 1 | 2 | Small |' in content
            
            Path(f.name).unlink()


if __name__ == '__main__':
    pytest.main([__file__])