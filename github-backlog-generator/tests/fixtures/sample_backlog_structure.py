"""Test fixtures for sample backlog file structures."""

import json
from datetime import datetime
from pathlib import Path


def create_sample_backlog_structure(base_path: Path) -> None:
    """Create a complete sample backlog file structure for testing."""
    
    # Create base directory
    base_path.mkdir(exist_ok=True)
    
    # Create metadata.json
    metadata = {
        'owner': 'test-owner',
        'repo': 'test-repo',
        'project_data': {
            'title': 'Test E-Commerce Platform',
            'description': 'A modern e-commerce platform with microservices architecture',
            'domain': 'e-commerce',
            'complexity': 'high',
            'features': [
                'product-catalog',
                'shopping-cart', 
                'payment-processing',
                'order-management',
                'user-authentication',
                'inventory-management'
            ],
            'techStack': ['Node.js', 'React', 'PostgreSQL', 'Redis', 'AWS CDK', 'Docker', 'Kubernetes']
        },
        'created_at': '2024-01-15T10:00:00Z',
        'last_updated': '2024-01-15T10:00:00Z'
    }
    
    with open(base_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Create milestone_mapping.json
    milestone_mapping = {
        'milestones': {
            '1': 101,
            '2': 102,
            '3': 103,
            '4': 104,
            '5': 105,
            '6': 106,
            '7': 107,
            '8': 108
        },
        'updated_at': '2024-01-15T10:05:00Z'
    }
    
    with open(base_path / 'milestone_mapping.json', 'w') as f:
        json.dump(milestone_mapping, f, indent=2)
    
    # Create phases directory
    phases_dir = base_path / 'phases'
    phases_dir.mkdir(exist_ok=True)
    
    # Define all 8 phases
    phases = [
        {
            'number': 1,
            'title': 'Discovery & Requirements',
            'description': 'This phase focuses on understanding the project requirements, user needs, and technical constraints.',
            'id': 'phase-1',
            'dueDate': '2024-02-01T00:00:00Z'
        },
        {
            'number': 2,
            'title': 'Technical Planning & Architecture',
            'description': 'This phase involves designing the system architecture and planning the technical implementation.',
            'id': 'phase-2',
            'dueDate': '2024-02-15T00:00:00Z'
        },
        {
            'number': 3,
            'title': 'UI/UX Design & Prototyping',
            'description': 'This phase centers on creating the user experience and interactive prototypes.',
            'id': 'phase-3',
            'dueDate': '2024-03-01T00:00:00Z'
        }
        # Add more phases as needed for complete testing
    ]
    
    # Save phases.json
    phases_data = {
        'phases': phases,
        'generated_at': '2024-01-15T10:00:00Z'
    }
    
    with open(phases_dir / 'phases.json', 'w') as f:
        json.dump(phases_data, f, indent=2)
    
    # Create sample data for phase 1
    phase1_dir = phases_dir / 'phase1'
    phase1_dir.mkdir(exist_ok=True)
    
    # Save phase1/phase.json
    with open(phase1_dir / 'phase.json', 'w') as f:
        json.dump(phases[0], f, indent=2)
    
    # Create epics for phase 1
    phase1_epics = [
        {
            'title': 'Market Research and User Analysis',
            'description': 'Conduct comprehensive market research and user analysis to understand target audience needs',
            'suggestedRoles': ['Product Manager', 'UX Researcher', 'Business Analyst'],
            'tasks': [],
            'github_number': 1,
            'github_url': 'https://github.com/test-owner/test-repo/issues/1'
        },
        {
            'title': 'Technical Feasibility Study',
            'description': 'Evaluate technical options and constraints for the e-commerce platform',
            'suggestedRoles': ['Technical Lead', 'DevOps Engineer', 'Security Engineer'],
            'tasks': [],
            'github_number': 2,
            'github_url': 'https://github.com/test-owner/test-repo/issues/2'
        }
    ]
    
    # Save phase1/epics.json
    epics_data = {
        'phase_num': 1,
        'epics': phase1_epics,
        'generated_at': '2024-01-15T10:10:00Z'
    }
    
    with open(phase1_dir / 'epics.json', 'w') as f:
        json.dump(epics_data, f, indent=2)
    
    # Create epic directories and issues
    for i, epic in enumerate(phase1_epics, 1):
        epic_dir = phase1_dir / f'epic{i}'
        epic_dir.mkdir(exist_ok=True)
        
        # Save epic.json
        with open(epic_dir / 'epic.json', 'w') as f:
            json.dump(epic, f, indent=2)
        
        # Create sample issues
        if i == 1:  # First epic - Market Research
            issues = [
                {
                    'title': 'Conduct user interviews with target demographics',
                    'description': '''### Description

Conduct in-depth user interviews with potential customers from our target demographics to understand their e-commerce needs and pain points.

**Epic:** #1 [EPIC] Market Research and User Analysis''',
                    'acceptanceCriteria': [
                        '✅ Interview at least 20 users from different demographic groups',
                        '✅ Document key findings and pain points identified',
                        '✅ Component can be unit tested in isolation with mocked dependencies',
                        '✅ Component successfully integrates with existing research database',
                        '✅ Create user persona documents based on findings',
                        '✅ All upstream dependencies identified and documented',
                        '✅ Deployment commands execute successfully in the single environment',
                        '✅ Documentation updated with \'why\' explanations for key decisions'
                    ],
                    'technicalNotes': '''### Pre-work Investigation

Before starting implementation:
1. Run `cdk list` to discover existing stacks
2. Search for existing components: `grep -r 'ResearchDB' .`
3. Document all discovered upstream dependencies

### Implementation Guidance

Set up interview recording infrastructure using existing tools. Integrate with our research database for storing insights.

### Deployment Instructions

**Environment:** Single environment only (no dev/staging/prod)

1. Run unit tests: `npm test`
2. Run integration tests: `npm run test:integration`
3. Deploy to AWS: `cdk deploy ResearchStack --require-approval never`
4. Verify deployment: `aws cloudformation describe-stacks --stack-name ResearchStack`

### Documentation Requirements

- Every function/class must have a docstring explaining WHY it exists
- Update README.md with any new setup steps
- Do NOT commit: test files, debug logs, experimental code
- ONLY commit: source code, tests, documentation''',
                    'dependencies': ['Research database must be set up', 'Interview tools configured'],
                    'priority': 'high',
                    'estimatedEffort': 'large',
                    'suggestedRole': 'UX Researcher'
                },
                {
                    'title': 'Analyze competitor e-commerce platforms',
                    'description': '''### Description

Perform competitive analysis of leading e-commerce platforms to identify best practices and opportunities for differentiation.

**Epic:** #1 [EPIC] Market Research and User Analysis''',
                    'acceptanceCriteria': [
                        '✅ Analyze at least 5 major competitor platforms',
                        '✅ Document feature comparisons and gap analysis',
                        '✅ Component can be unit tested in isolation',
                        '✅ Integration with analysis tools verified',
                        '✅ Create competitive analysis report',
                        '✅ All findings stored in research database',
                        '✅ Deployment successful in single environment',
                        '✅ Documentation includes decision rationale'
                    ],
                    'technicalNotes': '''### Pre-work Investigation

1. Check existing analysis tools: `cdk list | grep Analysis`
2. Find competitor data sources: `grep -r 'CompetitorAPI' .`
3. Document integration points

### Implementation Guidance

Use automated scraping tools where legal. Focus on public information and user experience analysis.

### Deployment Instructions

**Environment:** Single environment only

1. Test scraping scripts: `python -m pytest tests/scrapers`
2. Deploy analysis stack: `cdk deploy AnalysisStack --require-approval never`
3. Verify data collection: `aws s3 ls s3://analysis-bucket/competitors/`

### Documentation Requirements

- Document WHY each competitor was selected
- Explain analysis methodology
- ONLY commit sanitized, legal data''',
                    'dependencies': ['Legal approval for competitive analysis'],
                    'priority': 'medium',
                    'estimatedEffort': 'medium',
                    'suggestedRole': 'Business Analyst'
                }
            ]
        else:  # Second epic - Technical Feasibility
            issues = [
                {
                    'title': 'Evaluate microservices vs monolithic architecture',
                    'description': '''### Description

Create proof-of-concept implementations to evaluate microservices versus monolithic architecture for our e-commerce platform.

**Epic:** #2 [EPIC] Technical Feasibility Study''',
                    'acceptanceCriteria': [
                        '✅ PoC for both architectures implemented',
                        '✅ Performance benchmarks documented',
                        '✅ Components can be unit tested in isolation',
                        '✅ Integration testing between services successful',
                        '✅ Cost analysis for both approaches',
                        '✅ All infrastructure dependencies documented',
                        '✅ CDK stacks deploy successfully',
                        '✅ Architecture decision documented with rationale'
                    ],
                    'technicalNotes': '''### Pre-work Investigation

1. Run `cdk list` to see existing infrastructure
2. Search for service templates: `find . -name "*service-template*"`
3. Review existing architecture patterns

### Implementation Guidance

Create minimal but representative implementations. Focus on critical paths like product search and checkout.

### Deployment Instructions

**Environment:** Single environment only (no dev/staging/prod)

1. Run architecture tests: `npm run test:architecture`
2. Deploy PoC stacks: `cdk deploy PoCStack --require-approval never`
3. Run benchmarks: `npm run benchmark`
4. Generate report: `npm run report:architecture`

### Documentation Requirements

- Document WHY each architecture might be suitable
- Include performance data and graphs
- Do NOT commit: load test data files, temp logs
- ONLY commit: source code, benchmarks, reports''',
                    'dependencies': ['AWS account with sufficient limits', 'Benchmark tools installed'],
                    'priority': 'high',
                    'estimatedEffort': 'large',
                    'suggestedRole': 'Technical Lead'
                }
            ]
        
        # Save issues.json
        issues_data = {
            'phase_num': 1,
            'epic_num': i,
            'issues': issues,
            'generated_at': '2024-01-15T10:15:00Z'
        }
        
        with open(epic_dir / 'issues.json', 'w') as f:
            json.dump(issues_data, f, indent=2)


def get_sample_issue_with_enhanced_requirements():
    """Get a sample issue that includes all enhanced requirements."""
    return {
        'title': 'Implement product catalog API with CDK',
        'description': '''### Description

Implement RESTful API for product catalog management using AWS Lambda and API Gateway, deployed with CDK.

**Epic:** #3 [EPIC] Build Product Catalog Service''',
        'acceptanceCriteria': [
            '✅ API endpoints handle CRUD operations for products',
            '✅ Input validation and error handling implemented',
            '✅ Component can be unit tested in isolation with mocked dependencies',
            '✅ Component successfully integrates with existing ProductDB and CacheService',
            '✅ Performance: Product queries return in < 200ms for 95th percentile',
            '✅ All upstream dependencies identified and documented in README',
            '✅ Deployment commands execute successfully in the single environment',
            '✅ Documentation updated with \'why\' explanations for all design decisions'
        ],
        'technicalNotes': '''### Pre-work Investigation

Before starting implementation:
1. Run `cdk list` to discover existing stacks
   - Found: ProductDBStack, CacheStack, APIGatewayStack
2. Search for existing components: `grep -r 'ProductService' .`
   - Found: src/services/ProductService.ts (interface only)
3. Document all discovered upstream dependencies:
   - ProductDB (PostgreSQL RDS instance)
   - CacheService (Redis cluster) 
   - APIGatewayStack (shared API Gateway)

### Implementation Guidance

Implement using AWS CDK for infrastructure and Node.js/Express for the Lambda functions. Follow the existing pattern in src/services/ for consistency. Use the shared API Gateway from APIGatewayStack.

Key design decisions:
- Use Lambda for automatic scaling
- Implement caching layer for frequently accessed products
- Use DynamoDB for product metadata, S3 for images

### Deployment Instructions

**Environment:** Single environment only (no dev/staging/prod)

1. Run unit tests: `npm test src/services/ProductCatalogAPI.test.ts`
2. Run integration tests: `npm run test:integration -- --grep "Product Catalog"`
3. Deploy to AWS: `cdk deploy ProductCatalogStack --require-approval never`
4. Verify deployment: `aws cloudformation describe-stacks --stack-name ProductCatalogStack`
5. Test API: `curl -X GET https://api.domain.com/products`

### Documentation Requirements

- Every function/class must have a docstring explaining WHY it exists
- Update README.md with:
  - New API endpoints and their purpose
  - Setup steps for local development
  - Environment variables required
- Update API documentation with new endpoints
- Do NOT commit: .env files, test databases, debug logs, experimental lambdas
- ONLY commit: source code, tests, documentation, CDK templates''',
        'dependencies': [
            'ProductDBStack must be deployed',
            'CacheStack must be running',
            'API Gateway custom domain configured'
        ],
        'priority': 'high',
        'estimatedEffort': 'large',
        'suggestedRole': 'Backend Developer'
    }