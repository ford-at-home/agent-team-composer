"""Tests for phase preprocessing via LLM."""

import json
from unittest.mock import Mock, patch

import pytest

from github_backlog_generator.phase_preprocessor import (
    PhasePreprocessor, preprocess_phases_with_llm
)


class TestPhasePreprocessor:
    """Test the PhasePreprocessor class."""
    
    def test_should_preprocess_phase(self):
        """Test phase preprocessing eligibility."""
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        assert not preprocessor.should_preprocess_phase(1)
        assert preprocessor.should_preprocess_phase(2)
        assert preprocessor.should_preprocess_phase(3)
    
    def test_build_preprocessing_prompt_basic(self):
        """Test building basic preprocessing prompt."""
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        current_phase = {
            'number': 2,
            'title': 'Design Phase',
            'description': 'Design the system',
            'suggestedRoles': ['designer', 'architect']
        }
        
        prior_phases = [
            {
                'number': 1,
                'title': 'Planning Phase',
                'description': 'Plan the project',
                'suggestedRoles': ['analyst']
            }
        ]
        
        prompt = preprocessor.build_preprocessing_prompt(current_phase, prior_phases)
        
        assert "Phase Preprocessing Analysis" in prompt
        assert "Planning Phase" in prompt
        assert "Design Phase" in prompt
        assert "Based on the prior phases" in prompt
        assert "needs_modification" in prompt
    
    def test_build_preprocessing_prompt_with_context(self):
        """Test building prompt with project context."""
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        current_phase = {
            'number': 2,
            'title': 'Design Phase',
            'description': 'Design the system',
            'suggestedRoles': ['designer']
        }
        
        prior_phases = [
            {
                'number': 1,
                'title': 'Planning Phase',
                'description': 'Plan the project',
                'suggestedRoles': ['analyst']
            }
        ]
        
        project_context = {
            'title': 'Test Project',
            'domain': 'web-development',
            'complexity': 'high'
        }
        
        prior_epics = [
            {'title': 'Epic 1'},
            {'title': 'Epic 2'}
        ]
        
        prior_issues = [
            {'title': 'Issue 1'},
            {'title': 'Issue 2'}
        ]
        
        prompt = preprocessor.build_preprocessing_prompt(
            current_phase, prior_phases, project_context, prior_epics, prior_issues
        )
        
        assert "Test Project" in prompt
        assert "web-development" in prompt
        assert "Epic 1" in prompt
        assert "Issue 1" in prompt
    
    @patch('anthropic.Anthropic')
    def test_call_llm_for_preprocessing_success(self, mock_anthropic_class):
        """Test successful LLM call for preprocessing."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock the response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''
        Looking at this phase, I think some modifications would be helpful.
        
        {
          "needs_modification": true,
          "reasoning": "The phase should be updated based on prior work",
          "modifications": {
            "description": "Updated description based on planning phase results",
            "suggestedRoles": ["designer", "architect", "developer"]
          }
        }
        '''
        
        mock_client.messages.create.return_value = mock_response
        
        preprocessor = PhasePreprocessor(api_key="test-key")
        result = preprocessor.call_llm_for_preprocessing("test prompt")
        
        assert result['needs_modification'] is True
        assert 'reasoning' in result
        assert 'modifications' in result
        assert 'description' in result['modifications']
        
        # Verify the API was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['model'] == 'claude-3-5-sonnet-20241022'
        assert call_args[1]['temperature'] == 0.1
        assert call_args[1]['messages'][0]['content'] == "test prompt"
    
    @patch('anthropic.Anthropic')
    def test_call_llm_for_preprocessing_invalid_json(self, mock_anthropic_class):
        """Test LLM call with invalid JSON response."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is not valid JSON"
        
        mock_client.messages.create.return_value = mock_response
        
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        with pytest.raises(ValueError, match="No JSON found"):
            preprocessor.call_llm_for_preprocessing("test prompt")
    
    @patch('anthropic.Anthropic')
    def test_preprocess_phase_no_modification_needed(self, mock_anthropic_class):
        """Test preprocessing when no modification is needed."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock response indicating no changes needed
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''
        {
          "needs_modification": false,
          "reasoning": "The phase is already well-defined for this project context"
        }
        '''
        
        mock_client.messages.create.return_value = mock_response
        
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        current_phase = {
            'number': 2,
            'title': 'Design Phase',
            'description': 'Design the system',
            'suggestedRoles': ['designer']
        }
        
        prior_phases = [
            {
                'number': 1,
                'title': 'Planning Phase',
                'description': 'Plan the project',
                'suggestedRoles': ['analyst']
            }
        ]
        
        result = preprocessor.preprocess_phase(current_phase, prior_phases)
        
        # Should return the original phase unchanged
        assert result == current_phase
        assert 'preprocessing' not in result
    
    @patch('anthropic.Anthropic')
    def test_preprocess_phase_with_modifications(self, mock_anthropic_class):
        """Test preprocessing when modifications are needed."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock response with modifications
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''
        {
          "needs_modification": true,
          "reasoning": "Based on the planning phase, we need to adjust the scope",
          "modifications": {
            "description": "Design the system based on requirements from planning phase",
            "suggestedRoles": ["designer", "architect", "developer"]
          }
        }
        '''
        
        mock_client.messages.create.return_value = mock_response
        
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        current_phase = {
            'number': 2,
            'title': 'Design Phase',
            'description': 'Design the system',
            'suggestedRoles': ['designer']
        }
        
        prior_phases = [
            {
                'number': 1,
                'title': 'Planning Phase',
                'description': 'Plan the project',
                'suggestedRoles': ['analyst']
            }
        ]
        
        result = preprocessor.preprocess_phase(current_phase, prior_phases)
        
        # Should return the modified phase
        assert result['title'] == 'Design Phase'  # Unchanged
        assert result['description'] == 'Design the system based on requirements from planning phase'
        assert result['suggestedRoles'] == ['designer', 'architect', 'developer']
        
        # Should have preprocessing metadata
        assert 'preprocessing' in result
        assert result['preprocessing']['reasoning'] == 'Based on the planning phase, we need to adjust the scope'
        assert 'original_phase' in result['preprocessing']
    
    def test_preprocess_phase_first_phase_skipped(self):
        """Test that first phase is not preprocessed."""
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        first_phase = {
            'number': 1,
            'title': 'First Phase',
            'description': 'The first phase',
            'suggestedRoles': ['analyst']
        }
        
        result = preprocessor.preprocess_phase(first_phase, [])
        
        # Should return the phase unchanged without calling LLM
        assert result == first_phase
    
    @patch('anthropic.Anthropic')
    def test_preprocess_phase_error_handling(self, mock_anthropic_class):
        """Test error handling during preprocessing."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock API call failure
        mock_client.messages.create.side_effect = Exception("API call failed")
        
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        current_phase = {
            'number': 2,
            'title': 'Design Phase',
            'description': 'Design the system',
            'suggestedRoles': ['designer']
        }
        
        prior_phases = [
            {
                'number': 1,
                'title': 'Planning Phase',
                'description': 'Plan the project',
                'suggestedRoles': ['analyst']
            }
        ]
        
        # Should handle error gracefully and return original phase
        result = preprocessor.preprocess_phase(current_phase, prior_phases)
        assert result == current_phase
    
    @patch('anthropic.Anthropic')
    def test_preprocess_all_phases(self, mock_anthropic_class):
        """Test preprocessing all phases in sequence."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock response for phase 2
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''
        {
          "needs_modification": true,
          "reasoning": "Adjusting based on prior phase",
          "modifications": {
            "description": "Updated description for phase 2"
          }
        }
        '''
        
        mock_client.messages.create.return_value = mock_response
        
        preprocessor = PhasePreprocessor(api_key="test-key")
        
        phases = [
            {
                'number': 1,
                'title': 'Phase 1',
                'description': 'First phase',
                'suggestedRoles': ['analyst']
            },
            {
                'number': 2,
                'title': 'Phase 2',
                'description': 'Second phase',
                'suggestedRoles': ['designer']
            }
        ]
        
        result = preprocessor.preprocess_all_phases(phases)
        
        assert len(result) == 2
        # First phase unchanged
        assert result[0] == phases[0]
        # Second phase modified
        assert result[1]['description'] == 'Updated description for phase 2'
        assert 'preprocessing' in result[1]
    
    @patch('github_backlog_generator.phase_preprocessor.PhasePreprocessor')
    def test_preprocess_phases_with_llm_convenience_function(self, mock_preprocessor_class):
        """Test the convenience function for preprocessing phases."""
        mock_preprocessor = Mock()
        mock_preprocessor_class.return_value = mock_preprocessor
        
        phases = [{'number': 1, 'title': 'Test'}]
        processed_phases = [{'number': 1, 'title': 'Test', 'processed': True}]
        
        mock_preprocessor.preprocess_all_phases.return_value = processed_phases
        
        result = preprocess_phases_with_llm(
            phases=phases,
            api_key="test-key",
            project_context={'title': 'Test Project'}
        )
        
        assert result == processed_phases
        mock_preprocessor_class.assert_called_once_with(api_key="test-key", model='claude-3-5-sonnet-20241022')
        mock_preprocessor.preprocess_all_phases.assert_called_once_with(phases, {'title': 'Test Project'})


if __name__ == '__main__':
    pytest.main([__file__])