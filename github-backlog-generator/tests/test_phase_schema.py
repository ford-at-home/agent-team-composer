"""Tests for phase JSON schema validation and handling."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from github_backlog_generator.phase_schema import (
    PhaseSchema, PhaseSchemaError, load_phases_from_file
)
from github_backlog_generator.cli import cli


class TestPhaseSchema:
    """Test the PhaseSchema validation and processing."""
    
    def test_validate_valid_phase(self):
        """Test validation of a valid phase."""
        phase = {
            'title': 'Test Phase',
            'description': 'A test phase',
            'order': 1,
            'suggestedRoles': ['developer', 'tester']
        }
        
        errors = PhaseSchema.validate_phase(phase, 1)
        assert errors == []
    
    def test_validate_phase_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        phase = {'title': 'Test Phase'}  # Missing description
        
        errors = PhaseSchema.validate_phase(phase, 1)
        assert len(errors) == 1
        assert "Missing required field 'description'" in errors[0]
    
    def test_validate_phase_wrong_types(self):
        """Test validation fails for wrong field types."""
        phase = {
            'title': 123,  # Should be string
            'description': 'Valid description',
            'suggestedRoles': 'not a list',  # Should be list
            'order': 'not an int'  # Should be int
        }
        
        errors = PhaseSchema.validate_phase(phase, 1)
        assert len(errors) == 3
        assert any("'title' must be a string" in error for error in errors)
        assert any("'suggestedRoles' must be a list" in error for error in errors)
        assert any("'order' must be an integer" in error for error in errors)
    
    def test_validate_phases_json_valid(self):
        """Test validation of valid phases JSON."""
        phases_data = {
            'phases': [
                {
                    'title': 'Phase 1',
                    'description': 'First phase',
                    'order': 1
                },
                {
                    'title': 'Phase 2', 
                    'description': 'Second phase',
                    'order': 2
                }
            ]
        }
        
        errors = PhaseSchema.validate_phases_json(phases_data)
        assert errors == []
    
    def test_validate_phases_json_invalid_structure(self):
        """Test validation fails for invalid JSON structure."""
        # Missing phases key
        phases_data = {'invalid': 'structure'}
        errors = PhaseSchema.validate_phases_json(phases_data)
        assert len(errors) == 1
        assert "Missing 'phases' key" in errors[0]
        
        # Phases not a list
        phases_data = {'phases': 'not a list'}
        errors = PhaseSchema.validate_phases_json(phases_data)
        assert len(errors) == 1
        assert "'phases' must be a list" in errors[0]
        
        # Empty phases
        phases_data = {'phases': []}
        errors = PhaseSchema.validate_phases_json(phases_data)
        assert len(errors) == 1
        assert "'phases' list cannot be empty" in errors[0]
    
    def test_validate_phases_json_duplicate_titles(self):
        """Test validation fails for duplicate phase titles."""
        phases_data = {
            'phases': [
                {'title': 'Duplicate', 'description': 'First'},
                {'title': 'Duplicate', 'description': 'Second'}
            ]
        }
        
        errors = PhaseSchema.validate_phases_json(phases_data)
        assert len(errors) == 1
        assert "Duplicate title 'Duplicate'" in errors[0]
    
    def test_load_and_validate_nonexistent_file(self):
        """Test loading nonexistent file raises error."""
        with pytest.raises(PhaseSchemaError, match="Phases file not found"):
            PhaseSchema.load_and_validate('/nonexistent/file.json')
    
    def test_load_and_validate_invalid_json(self):
        """Test loading invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            f.flush()
            
            with pytest.raises(PhaseSchemaError, match="Invalid JSON"):
                PhaseSchema.load_and_validate(f.name)
            
            Path(f.name).unlink()
    
    def test_load_and_validate_valid_file(self):
        """Test loading valid phases file."""
        phases_data = {
            'phases': [
                {
                    'title': 'Test Phase',
                    'description': 'A test phase',
                    'order': 1
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f)
            f.flush()
            
            result = PhaseSchema.load_and_validate(f.name)
            assert result == phases_data
            
            Path(f.name).unlink()
    
    def test_normalize_phases(self):
        """Test phase normalization."""
        phases_data = {
            'phases': [
                {
                    'title': 'Second Phase',
                    'description': 'Should be ordered second',
                    'order': 2
                },
                {
                    'title': 'First Phase',
                    'description': 'Should be ordered first',
                    'order': 1
                }
            ]
        }
        
        normalized = PhaseSchema.normalize_phases(phases_data)
        
        assert len(normalized) == 2
        assert normalized[0]['title'] == 'First Phase'
        assert normalized[0]['number'] == 1
        assert normalized[1]['title'] == 'Second Phase'
        assert normalized[1]['number'] == 2
        
        # Check that IDs are generated
        assert 'id' in normalized[0]
        assert 'id' in normalized[1]
        
        # Check that due dates are generated
        assert 'dueDate' in normalized[0]
        assert 'dueDate' in normalized[1]
    
    def test_create_sample_phases_json(self):
        """Test creating sample phases JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_phases.json'
            
            created_path = PhaseSchema.create_sample_phases_json(str(output_path))
            
            assert Path(created_path).exists()
            
            # Validate the created file
            data = PhaseSchema.load_and_validate(created_path)
            assert 'phases' in data
            assert len(data['phases']) == 8  # Default 8 phases
            assert 'metadata' in data


class TestPhaseSchemaIntegration:
    """Test integration with CLI commands."""
    
    def test_load_phases_from_file_success(self):
        """Test successful loading of phases from file."""
        phases_data = {
            'phases': [
                {
                    'title': 'Test Phase',
                    'description': 'A test phase',
                    'order': 1,
                    'suggestedRoles': ['developer']
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f)
            f.flush()
            
            result = load_phases_from_file(f.name)
            
            assert len(result) == 1
            assert result[0]['title'] == 'Test Phase'
            assert result[0]['number'] == 1
            
            Path(f.name).unlink()
    
    def test_load_phases_from_file_validation_error(self):
        """Test loading phases with validation errors."""
        phases_data = {
            'phases': [
                {
                    'title': 'Test Phase'
                    # Missing description
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f)
            f.flush()
            
            with pytest.raises(PhaseSchemaError):
                load_phases_from_file(f.name)
            
            Path(f.name).unlink()


class TestCLICommands:
    """Test new CLI commands for phase handling."""
    
    def test_generate_phases_command_show(self):
        """Test generate-phases command with --show flag."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ['generate-phases', '--show'])
        
        assert result.exit_code == 0
        assert 'Sample phases.json content:' in result.output
        assert '"phases"' in result.output
    
    def test_generate_phases_command_create_file(self):
        """Test generate-phases command creates file."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_phases.json'
            
            result = runner.invoke(cli, ['generate-phases', '--output', str(output_path)])
            
            assert result.exit_code == 0
            assert output_path.exists()
            assert 'Sample phases.json created' in result.output
            
            # Verify the file is valid
            data = json.loads(output_path.read_text())
            assert 'phases' in data
            assert len(data['phases']) == 8
    
    def test_run_command_missing_phases_file(self):
        """Test run command with missing phases file."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'run',
            '--phases', '/nonexistent/phases.json',
            '--repo', 'owner/repo'
        ])
        
        assert result.exit_code == 2  # Click validation error
        assert 'does not exist' in result.output
    
    def test_run_command_invalid_repo_format(self):
        """Test run command with invalid repository format."""
        runner = CliRunner()
        
        # Create a valid phases file
        phases_data = {
            'phases': [
                {'title': 'Test', 'description': 'Test phase'}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f)
            f.flush()
            
            result = runner.invoke(cli, [
                'run',
                '--phases', f.name,
                '--repo', 'invalid-repo-format'
            ])
            
            assert result.exit_code == 1
            assert 'Error parsing repository' in result.output
            
            Path(f.name).unlink()
    
    def test_run_command_missing_api_key(self):
        """Test run command without API key."""
        runner = CliRunner()
        
        # Create a valid phases file
        phases_data = {
            'phases': [
                {'title': 'Test', 'description': 'Test phase'}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f)
            f.flush()
            
            # Clear environment variables
            with patch.dict('os.environ', {}, clear=True):
                result = runner.invoke(cli, [
                    'run',
                    '--phases', f.name,
                    '--repo', 'owner/repo'
                ])
                
                assert result.exit_code == 1
                assert 'ANTHROPIC_API_KEY not found' in result.output
            
            Path(f.name).unlink()
    
    def test_run_command_dry_run_success(self):
        """Test run command in dry-run mode."""
        runner = CliRunner()
        
        # Create a valid phases file
        phases_data = {
            'phases': [
                {
                    'title': 'Test Phase',
                    'description': 'A test phase for dry run',
                    'order': 1,
                    'suggestedRoles': ['developer']
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f)
            f.flush()
            
            # Mock the CLI command invocations
            with patch('github_backlog_generator.cli.phases') as mock_phases, \
                 patch('github_backlog_generator.cli.epics') as mock_epics, \
                 patch('github_backlog_generator.cli.issues') as mock_issues, \
                 patch('github_backlog_generator.cli.enhanced_status') as mock_status:
                
                # Set environment variable for API key
                with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
                    result = runner.invoke(cli, [
                        'run',
                        '--phases', f.name,
                        '--repo', 'owner/repo',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert 'GitHub Backlog Generator - Full Workflow' in result.output
                    assert 'Test Phase' in result.output
                    assert 'DRY RUN MODE' in result.output
                    assert 'Workflow completed successfully' in result.output
                    
                    # Verify sub-commands were called
                    mock_phases.assert_called_once()
                    mock_epics.assert_called_once()
                    mock_issues.assert_called_once()
                    mock_status.assert_called_once()
            
            Path(f.name).unlink()


if __name__ == '__main__':
    pytest.main([__file__])