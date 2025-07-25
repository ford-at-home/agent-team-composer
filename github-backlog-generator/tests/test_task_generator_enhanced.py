"""Enhanced unit tests for task generator with new requirements."""

import json
import pytest
from unittest.mock import Mock, patch

from github_backlog_generator.task_generator import (
    TaskGenerator, Task, EpicTasks, TaskDescription
)


class TestEnhancedTaskGenerator:
    """Test cases for enhanced TaskGenerator features."""
    
    @pytest.fixture
    def task_generator(self):
        """Create a TaskGenerator instance."""
        with patch('github_backlog_generator.task_generator.Anthropic'):
            return TaskGenerator("test-api-key")
    
    @pytest.fixture
    def sample_epic(self):
        """Sample epic data for testing."""
        return {
            'title': 'Build Authentication System',
            'description': 'Implement secure multi-tenant authentication with SSO support',
            'suggestedRoles': ['Security Engineer', 'Backend Developer', 'DevOps Engineer'],
            'number': 42
        }
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            'title': 'SaaS Platform',
            'description': 'Multi-tenant SaaS platform for project management',
            'domain': 'enterprise-software',
            'features': ['multi-tenancy', 'sso', 'rbac'],
            'techStack': ['Node.js', 'Express', 'PostgreSQL', 'Redis', 'React', 'AWS CDK']
        }
    
    def test_acceptance_criteria_includes_testing(self, task_generator, sample_epic, sample_project_data):
        """Test that acceptance criteria include unit and integration testing requirements."""
        task = {
            'title': 'Implement JWT validation middleware',
            'suggestedRole': 'Backend Developer',
            'priority': 'high',
            'estimatedEffort': 'medium'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Check for testing requirements in prompt
        assert "Component can be unit tested in isolation" in prompt
        assert "Component can be integration tested with existing components" in prompt
        assert "Component can be unit tested in isolation with mocked dependencies" in prompt
        assert "Component successfully integrates with existing" in prompt
        
        # Check for specific testing criteria
        assert "acceptanceCriteria" in prompt
        assert "unit tested in isolation" in prompt
        assert "integration tested" in prompt
    
    def test_pre_work_investigation_requirements(self, task_generator, sample_epic, sample_project_data):
        """Test that pre-work investigation steps are included."""
        task = {
            'title': 'Create Lambda function for user authentication',
            'suggestedRole': 'Backend Developer',
            'priority': 'high',
            'estimatedEffort': 'large'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Check for CDK discovery requirements
        assert "cdk list" in prompt
        assert "Search for existing CDK stacks" in prompt
        assert "discover existing stacks" in prompt
        assert "Document all discovered upstream dependencies" in prompt
        
        # Check for component search requirements
        assert "Search for existing components" in prompt
        assert "grep -r 'ComponentName'" in prompt
        assert "exact naming, location, and configuration of upstream dependencies" in prompt
    
    def test_deployment_instructions_single_environment(self, task_generator, sample_epic, sample_project_data):
        """Test that deployment instructions specify single environment."""
        task = {
            'title': 'Deploy authentication service',
            'suggestedRole': 'DevOps Engineer',
            'priority': 'high',
            'estimatedEffort': 'medium'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Deployment",
            project_data=sample_project_data
        )
        
        # Check for single environment specification
        assert "Single environment only" in prompt
        assert "no dev/staging/prod" in prompt
        assert "Do not use environment-specific naming conventions" in prompt
        
        # Check for specific deployment commands
        assert "cdk deploy StackName --require-approval never" in prompt
        assert "aws cloudformation describe-stacks" in prompt
        assert "npm test" in prompt
        assert "npm run test:integration" in prompt
        
        # Check for automated deployment after tests
        assert "Must deploy automatically after tests pass and product owner review" in prompt
    
    def test_documentation_requirements(self, task_generator, sample_epic, sample_project_data):
        """Test that documentation requirements are properly specified."""
        task = {
            'title': 'Implement user session management',
            'suggestedRole': 'Backend Developer',
            'priority': 'medium',
            'estimatedEffort': 'medium'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Check for "why" documentation requirements
        assert 'heavily documented with "why"' in prompt
        assert 'not just "what"' in prompt
        assert "Every function/class must have a docstring explaining WHY it exists" in prompt
        
        # Check for file commit restrictions
        assert "Do not commit experimental or troubleshooting files" in prompt
        assert "Only commit the bare minimum files needed for functionality" in prompt
        assert "Do NOT commit: test files, debug logs, experimental code" in prompt
        assert "ONLY commit: source code, tests, documentation" in prompt
    
    def test_example_technical_notes_format(self, task_generator, sample_epic, sample_project_data):
        """Test that technical notes example includes all required sections."""
        task = {
            'title': 'Create API Gateway integration',
            'suggestedRole': 'Backend Developer',
            'priority': 'high',
            'estimatedEffort': 'large'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Check for example sections
        assert "### Pre-work Investigation" in prompt
        assert "### Implementation Guidance" in prompt
        assert "### Deployment Instructions" in prompt
        assert "### Documentation Requirements" in prompt
        
        # Check example includes CDK discovery
        assert "Run `cdk list` - found existing stacks" in prompt
        assert "UserAuthStack, APIGatewayStack" in prompt
        
        # Check example includes deployment commands
        assert "Run tests: `npm test" in prompt
        assert "Deploy: `cdk deploy" in prompt
        assert "Verify: `curl -X POST" in prompt
    
    def test_enhanced_acceptance_criteria_format(self, task_generator, sample_epic, sample_project_data):
        """Test that acceptance criteria include all enhanced requirements."""
        # Create a mock response that includes the enhanced criteria
        enhanced_response = {
            "title": "Implement JWT validation middleware",
            "description": "### Description\n\nImplement middleware for JWT validation...",
            "acceptanceCriteria": [
                "✅ JWT tokens are validated correctly",
                "✅ Invalid tokens return 401 status",
                "✅ Component can be unit tested in isolation with mocked dependencies",
                "✅ Component successfully integrates with existing AuthService and UserRepository",
                "✅ Performance: Token validation completes in < 50ms",
                "✅ All upstream dependencies identified and documented",
                "✅ Deployment commands execute successfully in the single environment",
                "✅ Documentation updated with 'why' explanations for key decisions"
            ],
            "technicalNotes": "### Pre-work Investigation\n\n1. Run `cdk list`...",
            "dependencies": ["AuthService must be deployed", "Redis cache available"]
        }
        
        # Mock the response
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(enhanced_response))]
        task_generator.anthropic.messages.create.return_value = mock_message
        
        task = {
            'title': 'Implement JWT validation middleware',
            'suggestedRole': 'Backend Developer',
            'priority': 'high',
            'estimatedEffort': 'medium'
        }
        
        # Generate description
        description = task_generator.generate_task_description(
            task=task,
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Verify enhanced criteria are present
        criteria = description['acceptanceCriteria']
        assert any("unit tested in isolation" in c for c in criteria)
        assert any("integrates with existing" in c for c in criteria)
        assert any("upstream dependencies identified" in c for c in criteria)
        assert any("Deployment commands execute successfully" in c for c in criteria)
        assert any("Documentation updated" in c for c in criteria)
    
    def test_cdk_specific_project_handling(self, task_generator, sample_epic, sample_project_data):
        """Test that CDK projects get appropriate instructions."""
        # Ensure AWS CDK is in tech stack
        assert 'AWS CDK' in sample_project_data['techStack']
        
        task = {
            'title': 'Create DynamoDB table for user sessions',
            'suggestedRole': 'Backend Developer',
            'priority': 'medium',
            'estimatedEffort': 'small'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Core Development",
            project_data=sample_project_data
        )
        
        # Should reference CDK specifically
        assert "AWS CDK" in prompt
        assert "cdk list" in prompt
        assert "cdk deploy" in prompt
    
    def test_no_environment_specific_naming(self, task_generator, sample_epic, sample_project_data):
        """Test that environment-specific naming is discouraged."""
        task = {
            'title': 'Configure API Gateway endpoints',
            'suggestedRole': 'DevOps Engineer',
            'priority': 'high',
            'estimatedEffort': 'medium'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Deployment",
            project_data=sample_project_data
        )
        
        # Check warnings against environment naming
        assert "no dev/staging/prod separation" in prompt
        assert "Do not use environment-specific naming" in prompt
        assert "ONE environment" in prompt
    
    def test_automated_deployment_requirement(self, task_generator, sample_epic, sample_project_data):
        """Test that automated deployment after review is required."""
        task = {
            'title': 'Setup CI/CD pipeline',
            'suggestedRole': 'DevOps Engineer',
            'priority': 'high',
            'estimatedEffort': 'large'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Deployment",
            project_data=sample_project_data
        )
        
        # Check for automated deployment requirement
        assert "deploy automatically after tests pass" in prompt
        assert "product owner review" in prompt
        
        # Check that deployment commands are without approval
        assert "--require-approval never" in prompt
    
    @pytest.mark.parametrize("bad_files", [
        "test files",
        "debug logs", 
        "experimental code",
        "troubleshooting files"
    ])
    def test_files_not_to_commit(self, task_generator, sample_epic, sample_project_data, bad_files):
        """Test that instructions specify what files NOT to commit."""
        task = {
            'title': 'Implement feature',
            'suggestedRole': 'Developer',
            'priority': 'medium',
            'estimatedEffort': 'medium'
        }
        
        prompt = task_generator._build_description_prompt(
            task=task,
            epic=sample_epic,
            phase_name="Development",
            project_data=sample_project_data
        )
        
        assert bad_files in prompt
        assert "Do NOT commit" in prompt
        assert "ONLY commit: source code, tests, documentation" in prompt