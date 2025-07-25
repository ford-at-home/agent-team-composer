"""Unit tests for task generator module."""

import json
import pytest
from unittest.mock import Mock, patch

from github_backlog_generator.task_generator import (
    TaskGenerator, Task, EpicTasks, TaskDescription
)


class TestTaskGenerator:
    """Test cases for TaskGenerator class."""
    
    @pytest.fixture
    def mock_anthropic(self):
        """Create a mock Anthropic client."""
        with patch('github_backlog_generator.task_generator.Anthropic') as mock:
            yield mock
    
    @pytest.fixture
    def task_generator(self, mock_anthropic):
        """Create a TaskGenerator instance with mocked Anthropic."""
        return TaskGenerator("test-api-key")
    
    @pytest.fixture
    def sample_epic(self):
        """Sample epic data for testing."""
        return {
            'title': 'Build Authentication System',
            'description': 'Implement secure multi-tenant authentication with SSO support',
            'suggestedRoles': ['Security Engineer', 'Backend Developer', 'DevOps Engineer'],
            'number': 42  # Epic issue number
        }
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            'title': 'SaaS Platform',
            'description': 'Multi-tenant SaaS platform for project management',
            'domain': 'enterprise-software',
            'features': ['multi-tenancy', 'sso', 'rbac'],
            'techStack': ['Node.js', 'Express', 'PostgreSQL', 'Redis', 'React']
        }
    
    @pytest.fixture
    def valid_tasks_response(self):
        """Valid AI response with tasks."""
        return {
            "epicTitle": "Build Authentication System",
            "tasks": [
                {
                    "title": "Design JWT token architecture for multi-tenancy",
                    "suggestedRole": "Security Engineer",
                    "priority": "high",
                    "estimatedEffort": "medium"
                },
                {
                    "title": "Implement OAuth2/OIDC provider integration",
                    "suggestedRole": "Backend Developer",
                    "priority": "high",
                    "estimatedEffort": "large"
                },
                {
                    "title": "Create tenant isolation middleware",
                    "suggestedRole": "Backend Developer",
                    "priority": "high",
                    "estimatedEffort": "medium"
                }
            ]
        }
    
    @pytest.fixture
    def valid_description_response(self):
        """Valid AI response for task description."""
        return {
            "title": "Design JWT token architecture for multi-tenancy",
            "description": "### Description\n\nDesign and document a secure JWT token architecture that supports multi-tenant isolation in our SaaS platform. The tokens must encode tenant context securely while maintaining stateless authentication.\n\n**Epic:** #42 [EPIC] Build Authentication System",
            "acceptanceCriteria": [
                "✅ JWT tokens include encrypted tenant ID that cannot be tampered with",
                "✅ Token rotation strategy documented with refresh token flow",
                "✅ Token size remains under 4KB for header compatibility"
            ],
            "technicalNotes": "Use RS256 algorithm for token signing with rotating keys stored in Redis. Implement token versioning to support gradual migrations. Follow OWASP JWT security best practices.",
            "dependencies": [
                "Redis cluster must be configured for key storage",
                "Security review of token structure required"
            ]
        }
    
    def test_init(self, mock_anthropic):
        """Test TaskGenerator initialization."""
        generator = TaskGenerator("test-key")
        assert generator.anthropic is not None
        assert generator.max_retries == 3
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    def test_build_tasks_prompt(self, task_generator, sample_epic, sample_project_data):
        """Test task generation prompt includes all mental models."""
        prompt = task_generator._build_tasks_prompt(
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Check for mental models section
        assert "Acceptance Criteria" in prompt
        assert "Test First Thinking" in prompt
        assert "One-Thing Rule" in prompt
        assert "Design by Contract" in prompt
        
        # Check for cognitive biases section
        assert "Overconfidence Bias" in prompt
        assert "Tunnel Vision" in prompt
        assert "Neglect of Probability" in prompt
        assert "Present Bias" in prompt
        
        # Check for bias mitigation
        assert "Add 50% to initial estimates" in prompt
        assert "Consider ripple effects" in prompt
        assert "edge case considerations" in prompt
        
        # Check for project context
        assert "SaaS Platform" in prompt
        assert "multi-tenancy" in prompt
        assert "Node.js" in prompt
        
        # Check for meta-strategy validation
        assert "META-STRATEGY VALIDATION" in prompt
        assert "Can it be tested/verified independently?" in prompt
    
    def test_generate_tasks_success(self, task_generator, sample_epic, sample_project_data, valid_tasks_response):
        """Test successful task generation."""
        # Mock the Anthropic response
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(valid_tasks_response))]
        task_generator.anthropic.messages.create.return_value = mock_message
        
        # Generate tasks
        tasks = task_generator.generate_tasks_for_epic(
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Verify the result
        assert len(tasks) == 3
        assert tasks[0]['title'] == "Design JWT token architecture for multi-tenancy"
        assert tasks[0]['priority'] == "high"
        assert tasks[0]['estimatedEffort'] == "medium"
        assert tasks[0]['suggestedRole'] == "Security Engineer"
        
        # Verify API was called correctly
        task_generator.anthropic.messages.create.assert_called_once()
        call_args = task_generator.anthropic.messages.create.call_args
        assert call_args.kwargs['model'] == 'claude-3-sonnet-20240229'
        assert call_args.kwargs['max_tokens'] == 2048
    
    def test_generate_task_description(self, task_generator, sample_epic, sample_project_data, valid_description_response):
        """Test task description generation."""
        task = {
            'title': 'Design JWT token architecture for multi-tenancy',
            'suggestedRole': 'Security Engineer',
            'priority': 'high',
            'estimatedEffort': 'medium'
        }
        
        # Mock the Anthropic response
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(valid_description_response))]
        task_generator.anthropic.messages.create.return_value = mock_message
        
        # Generate description
        description = task_generator.generate_task_description(
            task=task,
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Verify the result
        assert description['title'] == task['title']
        assert "multi-tenant isolation" in description['description']
        assert "Epic:** #42" in description['description']
        assert len(description['acceptanceCriteria']) == 3
        assert "Given-When-Then" in task_generator._build_description_prompt(task, sample_epic, "Core Development", sample_project_data)
        assert "RS256 algorithm" in description['technicalNotes']
        assert len(description['dependencies']) == 2
    
    def test_build_description_prompt(self, task_generator, sample_epic, sample_project_data):
        """Test description prompt includes mental models and best practices."""
        task = {
            'title': 'Test Task',
            'suggestedRole': 'Developer',
            'priority': 'medium',
            'estimatedEffort': 'small'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Development",
            project_data=sample_project_data
        )
        
        # Check for mental models
        assert "Given-When-Then format" in prompt
        assert "Test First Thinking" in prompt
        assert "Design by Contract" in prompt
        assert "Edge Cases" in prompt
        
        # Check for GitHub best practices
        assert "### Description" in prompt
        assert "**Epic:**" in prompt
        assert "### Acceptance Criteria" in prompt
        assert "### Technical Notes" in prompt
        
        # Check for specific technology references
        assert "Node.js" in prompt
        assert "Express" in prompt
        assert "PostgreSQL" in prompt
    
    def test_retry_logic(self, task_generator, sample_epic, sample_project_data):
        """Test retry logic for failed attempts."""
        # First attempt fails, second succeeds
        invalid_response = '{"invalid": "response"}'
        valid_response = {
            "epicTitle": "Test Epic",
            "tasks": [{
                "title": "Test Task",
                "suggestedRole": "Developer",
                "priority": "high",
                "estimatedEffort": "small"
            }]
        }
        
        mock_messages = [
            Mock(content=[Mock(text=invalid_response)]),
            Mock(content=[Mock(text=json.dumps(valid_response))])
        ]
        
        task_generator.anthropic.messages.create.side_effect = mock_messages
        
        # Should succeed on second attempt
        tasks = task_generator.generate_tasks_for_epic(
            epic=sample_epic,
            phase_name="Test Phase",
            project_data=sample_project_data
        )
        
        assert len(tasks) == 1
        assert tasks[0]['title'] == "Test Task"
        assert task_generator.anthropic.messages.create.call_count == 2
    
    def test_extract_and_validate_tasks(self, task_generator, valid_tasks_response):
        """Test extraction and validation of task data."""
        # Test direct JSON
        result = task_generator._extract_and_validate_tasks(json.dumps(valid_tasks_response))
        assert result['epicTitle'] == "Build Authentication System"
        assert len(result['tasks']) == 3
        
        # Test JSON in code block
        json_in_code_block = f"```json\n{json.dumps(valid_tasks_response)}\n```"
        result = task_generator._extract_and_validate_tasks(json_in_code_block)
        assert len(result['tasks']) == 3
        
        # Test JSON with trailing commas
        json_with_commas = json.dumps(valid_tasks_response).replace('}]', '},]')
        result = task_generator._extract_and_validate_tasks(json_with_commas)
        assert len(result['tasks']) == 3
    
    def test_task_model_validation(self):
        """Test Task model validation."""
        # Valid task
        task = Task(
            title="Implement feature",
            suggestedRole="Backend Developer",
            priority="high",
            estimatedEffort="medium"
        )
        assert task.title == "Implement feature"
        assert task.priority == "high"
        
        # Invalid priority
        with pytest.raises(ValueError):
            Task(
                title="Test",
                suggestedRole="Developer",
                priority="urgent",  # Invalid priority
                estimatedEffort="medium"
            )
        
        # Invalid effort
        with pytest.raises(ValueError):
            Task(
                title="Test",
                suggestedRole="Developer",
                priority="high",
                estimatedEffort="huge"  # Invalid effort
            )
    
    def test_one_thing_rule(self, task_generator, sample_epic, sample_project_data):
        """Test that prompt emphasizes one-thing rule."""
        prompt = task_generator._build_tasks_prompt(
            epic=sample_epic,
            phase_name="Development",
            project_data=sample_project_data
        )
        
        assert "One issue = one deliverable" in prompt
        assert "avoid bundling" in prompt
        assert "discrete, completable unit of work" in prompt
    
    def test_edge_case_consideration(self, task_generator, sample_epic, sample_project_data):
        """Test that prompts include edge case handling."""
        task = {
            'title': 'Implement API endpoint',
            'suggestedRole': 'Backend Developer',
            'priority': 'high',
            'estimatedEffort': 'medium'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Development",
            project_data=sample_project_data
        )
        
        assert "failure scenarios" in prompt
        assert "edge cases" in prompt
        assert "Neglect of Probability" in prompt
    
    @pytest.mark.parametrize("effort,expected_buffer", [
        ("small", 1.5),  # 50% buffer
        ("medium", 1.5),  # 50% buffer
        ("large", 1.5),  # 50% buffer
    ])
    def test_effort_estimation_buffer(self, task_generator, sample_epic, sample_project_data, effort, expected_buffer):
        """Test that effort estimates include overconfidence buffer."""
        prompt = task_generator._build_tasks_prompt(
            epic=sample_epic,
            phase_name="Development",
            project_data=sample_project_data
        )
        
        # Check that prompt mentions adding buffer
        assert "Add 50% to initial estimates" in prompt
        assert "Overconfidence Bias" in prompt
    
    def test_issue_types_coverage(self, task_generator, sample_epic, sample_project_data):
        """Test that various issue types are suggested."""
        prompt = task_generator._build_tasks_prompt(
            epic=sample_epic,
            phase_name="Development",
            project_data=sample_project_data
        )
        
        # Check for different issue types
        assert "Feature implementation" in prompt
        assert "Documentation updates" in prompt
        assert "Testing tasks" in prompt
        assert "Infrastructure/DevOps work" in prompt
        assert "Error handling and edge cases" in prompt