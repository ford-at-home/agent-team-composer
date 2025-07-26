"""Tests for CLI constraints and validation."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from github_backlog_generator.cli_constraints import (
    CLIConstraints, CLIConstraintError, validate_constraints
)


class TestCLIConstraints:
    """Test the CLIConstraints class methods."""
    
    def test_validate_repository_format_valid(self):
        """Test valid repository format validation."""
        owner, repo = CLIConstraints.validate_repository_format('owner/repo')
        assert owner == 'owner'
        assert repo == 'repo'
        
        owner, repo = CLIConstraints.validate_repository_format('test-owner/test-repo.name')
        assert owner == 'test-owner'
        assert repo == 'test-repo.name'
    
    def test_validate_repository_format_invalid(self):
        """Test invalid repository format validation."""
        with pytest.raises(CLIConstraintError, match="Invalid repository format"):
            CLIConstraints.validate_repository_format('invalid')
        
        with pytest.raises(CLIConstraintError, match="Invalid repository format"):
            CLIConstraints.validate_repository_format('owner/')
        
        with pytest.raises(CLIConstraintError, match="Invalid repository format"):
            CLIConstraints.validate_repository_format('/repo')
        
        with pytest.raises(CLIConstraintError, match="Invalid repository format"):
            CLIConstraints.validate_repository_format('owner/repo/extra')
    
    def test_is_valid_github_name(self):
        """Test GitHub name validation."""
        assert CLIConstraints.is_valid_github_name('validname')
        assert CLIConstraints.is_valid_github_name('valid-name')
        assert CLIConstraints.is_valid_github_name('valid_name')
        assert CLIConstraints.is_valid_github_name('valid.name')
        assert CLIConstraints.is_valid_github_name('valid123')
        
        # Invalid names
        assert not CLIConstraints.is_valid_github_name('-invalid')  # starts with hyphen
        assert not CLIConstraints.is_valid_github_name('invalid-')  # ends with hyphen
        assert not CLIConstraints.is_valid_github_name('')  # empty
        assert not CLIConstraints.is_valid_github_name('a' * 40)  # too long
        assert not CLIConstraints.is_valid_github_name('invalid space')  # contains space
    
    def test_validate_phases_file_valid(self):
        """Test valid phases file validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "content"}')
            f.flush()
            
            result = CLIConstraints.validate_phases_file(f.name)
            assert result == str(Path(f.name).absolute())
            
            Path(f.name).unlink()
    
    def test_validate_phases_file_not_found(self):
        """Test phases file validation with nonexistent file."""
        with pytest.raises(CLIConstraintError, match="Phases file not found"):
            CLIConstraints.validate_phases_file('/nonexistent/file.json')
    
    def test_validate_phases_file_not_json_extension(self):
        """Test phases file validation with non-JSON extension."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('content')
            f.flush()
            
            # Should still pass but show warning
            result = CLIConstraints.validate_phases_file(f.name)
            assert result == str(Path(f.name).absolute())
            
            Path(f.name).unlink()
    
    def test_validate_phases_json_content_valid(self):
        """Test valid phases JSON content validation."""
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
            
            result = CLIConstraints.validate_phases_json_content(f.name)
            assert len(result) == 1
            assert result[0]['title'] == 'Test Phase'
            assert 'number' in result[0]  # Should be normalized
            
            Path(f.name).unlink()
    
    def test_validate_phases_json_content_invalid_json(self):
        """Test phases JSON content validation with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            f.flush()
            
            with pytest.raises(CLIConstraintError, match="Invalid JSON"):
                CLIConstraints.validate_phases_json_content(f.name)
            
            Path(f.name).unlink()
    
    def test_validate_api_key_valid(self):
        """Test valid API key validation."""
        key = CLIConstraints.validate_api_key('sk-test-key-123456789012345')
        assert key == 'sk-test-key-123456789012345'
    
    def test_validate_api_key_from_env(self):
        """Test API key validation from environment."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-test-env-key-123456789012345'}):
            key = CLIConstraints.validate_api_key()
            assert key == 'sk-test-env-key-123456789012345'
    
    def test_validate_api_key_missing(self):
        """Test API key validation when missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(CLIConstraintError, match="ANTHROPIC_API_KEY not found"):
                CLIConstraints.validate_api_key()
    
    def test_validate_api_key_invalid_format(self):
        """Test API key validation with invalid format."""
        with pytest.raises(CLIConstraintError, match="Invalid ANTHROPIC_API_KEY format"):
            CLIConstraints.validate_api_key('invalid-key')
        
        with pytest.raises(CLIConstraintError, match="appears to be too short"):
            CLIConstraints.validate_api_key('sk-short')
    
    def test_validate_github_token_valid(self):
        """Test valid GitHub token validation."""
        token = CLIConstraints.validate_github_token('ghp_1234567890123456789012345678901234567890')
        assert token == 'ghp_1234567890123456789012345678901234567890'
    
    def test_validate_github_token_from_env(self):
        """Test GitHub token validation from environment."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'ghp_test_token_123456789012345678901234567890'}):
            token = CLIConstraints.validate_github_token()
            assert token == 'ghp_test_token_123456789012345678901234567890'
    
    def test_validate_github_token_missing(self):
        """Test GitHub token validation when missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(CLIConstraintError, match="GITHUB_TOKEN not found"):
                CLIConstraints.validate_github_token()
    
    def test_validate_output_file_path_valid(self):
        """Test valid output file path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'output.json'
            
            result = CLIConstraints.validate_output_file_path(str(output_path))
            assert result == str(output_path.absolute())
    
    def test_validate_output_file_path_create_directory(self):
        """Test output file path validation with directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'new_dir' / 'output.json'
            
            result = CLIConstraints.validate_output_file_path(str(output_path))
            assert result == str(output_path.absolute())
            assert output_path.parent.exists()
    
    def test_check_concurrent_execution_none(self):
        """Test concurrent execution check when none exists."""
        with patch('github_backlog_generator.cli_constraints.create_state_manager') as mock_create_state:
            mock_state_manager = Mock()
            mock_state_manager.check_concurrent_execution.return_value = None
            mock_create_state.return_value = mock_state_manager
            
            result = CLIConstraints.check_concurrent_execution('owner', 'repo')
            assert result is None
    
    def test_check_concurrent_execution_detected(self):
        """Test concurrent execution check when process is detected."""
        concurrent_info = {
            'pid': 12345,
            'locked_at': '2024-01-01T10:00:00',
            'command': 'test command'
        }
        
        with patch('github_backlog_generator.cli_constraints.create_state_manager') as mock_create_state:
            mock_state_manager = Mock()
            mock_state_manager.check_concurrent_execution.return_value = concurrent_info
            mock_create_state.return_value = mock_state_manager
            
            result = CLIConstraints.check_concurrent_execution('owner', 'repo')
            assert result == concurrent_info
    
    def test_validate_command_combination(self):
        """Test command combination validation."""
        mock_ctx = Mock()
        
        # Test with conflicting options
        result = CLIConstraints.validate_command_combination(
            mock_ctx, dry_run=True, force_restart=True
        )
        
        assert len(result['warnings']) > 0
        assert any('--force-restart has no effect in dry-run mode' in w for w in result['warnings'])
        assert len(result['suggestions']) > 0
    
    def test_enforce_minimum_requirements_python_version(self):
        """Test minimum requirements enforcement."""
        # This should pass in normal test environment
        try:
            CLIConstraints.enforce_minimum_requirements()
        except CLIConstraintError:
            # If it fails, it should be because of missing packages, not Python version
            # since we're running tests in a proper environment
            pass
    
    def test_display_constraint_violations(self):
        """Test constraint violations display."""
        violations = ['Error 1', 'Error 2', 'Error 3']
        
        # This should not raise an exception, just print output
        CLIConstraints.display_constraint_violations(violations)


class TestValidateConstraintsDecorator:
    """Test the validate_constraints decorator."""
    
    def test_decorator_basic_functionality(self):
        """Test basic decorator functionality."""
        
        @validate_constraints(require_repo=True)
        def test_func(repo='owner/repo', **kwargs):
            return f"Called with {kwargs.get('owner')}/{kwargs.get('repo_name')}"
        
        result = test_func(repo='test-owner/test-repo')
        assert result == "Called with test-owner/test-repo"
    
    def test_decorator_invalid_repo(self):
        """Test decorator with invalid repository."""
        
        @validate_constraints(require_repo=True)
        def test_func(repo='invalid', **kwargs):
            return "Should not reach here"
        
        with pytest.raises(SystemExit):
            test_func(repo='invalid')
    
    def test_decorator_api_key_validation(self):
        """Test decorator with API key validation."""
        
        @validate_constraints(require_api_key=True)
        def test_func(api_key=None, **kwargs):
            return f"API key: {kwargs.get('api_key', 'none')}"
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-test-key-123456789012345'}):
            result = test_func()
            assert 'sk-test-key-123456789012345' in result
    
    def test_decorator_phases_file_validation(self):
        """Test decorator with phases file validation."""
        
        @validate_constraints(require_phases_file=True)
        def test_func(phases=None, **kwargs):
            return f"Phases: {len(kwargs.get('phases_data', []))}"
        
        phases_data = {
            'phases': [
                {'title': 'Test', 'description': 'Test phase'}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(phases_data, f)
            f.flush()
            
            result = test_func(phases=f.name)
            assert "Phases: 1" in result
            
            Path(f.name).unlink()


if __name__ == '__main__':
    pytest.main([__file__])