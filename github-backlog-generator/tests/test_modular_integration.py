"""Integration tests for the modular workflow."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from github_backlog_generator.cli_modular import BacklogManager
from github_backlog_generator.phase_generator import PhaseGenerator
from github_backlog_generator.epic_generator import EpicGenerator
from github_backlog_generator.task_generator import TaskGenerator
from github_backlog_generator.github_client import GitHubClient


class TestModularWorkflowIntegration:
    """Integration tests for the complete modular workflow."""
    
    @pytest.fixture
    def test_project_data(self):
        """Sample project data for testing."""
        return {
            'title': 'E-Commerce Platform',
            'description': 'Modern e-commerce platform with microservices',
            'domain': 'e-commerce',
            'complexity': 'high',
            'features': [
                'product-catalog',
                'shopping-cart',
                'payment-processing',
                'order-management',
                'user-authentication'
            ],
            'techStack': ['Node.js', 'React', 'PostgreSQL', 'Redis', 'AWS CDK', 'Docker']
        }
    
    @pytest.fixture
    def temp_backlog_dir(self, tmp_path):
        """Create temporary backlog directory."""
        backlog_dir = tmp_path / ".backlog-test-owner-test-repo"
        backlog_dir.mkdir()
        (backlog_dir / "phases").mkdir()
        return backlog_dir
    
    @pytest.fixture
    def manager(self, temp_backlog_dir):
        """Create BacklogManager with temp directory."""
        manager = BacklogManager("test-owner", "test-repo")
        manager.base_dir = temp_backlog_dir
        manager.metadata_file = temp_backlog_dir / "metadata.json"
        manager.phases_dir = temp_backlog_dir / "phases"
        return manager
    
    def test_complete_workflow(self, manager, test_project_data):
        """Test the complete workflow from project init to issue generation."""
        # Step 1: Save project metadata
        manager.save_metadata(test_project_data)
        
        # Verify metadata saved correctly
        metadata = manager.load_metadata()
        assert metadata['project_data']['title'] == 'E-Commerce Platform'
        assert 'AWS CDK' in metadata['project_data']['techStack']
        
        # Step 2: Generate and save phases
        phases = []
        for i in range(1, 9):
            phase = {
                'number': i,
                'title': f'Phase {i}',
                'description': f'Description for phase {i}',
                'id': f'phase-{i}',
                'dueDate': datetime.now().isoformat()
            }
            phases.append(phase)
        
        manager.save_phases(phases)
        
        # Verify phases structure
        assert (manager.phases_dir / "phases.json").exists()
        assert (manager.phases_dir / "phase1").exists()
        assert (manager.phases_dir / "phase1" / "phase.json").exists()
        
        # Step 3: Generate epics for phase 1
        epics = [
            {
                'title': 'Setup Infrastructure',
                'description': 'Setup AWS infrastructure using CDK',
                'suggestedRoles': ['DevOps Engineer', 'Backend Developer'],
                'tasks': []
            },
            {
                'title': 'Build Authentication Service',
                'description': 'Implement user authentication and authorization',
                'suggestedRoles': ['Security Engineer', 'Backend Developer'],
                'tasks': []
            }
        ]
        
        manager.save_epics(1, epics)
        
        # Verify epic structure
        assert (manager.phases_dir / "phase1" / "epics.json").exists()
        assert (manager.phases_dir / "phase1" / "epic1").exists()
        assert (manager.phases_dir / "phase1" / "epic1" / "epic.json").exists()
        
        # Step 4: Generate issues for epic 1
        issues = [
            {
                'title': 'Create VPC and networking stack',
                'description': '### Description\n\nCreate VPC with public/private subnets...',
                'acceptanceCriteria': [
                    '✅ VPC created with proper CIDR blocks',
                    '✅ Component can be unit tested in isolation',
                    '✅ CDK stack deploys successfully',
                    '✅ All upstream dependencies documented'
                ],
                'technicalNotes': '### Pre-work Investigation\n\n1. Run `cdk list`...',
                'dependencies': ['AWS account setup'],
                'priority': 'high',
                'estimatedEffort': 'medium',
                'suggestedRole': 'DevOps Engineer'
            },
            {
                'title': 'Setup RDS PostgreSQL instance',
                'description': '### Description\n\nProvision RDS PostgreSQL...',
                'acceptanceCriteria': [
                    '✅ RDS instance provisioned',
                    '✅ Integration tested with app',
                    '✅ Deployment automated'
                ],
                'technicalNotes': '### Pre-work Investigation\n\nCheck existing stacks...',
                'dependencies': ['VPC must exist'],
                'priority': 'high',
                'estimatedEffort': 'large',
                'suggestedRole': 'DevOps Engineer'
            }
        ]
        
        manager.save_issues(1, 1, issues)
        
        # Verify issue structure
        issues_file = manager.phases_dir / "phase1" / "epic1" / "issues.json"
        assert issues_file.exists()
        
        # Load and verify saved issues
        loaded_issues = manager.load_issues(1, 1)
        assert len(loaded_issues) == 2
        assert loaded_issues[0]['title'] == 'Create VPC and networking stack'
        
        # Verify acceptance criteria include new requirements
        ac = loaded_issues[0]['acceptanceCriteria']
        assert any('unit tested in isolation' in criterion for criterion in ac)
        assert any('upstream dependencies documented' in criterion for criterion in ac)
        
        # Step 5: Test cascading file structure
        self._verify_file_structure(manager)
    
    def _verify_file_structure(self, manager):
        """Verify the complete cascading file structure."""
        base = manager.base_dir
        
        # Root level files
        assert (base / "metadata.json").exists()
        
        # Phases directory
        assert (base / "phases").exists()
        assert (base / "phases" / "phases.json").exists()
        
        # Phase 1 directory
        phase1 = base / "phases" / "phase1"
        assert phase1.exists()
        assert (phase1 / "phase.json").exists()
        assert (phase1 / "epics.json").exists()
        
        # Epic directories
        assert (phase1 / "epic1").exists()
        assert (phase1 / "epic1" / "epic.json").exists()
        assert (phase1 / "epic1" / "issues.json").exists()
        
        # No subdirectories beyond issues
        issues_dir = phase1 / "epic1"
        subdirs = [d for d in issues_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 0, "No subdirectories should exist beyond epic level"
    
    def test_json_structure_validation(self, manager, test_project_data):
        """Test that all JSON files have correct structure."""
        # Save test data
        manager.save_metadata(test_project_data)
        
        phases = [{
            'number': 1,
            'title': 'Infrastructure Setup',
            'description': 'Setup cloud infrastructure',
            'id': 'phase-1',
            'dueDate': datetime.now().isoformat()
        }]
        manager.save_phases(phases)
        
        epics = [{
            'title': 'CDK Stack Development',
            'description': 'Develop infrastructure as code',
            'suggestedRoles': ['DevOps Engineer'],
            'tasks': []
        }]
        manager.save_epics(1, epics)
        
        issues = [{
            'title': 'Create Lambda function stack',
            'description': 'Deploy Lambda functions using CDK',
            'acceptanceCriteria': [
                '✅ Lambda functions deploy successfully',
                '✅ Unit tests pass',
                '✅ Integration with API Gateway verified'
            ],
            'technicalNotes': 'Use CDK patterns',
            'dependencies': [],
            'priority': 'high',
            'estimatedEffort': 'medium',
            'suggestedRole': 'Backend Developer'
        }]
        manager.save_issues(1, 1, issues)
        
        # Validate metadata.json
        with open(manager.metadata_file) as f:
            metadata = json.load(f)
            assert 'owner' in metadata
            assert 'repo' in metadata
            assert 'project_data' in metadata
            assert 'created_at' in metadata
            assert 'last_updated' in metadata
        
        # Validate phases.json
        with open(manager.phases_dir / "phases.json") as f:
            phases_data = json.load(f)
            assert 'phases' in phases_data
            assert 'generated_at' in phases_data
            assert len(phases_data['phases']) == 1
        
        # Validate epics.json
        with open(manager.phases_dir / "phase1" / "epics.json") as f:
            epics_data = json.load(f)
            assert 'phase_num' in epics_data
            assert 'epics' in epics_data
            assert 'generated_at' in epics_data
            assert epics_data['phase_num'] == 1
        
        # Validate issues.json
        with open(manager.phases_dir / "phase1" / "epic1" / "issues.json") as f:
            issues_data = json.load(f)
            assert 'phase_num' in issues_data
            assert 'epic_num' in issues_data
            assert 'issues' in issues_data
            assert 'generated_at' in issues_data
            assert issues_data['phase_num'] == 1
            assert issues_data['epic_num'] == 1
    
    def test_milestone_mapping_integration(self, manager):
        """Test milestone mapping functionality."""
        # Save milestone mapping
        mapping = {
            1: 101,
            2: 102,
            3: 103,
            4: 104
        }
        manager.save_milestone_mapping(mapping)
        
        # Load and verify
        loaded_mapping = manager.get_milestone_mapping()
        assert loaded_mapping == mapping
        
        # Verify file structure
        mapping_file = manager.base_dir / "milestone_mapping.json"
        assert mapping_file.exists()
        
        with open(mapping_file) as f:
            data = json.load(f)
            assert 'milestones' in data
            assert 'updated_at' in data
    
    def test_incremental_generation(self, manager, test_project_data):
        """Test that generation can be done incrementally."""
        # Save initial data
        manager.save_metadata(test_project_data)
        
        phases = [
            {'number': i, 'title': f'Phase {i}', 'description': f'Desc {i}', 
             'id': f'phase-{i}', 'dueDate': datetime.now().isoformat()}
            for i in range(1, 4)
        ]
        manager.save_phases(phases)
        
        # Generate epics for phase 1 only
        phase1_epics = [
            {'title': 'Epic 1.1', 'description': 'First epic', 'suggestedRoles': ['Dev'], 'tasks': []},
            {'title': 'Epic 1.2', 'description': 'Second epic', 'suggestedRoles': ['Dev'], 'tasks': []}
        ]
        manager.save_epics(1, phase1_epics)
        
        # Verify only phase 1 has epics
        assert (manager.phases_dir / "phase1" / "epics.json").exists()
        assert not (manager.phases_dir / "phase2" / "epics.json").exists()
        
        # Generate issues for epic 1 only
        issues = [
            {'title': 'Issue 1', 'description': 'First issue', 'priority': 'high'}
        ]
        manager.save_issues(1, 1, issues)
        
        # Verify only epic 1 has issues
        assert (manager.phases_dir / "phase1" / "epic1" / "issues.json").exists()
        assert not (manager.phases_dir / "phase1" / "epic2" / "issues.json").exists()
        
        # Later, generate epics for phase 2
        phase2_epics = [
            {'title': 'Epic 2.1', 'description': 'Phase 2 epic', 'suggestedRoles': ['QA'], 'tasks': []}
        ]
        manager.save_epics(2, phase2_epics)
        
        # Verify phase 2 now has epics
        assert (manager.phases_dir / "phase2" / "epics.json").exists()
    
    def test_enhanced_issue_content(self, manager):
        """Test that issues contain all enhanced requirements."""
        issue = {
            'title': 'Implement user authentication API',
            'description': '### Description\n\nImplement RESTful API for user authentication...',
            'acceptanceCriteria': [
                '✅ API endpoints return correct status codes',
                '✅ Component can be unit tested in isolation with mocked dependencies',
                '✅ Component successfully integrates with existing UserService and AuthMiddleware',
                '✅ Performance: Authentication completes in < 100ms',
                '✅ All upstream dependencies identified and documented',
                '✅ Deployment commands execute successfully in the single environment',
                '✅ Documentation updated with \'why\' explanations for key decisions'
            ],
            'technicalNotes': '''### Pre-work Investigation

Before starting implementation:
1. Run `cdk list` to discover existing stacks
2. Search for existing components: `grep -r 'AuthService' .`
3. Document all discovered upstream dependencies

### Implementation Guidance

Implementation guidance specific to Node.js, Express. Include architecture decisions, API endpoints, data models, or algorithms relevant to this issue.

### Deployment Instructions

**Environment:** Single environment only (no dev/staging/prod)

1. Run unit tests: `npm test`
2. Run integration tests: `npm run test:integration`
3. Deploy to AWS: `cdk deploy AuthStack --require-approval never`
4. Verify deployment: `aws cloudformation describe-stacks --stack-name AuthStack`

### Documentation Requirements

- Every function/class must have a docstring explaining WHY it exists
- Update README.md with any new setup steps
- Do NOT commit: test files, debug logs, experimental code
- ONLY commit: source code, tests, documentation''',
            'dependencies': ['UserService must be deployed', 'Database schema updated'],
            'priority': 'high',
            'estimatedEffort': 'large',
            'suggestedRole': 'Backend Developer'
        }
        
        # Save the issue
        manager.save_issues(1, 1, [issue])
        
        # Load and verify
        loaded = manager.load_issues(1, 1)
        assert len(loaded) == 1
        
        loaded_issue = loaded[0]
        
        # Verify all sections are present
        assert '### Pre-work Investigation' in loaded_issue['technicalNotes']
        assert '### Implementation Guidance' in loaded_issue['technicalNotes']
        assert '### Deployment Instructions' in loaded_issue['technicalNotes']
        assert '### Documentation Requirements' in loaded_issue['technicalNotes']
        
        # Verify specific requirements
        assert 'cdk list' in loaded_issue['technicalNotes']
        assert 'Single environment only' in loaded_issue['technicalNotes']
        assert '--require-approval never' in loaded_issue['technicalNotes']
        assert 'WHY it exists' in loaded_issue['technicalNotes']
        
        # Verify acceptance criteria
        ac = loaded_issue['acceptanceCriteria']
        assert any('unit tested in isolation' in c for c in ac)
        assert any('integrates with existing' in c for c in ac)
        assert any('upstream dependencies identified' in c for c in ac)
        assert any('Deployment commands execute' in c for c in ac)
        assert any('Documentation updated' in c for c in ac)
    
    @pytest.mark.parametrize("phase_num,epic_num", [
        (1, 1), (1, 2), (2, 1), (8, 10)
    ])
    def test_path_consistency(self, manager, phase_num, epic_num):
        """Test that paths are consistent across save/load operations."""
        # Create test issue
        test_issue = {
            'title': f'Test Issue P{phase_num}E{epic_num}',
            'description': 'Test description',
            'priority': 'medium'
        }
        
        # Save issue
        manager.save_issues(phase_num, epic_num, [test_issue])
        
        # Verify path
        expected_path = manager.phases_dir / f"phase{phase_num}" / f"epic{epic_num}" / "issues.json"
        assert expected_path.exists()
        
        # Load and verify
        loaded = manager.load_issues(phase_num, epic_num)
        assert loaded is not None
        assert len(loaded) == 1
        assert loaded[0]['title'] == f'Test Issue P{phase_num}E{epic_num}'