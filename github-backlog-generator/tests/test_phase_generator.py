"""Unit tests for phase generator module."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from github_backlog_generator.phase_generator import PhaseGenerator, Phase, PhasesResponse


class TestPhaseGenerator:
    """Test cases for PhaseGenerator class."""
    
    @pytest.fixture
    def mock_anthropic(self):
        """Create a mock Anthropic client."""
        with patch('github_backlog_generator.phase_generator.Anthropic') as mock:
            yield mock
    
    @pytest.fixture
    def phase_generator(self, mock_anthropic):
        """Create a PhaseGenerator instance with mocked Anthropic."""
        return PhaseGenerator("test-api-key")
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            'title': 'Test Project',
            'description': 'A test project for unit testing',
            'domain': 'web-application',
            'features': ['user-auth', 'dashboard', 'api'],
            'techStack': ['Python', 'React', 'PostgreSQL'],
            'rawContent': '# Test Project\nA sample README content'
        }
    
    @pytest.fixture
    def valid_ai_response(self):
        """Valid AI response with phases."""
        return {
            "phases": [
                {
                    "id": "research-discovery",
                    "title": "📚 Research & Discovery - Test Project",
                    "description": "Analyze requirements for Test Project auth system",
                    "suggestedRoles": ["Product Owner", "UX Researcher"]
                },
                {
                    "id": "planning-design",
                    "title": "🧐 Planning & Design - System Architecture",
                    "description": "Design PostgreSQL schema and React components",
                    "suggestedRoles": ["System Architect", "Tech Lead"]
                }
            ]
        }
    
    def test_init(self, mock_anthropic):
        """Test PhaseGenerator initialization."""
        generator = PhaseGenerator("test-key")
        assert generator.anthropic is not None
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    def test_build_prompt(self, phase_generator, sample_project_data):
        """Test prompt building includes all required elements."""
        prompt = phase_generator._build_prompt(sample_project_data)
        
        # Check for mental models section
        assert "Double Diamond" in prompt
        assert "Systems Thinking" in prompt
        assert "Critical Path Analysis" in prompt
        
        # Check for cognitive biases section
        assert "Planning Fallacy" in prompt
        assert "Recency Bias" in prompt
        assert "Optimism Bias" in prompt
        
        # Check for project context
        assert "Test Project" in prompt
        assert "Python" in prompt
        assert "React" in prompt
        assert "PostgreSQL" in prompt
        
        # Check for meta-strategy validation
        assert "META-STRATEGY VALIDATION" in prompt
        assert "First Principles" in prompt
        assert "Traceability" in prompt
    
    def test_generate_phases_success(self, phase_generator, sample_project_data, valid_ai_response):
        """Test successful phase generation."""
        # Mock the Anthropic response
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(valid_ai_response))]
        phase_generator.anthropic.messages.create.return_value = mock_message
        
        # Generate phases
        phases = phase_generator.generate_phases(sample_project_data)
        
        # Verify the result
        assert len(phases) == 2
        assert phases[0]['id'] == 'research-discovery'
        assert phases[0]['title'] == '📚 Research & Discovery - Test Project'
        assert 'dueDate' in phases[0]  # Due date should be added
        
        # Verify API was called correctly
        phase_generator.anthropic.messages.create.assert_called_once()
        call_args = phase_generator.anthropic.messages.create.call_args
        assert call_args.kwargs['model'] == 'claude-3-sonnet-20240229'
        assert call_args.kwargs['max_tokens'] == 4000
    
    def test_generate_phases_with_custom_phases(self, phase_generator):
        """Test generation includes custom phases for specific domains."""
        ai_project_data = {
            'title': 'AI Assistant',
            'domain': 'artificial-intelligence',
            'features': ['llm-integration', 'prompt-engineering'],
            'techStack': ['Python', 'LangChain', 'OpenAI'],
            'rawContent': 'An AI-powered assistant'
        }
        
        prompt = phase_generator._build_prompt(ai_project_data)
        
        # Should mention AI-specific custom phases
        assert "AI Prompt Tuning" in prompt
        assert "artificial-intelligence" in prompt
    
    def test_extract_phases_from_json(self, phase_generator, valid_ai_response):
        """Test extracting phases from various JSON formats."""
        # Test direct JSON
        phases = phase_generator._extract_phases(json.dumps(valid_ai_response))
        assert len(phases) == 2
        assert phases[0]['id'] == 'research-discovery'
        
        # Test JSON in code block
        json_in_code_block = f"```json\n{json.dumps(valid_ai_response)}\n```"
        phases = phase_generator._extract_phases(json_in_code_block)
        assert len(phases) == 2
        
        # Test JSON with extra text
        json_with_text = f"Here are the phases:\n{json.dumps(valid_ai_response)}\nEnd of phases"
        phases = phase_generator._extract_phases(json_with_text)
        assert len(phases) == 2
    
    def test_extract_phases_invalid_json(self, phase_generator):
        """Test handling of invalid JSON responses."""
        with pytest.raises(ValueError, match="No JSON found"):
            phase_generator._extract_phases("This is not JSON")
        
        with pytest.raises(ValueError, match="Failed to parse"):
            phase_generator._extract_phases('{"invalid": "structure"}')
    
    def test_calculate_due_dates(self, phase_generator):
        """Test due date calculation for phases."""
        phases = [
            {"id": "phase1", "title": "Phase 1"},
            {"id": "phase2", "title": "Phase 2"},
            {"id": "phase3", "title": "Phase 3"}
        ]
        
        start_date = datetime(2024, 1, 1)
        phases_with_dates = phase_generator._calculate_due_dates(phases, start_date)
        
        # Check that due dates are properly spaced
        assert len(phases_with_dates) == 3
        
        date1 = datetime.fromisoformat(phases_with_dates[0]['dueDate'].replace('Z', '+00:00'))
        date2 = datetime.fromisoformat(phases_with_dates[1]['dueDate'].replace('Z', '+00:00'))
        date3 = datetime.fromisoformat(phases_with_dates[2]['dueDate'].replace('Z', '+00:00'))
        
        # Each phase should be 14 days apart
        assert (date2 - date1).days == 14
        assert (date3 - date2).days == 14
    
    def test_calculate_due_dates_default_start(self, phase_generator):
        """Test due date calculation with default start date."""
        phases = [{"id": "phase1", "title": "Phase 1"}]
        
        # Should use current date as default
        with patch('github_backlog_generator.phase_generator.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            phases_with_dates = phase_generator._calculate_due_dates(phases)
            
            assert len(phases_with_dates) == 1
            due_date = datetime.fromisoformat(phases_with_dates[0]['dueDate'].replace('Z', '+00:00'))
            assert (due_date - mock_now).days == 14
    
    def test_generate_phases_api_error(self, phase_generator, sample_project_data):
        """Test handling of API errors."""
        phase_generator.anthropic.messages.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="Failed to generate phases: API Error"):
            phase_generator.generate_phases(sample_project_data)
    
    def test_phase_model_validation(self):
        """Test Phase model validation."""
        # Valid phase
        phase = Phase(
            id="test-phase",
            title="Test Phase",
            description="A test phase",
            suggestedRoles=["Developer", "Tester"]
        )
        assert phase.id == "test-phase"
        assert len(phase.suggestedRoles) == 2
        
        # Invalid phase - missing required fields
        with pytest.raises(ValueError):
            Phase(id="test", title="Test")  # Missing description and suggestedRoles
    
    def test_phases_response_validation(self):
        """Test PhasesResponse model validation."""
        # Valid response
        response = PhasesResponse(phases=[
            Phase(
                id="phase1",
                title="Phase 1",
                description="Description 1",
                suggestedRoles=["Role1"]
            )
        ])
        assert len(response.phases) == 1
        
        # Invalid response - empty phases
        with pytest.raises(ValueError):
            PhasesResponse(phases="not a list")
    
    @pytest.mark.parametrize("phase_count,domain", [
        (6, "web-application"),  # Standard web app - 6 core phases
        (7, "artificial-intelligence"),  # AI project - should add custom phases
        (7, "data-analytics"),  # Data project - should add custom phases
    ])
    def test_phase_count_by_domain(self, phase_generator, phase_count, domain):
        """Test that different domains generate appropriate number of phases."""
        project_data = {
            'title': f'Test {domain} Project',
            'domain': domain,
            'features': ['feature1', 'feature2'],
            'techStack': ['Python'],
            'rawContent': f'A {domain} project'
        }
        
        # Create a mock response with the expected number of phases
        phases_list = []
        for i in range(phase_count):
            phases_list.append({
                "id": f"phase-{i+1}",
                "title": f"Phase {i+1}",
                "description": f"Description for phase {i+1}",
                "suggestedRoles": ["Role1", "Role2"]
            })
        
        mock_response = {"phases": phases_list}
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(mock_response))]
        phase_generator.anthropic.messages.create.return_value = mock_message
        
        phases = phase_generator.generate_phases(project_data)
        assert len(phases) >= 6  # At least 6 core phases
        
        # Check that AI projects get prompt tuning phase
        if domain == "artificial-intelligence":
            prompt = phase_generator._build_prompt(project_data)
            assert "AI Prompt Tuning" in prompt