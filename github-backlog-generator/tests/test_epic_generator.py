"""Unit tests for epic generator module."""

import json
import pytest
from unittest.mock import Mock, patch

from github_backlog_generator.epic_generator import EpicGenerator, Epic, Task, PhaseEpics


class TestEpicGenerator:
    """Test cases for EpicGenerator class."""
    
    @pytest.fixture
    def mock_anthropic(self):
        """Create a mock Anthropic client."""
        with patch('github_backlog_generator.epic_generator.Anthropic') as mock:
            yield mock
    
    @pytest.fixture
    def epic_generator(self, mock_anthropic):
        """Create an EpicGenerator instance with mocked Anthropic."""
        return EpicGenerator("test-api-key")
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            'title': 'E-commerce Platform',
            'description': 'A modern e-commerce platform with AI recommendations',
            'domain': 'e-commerce',
            'features': ['shopping-cart', 'payment', 'recommendations'],
            'techStack': ['Django', 'React', 'PostgreSQL', 'Redis']
        }
    
    @pytest.fixture
    def valid_epic_response(self):
        """Valid AI response with epics."""
        return {
            "phaseId": "phase-1",
            "phaseTitle": "Discovery & Planning",
            "epics": [
                {
                    "title": "User Research and Market Analysis",
                    "description": "Conduct comprehensive user research to understand shopping behaviors and pain points in the e-commerce space.",
                    "suggestedRoles": ["UX Researcher", "Product Manager"],
                    "tasks": [
                        {
                            "title": "Conduct user interviews with target demographics",
                            "description": "Interview 20+ potential users about their online shopping habits",
                            "suggestedRole": "UX Researcher"
                        },
                        {
                            "title": "Analyze competitor platforms",
                            "description": "Deep dive into top 5 competitors' features and UX patterns",
                            "suggestedRole": "Product Manager"
                        }
                    ]
                },
                {
                    "title": "Technical Architecture Planning",
                    "description": "Design the scalable architecture for handling high-traffic e-commerce operations with AI integration.",
                    "suggestedRoles": ["System Architect", "DevOps Engineer"],
                    "tasks": [
                        {
                            "title": "Design microservices architecture",
                            "description": "Create architecture diagrams for cart, payment, and recommendation services",
                            "suggestedRole": "System Architect"
                        }
                    ]
                }
            ]
        }
    
    def test_init(self, mock_anthropic):
        """Test EpicGenerator initialization."""
        generator = EpicGenerator("test-key")
        assert generator.anthropic is not None
        assert generator.max_retries == 3
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    def test_build_prompt(self, epic_generator, sample_project_data):
        """Test prompt building includes all mental models and bias warnings."""
        prompt = epic_generator._build_prompt(
            phase_number=1,
            phase_name="Discovery & Planning",
            phase_description="Initial research and planning phase",
            project_data=sample_project_data
        )
        
        # Check for mental models section
        assert "Jobs To Be Done (JTBD)" in prompt
        assert "MoSCoW Prioritization" in prompt
        assert "Divide and Conquer" in prompt
        assert "SPADE Framework" in prompt
        
        # Check for cognitive biases section
        assert "Feature Creep" in prompt
        assert "Ambiguity Effect" in prompt
        assert "Confirmation Bias" in prompt
        
        # Check for project context
        assert "E-commerce Platform" in prompt
        assert "Django" in prompt
        assert "shopping-cart" in prompt
        
        # Check for meta-strategy validation
        assert "META-STRATEGY VALIDATION" in prompt
        assert "What job is the user trying to get done?" in prompt
        assert "Must-have for MVP" in prompt
    
    def test_generate_epics_success(self, epic_generator, sample_project_data, valid_epic_response):
        """Test successful epic generation."""
        # Mock the Anthropic response
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(valid_epic_response))]
        epic_generator.anthropic.messages.create.return_value = mock_message
        
        # Generate epics
        epics = epic_generator.generate_epics_for_phase(
            phase_number=1,
            phase_name="Discovery & Planning",
            phase_description="Initial phase",
            project_data=sample_project_data
        )
        
        # Verify the result
        assert len(epics) == 2
        assert epics[0]['title'] == "User Research and Market Analysis"
        assert len(epics[0]['tasks']) == 2
        assert epics[0]['tasks'][0]['suggestedRole'] == "UX Researcher"
        
        # Verify API was called correctly
        epic_generator.anthropic.messages.create.assert_called_once()
        call_args = epic_generator.anthropic.messages.create.call_args
        assert call_args.kwargs['model'] == 'claude-3-sonnet-20240229'
        assert call_args.kwargs['max_tokens'] == 4096
    
    def test_generate_epics_retry_logic(self, epic_generator, sample_project_data):
        """Test retry logic on invalid responses."""
        # First two attempts fail, third succeeds
        invalid_response = '{"invalid": "json"}'
        valid_response = {
            "phaseId": "phase-1",
            "phaseTitle": "Test Phase",
            "epics": [{
                "title": "Test Epic",
                "description": "Test description",
                "suggestedRoles": ["Developer"],
                "tasks": [{
                    "title": "Test Task",
                    "description": "Task description",
                    "suggestedRole": "Developer"
                }]
            }]
        }
        
        mock_messages = [
            Mock(content=[Mock(text=invalid_response)]),
            Mock(content=[Mock(text=invalid_response)]),
            Mock(content=[Mock(text=json.dumps(valid_response))])
        ]
        
        epic_generator.anthropic.messages.create.side_effect = mock_messages
        
        # Should succeed on third attempt
        epics = epic_generator.generate_epics_for_phase(
            phase_number=1,
            phase_name="Test Phase",
            phase_description="Test",
            project_data=sample_project_data
        )
        
        assert len(epics) == 1
        assert epics[0]['title'] == "Test Epic"
        assert epic_generator.anthropic.messages.create.call_count == 3
    
    def test_generate_epics_max_retries_exceeded(self, epic_generator, sample_project_data):
        """Test failure after max retries."""
        epic_generator.anthropic.messages.create.return_value = Mock(
            content=[Mock(text='{"invalid": "json"}')]
        )
        
        with pytest.raises(Exception, match="Failed to generate valid epics after 3 attempts"):
            epic_generator.generate_epics_for_phase(
                phase_number=1,
                phase_name="Test Phase",
                phase_description="Test",
                project_data=sample_project_data
            )
    
    def test_extract_and_validate_epics(self, epic_generator, valid_epic_response):
        """Test extraction and validation of epic data."""
        # Test direct JSON
        result = epic_generator._extract_and_validate_epics(json.dumps(valid_epic_response))
        assert result['phaseId'] == 'phase-1'
        assert len(result['epics']) == 2
        
        # Test JSON in code block
        json_in_code_block = f"```json\n{json.dumps(valid_epic_response)}\n```"
        result = epic_generator._extract_and_validate_epics(json_in_code_block)
        assert len(result['epics']) == 2
        
        # Test JSON with trailing commas (should be fixed)
        json_with_commas = json.dumps(valid_epic_response).replace('}]', '},]')
        result = epic_generator._extract_and_validate_epics(json_with_commas)
        assert len(result['epics']) == 2
    
    def test_epic_model_validation(self):
        """Test Epic model validation."""
        # Valid epic
        epic = Epic(
            title="Test Epic",
            description="A test epic",
            tasks=[
                Task(
                    title="Task 1",
                    description="Task description",
                    suggestedRole="Developer"
                )
            ],
            suggestedRoles=["Developer", "Tester"]
        )
        assert epic.title == "Test Epic"
        assert len(epic.tasks) == 1
        
        # Invalid epic - empty tasks
        with pytest.raises(ValueError):
            Epic(
                title="Test Epic",
                description="Description",
                tasks=[],  # Empty tasks list
                suggestedRoles=["Developer"]
            )
    
    def test_task_model_validation(self):
        """Test Task model validation."""
        # Valid task
        task = Task(
            title="Implement feature",
            description="Implement the shopping cart feature",
            suggestedRole="Frontend Developer"
        )
        assert task.title == "Implement feature"
        assert task.suggestedRole == "Frontend Developer"
        
        # Invalid task - missing fields
        with pytest.raises(ValueError):
            Task(title="Test")  # Missing description and suggestedRole
    
    @pytest.mark.parametrize("phase_number,expected_epic_types", [
        (1, ["Stakeholder", "Market Research", "User Research"]),  # Discovery phase
        (2, ["Architecture", "Technology", "API Design"]),  # Planning phase
        (3, ["UX Research", "Visual Design", "Prototypes"]),  # Design phase
        (4, ["Backend Services", "Frontend", "Authentication"]),  # Development phase
    ])
    def test_phase_specific_epic_suggestions(self, epic_generator, sample_project_data, phase_number, expected_epic_types):
        """Test that different phases suggest appropriate epic types."""
        prompt = epic_generator._build_prompt(
            phase_number=phase_number,
            phase_name=f"Phase {phase_number}",
            phase_description="Test phase",
            project_data=sample_project_data
        )
        
        # Check that appropriate epic types are mentioned in examples
        for epic_type in expected_epic_types:
            assert epic_type.lower() in prompt.lower()
    
    def test_jtbd_framing_in_prompt(self, epic_generator, sample_project_data):
        """Test that JTBD framework is properly explained in prompt."""
        prompt = epic_generator._build_prompt(
            phase_number=1,
            phase_name="Discovery",
            phase_description="Initial discovery",
            project_data=sample_project_data
        )
        
        # Check JTBD instructions
        assert "Frame each epic around what job the user is trying to accomplish" in prompt
        assert "user value and desired outcomes" in prompt
    
    def test_moscow_prioritization_in_prompt(self, epic_generator, sample_project_data):
        """Test that MoSCoW prioritization is included."""
        prompt = epic_generator._build_prompt(
            phase_number=2,
            phase_name="Planning",
            phase_description="Planning phase",
            project_data=sample_project_data
        )
        
        assert "Must-have for MVP" in prompt
        assert "Should/Could have" in prompt
    
    def test_domain_specific_epics(self, epic_generator):
        """Test that AI/ML projects get appropriate epic suggestions."""
        ai_project_data = {
            'title': 'AI Recommendation Engine',
            'domain': 'artificial-intelligence',
            'features': ['ml-models', 'real-time-inference'],
            'techStack': ['Python', 'TensorFlow', 'Kafka']
        }
        
        prompt = epic_generator._build_prompt(
            phase_number=3,
            phase_name="Development",
            phase_description="Core development",
            project_data=ai_project_data
        )
        
        # Should mention AI-specific considerations
        assert "model training" in prompt
        assert "prompt engineering" in prompt