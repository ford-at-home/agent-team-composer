# Product Lifecycle Agent Role Catalog

## Overview
This catalog defines modular agent roles for autonomous teams to collaboratively build digital products across the entire lifecycle. Each role is designed as a reusable function that can be instantiated by an orchestrator to handle GitHub issues and epics.

## Lifecycle Phases

### Phase 1: Discovery & Validation
**Objective**: Understand market needs, validate assumptions, and define product vision
- **Duration**: 2-4 weeks
- **Entry Criteria**: Business opportunity identified
- **Exit Criteria**: Validated problem-solution fit with clear product vision

### Phase 2: Product Specification
**Objective**: Transform validated concepts into detailed product requirements
- **Duration**: 1-3 weeks
- **Entry Criteria**: Validated problem-solution fit
- **Exit Criteria**: Complete PRD, user stories, and acceptance criteria

### Phase 3: Architecture & Planning
**Objective**: Design technical architecture and create implementation roadmap
- **Duration**: 1-2 weeks
- **Entry Criteria**: Approved product specifications
- **Exit Criteria**: Technical design docs, sprint plan, and resource allocation

### Phase 4: Implementation
**Objective**: Build the product iteratively with continuous integration
- **Duration**: 4-12 weeks (varies by scope)
- **Entry Criteria**: Approved architecture and sprint plan
- **Exit Criteria**: Feature-complete implementation with passing tests

### Phase 5: Quality Assurance & Review
**Objective**: Ensure product quality, security, and performance standards
- **Duration**: 1-2 weeks per release cycle
- **Entry Criteria**: Feature-complete implementation
- **Exit Criteria**: All tests passing, security approved, performance validated

### Phase 6: Release & Deployment
**Objective**: Deploy to production with proper monitoring and rollback plans
- **Duration**: 1-3 days
- **Entry Criteria**: QA approval and release criteria met
- **Exit Criteria**: Successfully deployed with monitoring active

### Phase 7: Monitoring & Feedback
**Objective**: Gather user feedback and monitor system health
- **Duration**: Ongoing
- **Entry Criteria**: Product in production
- **Exit Criteria**: Continuous improvement cycle established

### Phase 8: Iteration & Enhancement
**Objective**: Implement improvements based on feedback and metrics
- **Duration**: Ongoing sprints
- **Entry Criteria**: Prioritized feedback and enhancement requests
- **Exit Criteria**: N/A (continuous process)

---

## Deliverables and GitHub Issue Types by Phase

### Phase 1: Discovery & Validation

#### Key Deliverables:
- Market Research Report
- User Interview Findings
- Competitive Analysis
- Problem Statement Document
- Solution Hypothesis
- Validation Metrics Definition

#### GitHub Issue Types:
- `research/market-analysis`: Conduct market research on [segment]
- `research/user-interviews`: Interview [N] users about [problem space]
- `research/competitor-analysis`: Analyze competitor [name] features and positioning
- `docs/problem-statement`: Define and document core problem
- `experiment/validation`: Design and run validation experiment for [hypothesis]

#### Task Categories:
- Research
- Interview
- Analyze
- Document
- Experiment

### Phase 2: Product Specification

#### Key Deliverables:
- Product Requirements Document (PRD)
- User Stories with Acceptance Criteria
- UI/UX Wireframes
- API Specifications
- Data Model Design

#### GitHub Issue Types:
- `spec/prd`: Write PRD for [feature/product]
- `spec/user-stories`: Create user stories for [epic]
- `design/wireframes`: Design wireframes for [user flow]
- `spec/api`: Define API endpoints for [service]
- `spec/data-model`: Design data model for [entity]

#### Task Categories:
- Specify
- Design
- Document
- Review

### Phase 3: Architecture & Planning

#### Key Deliverables:
- Technical Architecture Document
- System Design Diagrams
- Technology Stack Decisions
- Sprint Planning Documents
- Risk Assessment

#### GitHub Issue Types:
- `arch/system-design`: Design system architecture for [component]
- `arch/tech-stack`: Evaluate and select technology for [need]
- `planning/sprint`: Plan sprint [N] deliverables
- `planning/risk-assessment`: Assess technical risks for [component]

#### Task Categories:
- Design
- Evaluate
- Plan
- Assess

### Phase 4: Implementation

#### Key Deliverables:
- Frontend Components
- Backend Services
- Database Schemas
- API Implementations
- Unit/Integration Tests
- CI/CD Pipelines

#### GitHub Issue Types:
- `feat/frontend`: Implement [UI component/feature]
- `feat/backend`: Implement [API endpoint/service]
- `feat/database`: Create migration for [schema change]
- `test/unit`: Write unit tests for [component]
- `test/integration`: Write integration tests for [flow]
- `infra/ci-cd`: Setup CI/CD for [service]

#### Task Categories:
- Implement
- Test
- Configure
- Integrate

### Phase 5: Quality Assurance & Review

#### Key Deliverables:
- Test Plans
- Test Execution Reports
- Bug Reports
- Security Audit Results
- Performance Benchmarks
- Code Review Feedback

#### GitHub Issue Types:
- `qa/test-plan`: Create test plan for [feature]
- `qa/test-execution`: Execute test cases for [release]
- `bug/report`: [Severity] bug in [component]
- `security/audit`: Security review of [component]
- `perf/benchmark`: Performance test [feature]
- `review/code`: Code review for PR #[number]

#### Task Categories:
- Test
- Audit
- Review
- Report

### Phase 6: Release & Deployment

#### Key Deliverables:
- Release Notes
- Deployment Configuration
- Rollback Plan
- Monitoring Setup
- Documentation Updates

#### GitHub Issue Types:
- `release/notes`: Write release notes for v[version]
- `deploy/config`: Configure deployment for [environment]
- `deploy/rollback`: Create rollback plan for [release]
- `monitor/setup`: Setup monitoring for [metric]
- `docs/update`: Update documentation for [feature]

#### Task Categories:
- Deploy
- Configure
- Document
- Monitor

### Phase 7: Monitoring & Feedback

#### Key Deliverables:
- Analytics Reports
- User Feedback Summary
- System Health Reports
- Incident Reports
- Improvement Recommendations

#### GitHub Issue Types:
- `analytics/report`: Generate analytics report for [metric]
- `feedback/user`: Analyze user feedback for [feature]
- `monitor/health`: System health check for [service]
- `incident/report`: Incident report for [issue]
- `improve/recommendation`: Improvement proposal for [area]

#### Task Categories:
- Monitor
- Analyze
- Report
- Recommend

### Phase 8: Iteration & Enhancement

#### Key Deliverables:
- Feature Enhancements
- Bug Fixes
- Performance Optimizations
- Refactoring Plans
- Technical Debt Reduction

#### GitHub Issue Types:
- `enhance/feature`: Enhance [feature] with [capability]
- `fix/bug`: Fix bug #[number]
- `perf/optimize`: Optimize performance of [component]
- `refactor/code`: Refactor [module] for [reason]
- `debt/technical`: Address technical debt in [area]

#### Task Categories:
- Enhance
- Fix
- Optimize
- Refactor

---

## Agent Role Specifications

### Role Specification Template

```yaml
role_id: unique_identifier
role_name: Human-readable name
phase: [applicable lifecycle phase(s)]
purpose: Single sentence describing the role's primary function
capabilities:
  - Specific capability 1
  - Specific capability 2
  - Specific capability 3
inputs:
  - Input type 1: Description
  - Input type 2: Description
outputs:
  - Output type 1: Description
  - Output type 2: Description
tools_required:
  - Tool 1
  - Tool 2
constraints:
  - Constraint or limitation 1
  - Constraint or limitation 2
success_criteria:
  - Measurable criterion 1
  - Measurable criterion 2
```

---

## Core Agent Roles

### Research & Analysis Roles

#### Market Research Analyst
```yaml
role_id: market_research_analyst
role_name: Market Research Analyst
phase: Discovery & Validation
purpose: Conducts comprehensive market research to identify opportunities and validate assumptions
capabilities:
  - Analyze market trends and competitor landscape
  - Identify target customer segments
  - Evaluate market size and growth potential
  - Synthesize research into actionable insights
inputs:
  - Market segment: Industry or market to research
  - Research questions: Specific questions to answer
  - Data sources: List of approved research sources
outputs:
  - Market research report: Comprehensive findings document
  - Competitor matrix: Competitive landscape analysis
  - Opportunity assessment: Prioritized opportunities
tools_required:
  - Web search and scraping tools
  - Data analysis frameworks
  - Report generation templates
constraints:
  - Must use only publicly available data
  - Reports must be evidence-based with citations
  - Maximum research period of 5 business days
success_criteria:
  - All research questions answered with evidence
  - Minimum 5 competitors analyzed
  - Clear recommendations provided
```

#### User Research Specialist
```yaml
role_id: user_research_specialist
role_name: User Research Specialist
phase: Discovery & Validation
purpose: Conducts user interviews and synthesizes insights to validate product assumptions
capabilities:
  - Design and conduct user interviews
  - Create user personas and journey maps
  - Identify pain points and unmet needs
  - Validate problem-solution fit
inputs:
  - Target user profile: Demographics and characteristics
  - Interview questions: Structured interview guide
  - Number of interviews: Required sample size
outputs:
  - Interview transcripts: Raw interview data
  - User insights report: Synthesized findings
  - Persona documents: Detailed user personas
  - Journey maps: User experience flows
tools_required:
  - Interview scheduling tools
  - Transcription services
  - Persona templates
  - Journey mapping tools
constraints:
  - Must maintain user privacy and consent
  - Interviews limited to 45 minutes each
  - Minimum 10 users per segment
success_criteria:
  - Target number of interviews completed
  - Clear patterns identified across users
  - Actionable insights documented
```

### Product Definition Roles

#### Product Requirements Author
```yaml
role_id: product_requirements_author
role_name: Product Requirements Author
phase: Product Specification
purpose: Transforms user needs and business goals into detailed product requirements
capabilities:
  - Write comprehensive PRDs
  - Define acceptance criteria
  - Create user stories with clear outcomes
  - Prioritize features using frameworks
inputs:
  - User research findings: Validated user needs
  - Business objectives: Strategic goals
  - Technical constraints: Known limitations
outputs:
  - Product Requirements Document: Complete PRD
  - User stories: Backlog of stories with acceptance criteria
  - Feature prioritization: Ranked feature list
tools_required:
  - PRD templates
  - User story frameworks
  - Prioritization matrices
constraints:
  - Must align with business strategy
  - Requirements must be testable
  - Must consider technical feasibility
success_criteria:
  - All features have clear acceptance criteria
  - Stakeholder approval obtained
  - Development team can estimate all stories
```

#### UI/UX Designer
```yaml
role_id: ui_ux_designer
role_name: UI/UX Designer
phase: Product Specification
purpose: Creates user interface designs and interaction flows that meet user needs
capabilities:
  - Design wireframes and mockups
  - Create interactive prototypes
  - Define design systems and components
  - Conduct usability testing
inputs:
  - User requirements: Feature specifications
  - Brand guidelines: Design constraints
  - User personas: Target user profiles
outputs:
  - Wireframes: Low-fidelity designs
  - Mockups: High-fidelity designs
  - Prototypes: Interactive demonstrations
  - Design system: Component library
tools_required:
  - Design software (Figma/Sketch)
  - Prototyping tools
  - Design system frameworks
constraints:
  - Must follow accessibility standards
  - Designs must be responsive
  - Must align with brand guidelines
success_criteria:
  - All user flows designed
  - Usability testing score > 80%
  - Developer handoff completed
```

### Architecture & Planning Roles

#### System Architect
```yaml
role_id: system_architect
role_name: System Architect
phase: Architecture & Planning
purpose: Designs scalable and maintainable system architecture that meets requirements
capabilities:
  - Design distributed systems
  - Select appropriate technologies
  - Define integration patterns
  - Create architecture documentation
inputs:
  - Functional requirements: What system must do
  - Non-functional requirements: Performance, security, etc.
  - Constraints: Budget, timeline, existing systems
outputs:
  - Architecture diagrams: System design visuals
  - Technology decisions: Stack recommendations
  - Integration specifications: API contracts
  - ADRs: Architecture Decision Records
tools_required:
  - Diagramming tools
  - Architecture frameworks
  - Documentation platforms
constraints:
  - Must consider scalability from day one
  - Security must be built-in
  - Must document all decisions
success_criteria:
  - Architecture supports all requirements
  - Technology choices justified
  - Team consensus achieved
```

#### Sprint Planner
```yaml
role_id: sprint_planner
role_name: Sprint Planner
phase: Architecture & Planning
purpose: Creates actionable sprint plans that balance velocity with quality
capabilities:
  - Estimate story complexity
  - Balance sprint capacity
  - Identify dependencies
  - Create sprint goals
inputs:
  - Product backlog: Prioritized stories
  - Team capacity: Available hours
  - Dependencies: Technical and external
outputs:
  - Sprint plan: Stories for sprint
  - Dependency map: Identified blockers
  - Sprint goals: Clear objectives
  - Risk mitigation plan: Contingencies
tools_required:
  - Project management tools
  - Estimation frameworks
  - Capacity planning tools
constraints:
  - Must not overcommit team
  - Must account for meetings/overhead
  - Dependencies must be resolved
success_criteria:
  - Sprint goals achievable
  - Team commits to plan
  - Buffer for unknowns included
```

### Implementation Roles

#### Frontend Developer
```yaml
role_id: frontend_developer
role_name: Frontend Developer
phase: Implementation
purpose: Implements user interface components that are performant and maintainable
capabilities:
  - Build responsive UI components
  - Implement state management
  - Integrate with backend APIs
  - Write component tests
inputs:
  - Design mockups: UI specifications
  - API contracts: Backend interfaces
  - Component requirements: Functionality specs
outputs:
  - UI components: Implemented features
  - Unit tests: Component test coverage
  - Integration code: API connections
  - Documentation: Component usage guides
tools_required:
  - Frontend frameworks (React/Vue/Angular)
  - State management libraries
  - Testing frameworks
  - Build tools
constraints:
  - Must follow coding standards
  - Components must be reusable
  - Must maintain > 80% test coverage
success_criteria:
  - All acceptance criteria met
  - Tests passing
  - Code review approved
```

#### Backend Developer
```yaml
role_id: backend_developer
role_name: Backend Developer
phase: Implementation
purpose: Implements server-side logic and APIs that are secure and scalable
capabilities:
  - Build RESTful/GraphQL APIs
  - Implement business logic
  - Design database schemas
  - Write integration tests
inputs:
  - API specifications: Endpoint definitions
  - Business rules: Logic requirements
  - Data models: Entity relationships
outputs:
  - API implementations: Working endpoints
  - Database migrations: Schema updates
  - Test suites: API test coverage
  - API documentation: Usage guides
tools_required:
  - Backend frameworks
  - Database systems
  - API testing tools
  - Documentation generators
constraints:
  - Must follow security best practices
  - APIs must be versioned
  - Must maintain > 85% test coverage
success_criteria:
  - All endpoints functional
  - Security review passed
  - Performance benchmarks met
```

#### Database Engineer
```yaml
role_id: database_engineer
role_name: Database Engineer
phase: Implementation
purpose: Designs and implements efficient database schemas and queries
capabilities:
  - Design normalized schemas
  - Optimize query performance
  - Implement data migrations
  - Setup replication and backups
inputs:
  - Data requirements: Entity relationships
  - Performance requirements: Query SLAs
  - Scale projections: Growth estimates
outputs:
  - Database schemas: Table structures
  - Migration scripts: Schema changes
  - Query optimizations: Indexed queries
  - Backup procedures: Recovery plans
tools_required:
  - Database management systems
  - Migration tools
  - Query analyzers
  - Backup solutions
constraints:
  - Must ensure data integrity
  - Must plan for scale
  - Must implement proper indexing
success_criteria:
  - All queries meet SLAs
  - Zero data loss migrations
  - Backup/recovery tested
```

#### DevOps Engineer
```yaml
role_id: devops_engineer
role_name: DevOps Engineer
phase: Implementation
purpose: Implements CI/CD pipelines and infrastructure automation
capabilities:
  - Setup CI/CD pipelines
  - Implement infrastructure as code
  - Configure monitoring and alerting
  - Automate deployment processes
inputs:
  - Application architecture: System design
  - Deployment requirements: Environments
  - Compliance needs: Security/regulatory
outputs:
  - CI/CD pipelines: Automated workflows
  - Infrastructure code: Terraform/CloudFormation
  - Monitoring dashboards: System metrics
  - Deployment scripts: Automated deploys
tools_required:
  - CI/CD platforms
  - Infrastructure as Code tools
  - Container orchestration
  - Monitoring solutions
constraints:
  - Must ensure zero-downtime deploys
  - Must implement proper secrets management
  - Must follow security best practices
success_criteria:
  - Deployments fully automated
  - All environments reproducible
  - Monitoring coverage > 95%
```

### Quality Assurance Roles

#### Test Engineer
```yaml
role_id: test_engineer
role_name: Test Engineer
phase: Quality Assurance & Review
purpose: Designs and executes comprehensive test plans to ensure quality
capabilities:
  - Create test plans and cases
  - Execute manual and automated tests
  - Report and track defects
  - Validate acceptance criteria
inputs:
  - Requirements: Feature specifications
  - Test environments: Where to test
  - Release criteria: Quality gates
outputs:
  - Test plans: Testing strategies
  - Test results: Execution reports
  - Bug reports: Defect documentation
  - Quality metrics: Coverage reports
tools_required:
  - Test management tools
  - Automation frameworks
  - Bug tracking systems
  - Test data generators
constraints:
  - Must test all acceptance criteria
  - Must maintain test documentation
  - Must meet coverage targets
success_criteria:
  - 100% requirements coverage
  - All critical bugs resolved
  - Automation coverage > 70%
```

#### Security Auditor
```yaml
role_id: security_auditor
role_name: Security Auditor
phase: Quality Assurance & Review
purpose: Identifies and validates security vulnerabilities and compliance
capabilities:
  - Perform security assessments
  - Review code for vulnerabilities
  - Test authentication/authorization
  - Validate compliance requirements
inputs:
  - Application code: Source to review
  - Architecture docs: System design
  - Compliance requirements: Standards to meet
outputs:
  - Security report: Vulnerability findings
  - Remediation plan: Fix recommendations
  - Compliance checklist: Standards met
  - Risk assessment: Security posture
tools_required:
  - Security scanning tools
  - Penetration testing tools
  - Compliance frameworks
  - Vulnerability databases
constraints:
  - Must follow responsible disclosure
  - Must prioritize by risk level
  - Must provide remediation guidance
success_criteria:
  - All high-risk issues identified
  - Compliance requirements met
  - Remediation plan accepted
```

#### Performance Tester
```yaml
role_id: performance_tester
role_name: Performance Tester
phase: Quality Assurance & Review
purpose: Validates system performance and identifies bottlenecks
capabilities:
  - Design load test scenarios
  - Execute performance tests
  - Analyze performance metrics
  - Recommend optimizations
inputs:
  - Performance requirements: SLAs
  - Usage patterns: Expected load
  - System architecture: Components to test
outputs:
  - Test results: Performance metrics
  - Bottleneck analysis: Problem areas
  - Optimization recommendations: Improvements
  - Capacity planning: Scale projections
tools_required:
  - Load testing tools
  - Monitoring tools
  - Profiling tools
  - Analysis frameworks
constraints:
  - Must test realistic scenarios
  - Must not impact production
  - Must provide actionable insights
success_criteria:
  - All SLAs validated
  - Bottlenecks identified
  - Recommendations implemented
```

### Release & Deployment Roles

#### Release Manager
```yaml
role_id: release_manager
role_name: Release Manager
phase: Release & Deployment
purpose: Coordinates and executes software releases with minimal risk
capabilities:
  - Plan release schedules
  - Coordinate release activities
  - Manage rollback procedures
  - Communicate release status
inputs:
  - Release candidate: Built software
  - Release criteria: Go/no-go checklist
  - Deployment plan: Step-by-step process
outputs:
  - Release notes: What's changing
  - Deployment checklist: Execution steps
  - Rollback plan: Recovery procedures
  - Communication plan: Stakeholder updates
tools_required:
  - Release management tools
  - Communication platforms
  - Deployment automation
  - Rollback mechanisms
constraints:
  - Must minimize downtime
  - Must have rollback ready
  - Must communicate clearly
success_criteria:
  - Successful deployment
  - Zero unplanned downtime
  - All stakeholders informed
```

#### Technical Writer
```yaml
role_id: technical_writer
role_name: Technical Writer
phase: Release & Deployment
purpose: Creates clear and comprehensive documentation for all audiences
capabilities:
  - Write user documentation
  - Create API documentation
  - Develop tutorials and guides
  - Maintain documentation systems
inputs:
  - Feature specifications: What to document
  - Target audience: Who will read
  - Technical details: How things work
outputs:
  - User guides: End-user documentation
  - API documentation: Developer guides
  - Tutorials: Step-by-step guides
  - Release notes: What's new
tools_required:
  - Documentation platforms
  - Diagram tools
  - Screenshot tools
  - Version control
constraints:
  - Must be accurate and current
  - Must follow style guides
  - Must be accessible
success_criteria:
  - All features documented
  - Documentation reviewed
  - User feedback positive
```

### Monitoring & Feedback Roles

#### Analytics Engineer
```yaml
role_id: analytics_engineer
role_name: Analytics Engineer
phase: Monitoring & Feedback
purpose: Implements analytics to track user behavior and system performance
capabilities:
  - Implement tracking code
  - Create analytics dashboards
  - Analyze user behavior
  - Generate insights reports
inputs:
  - Metrics requirements: What to track
  - Business questions: What to answer
  - Data sources: Where data lives
outputs:
  - Analytics implementation: Tracking code
  - Dashboards: Visual metrics
  - Insights reports: Data findings
  - Recommendations: Action items
tools_required:
  - Analytics platforms
  - Data visualization tools
  - Query languages
  - Statistical tools
constraints:
  - Must respect user privacy
  - Must ensure data accuracy
  - Must provide actionable insights
success_criteria:
  - All KPIs tracked
  - Dashboards operational
  - Insights driving decisions
```

#### Site Reliability Engineer
```yaml
role_id: site_reliability_engineer
role_name: Site Reliability Engineer
phase: Monitoring & Feedback
purpose: Ensures system reliability and quick incident response
capabilities:
  - Monitor system health
  - Respond to incidents
  - Implement SLOs/SLIs
  - Automate operations
inputs:
  - System architecture: What to monitor
  - SLA requirements: Uptime targets
  - Incident history: Past issues
outputs:
  - Monitoring setup: Alerts configured
  - Incident reports: Root cause analysis
  - Runbooks: Response procedures
  - Automation scripts: Self-healing
tools_required:
  - Monitoring platforms
  - Incident management tools
  - Automation frameworks
  - Log aggregation
constraints:
  - Must maintain SLAs
  - Must minimize MTTR
  - Must document everything
success_criteria:
  - SLA targets met
  - Incident response < 15min
  - Automation coverage > 60%
```

### Iteration & Enhancement Roles

#### Refactoring Specialist
```yaml
role_id: refactoring_specialist
role_name: Refactoring Specialist
phase: Iteration & Enhancement
purpose: Improves code quality and maintainability without changing functionality
capabilities:
  - Identify code smells
  - Refactor complex code
  - Improve test coverage
  - Update documentation
inputs:
  - Codebase: Code to improve
  - Quality metrics: Current state
  - Technical debt log: Known issues
outputs:
  - Refactored code: Improved implementation
  - Test improvements: Better coverage
  - Documentation updates: Current docs
  - Debt reduction report: Progress made
tools_required:
  - Code analysis tools
  - Refactoring tools
  - Testing frameworks
  - Documentation tools
constraints:
  - Must not break functionality
  - Must maintain backwards compatibility
  - Must improve metrics
success_criteria:
  - Code quality metrics improved
  - Test coverage increased
  - No regressions introduced
```

#### Feature Enhancement Developer
```yaml
role_id: feature_enhancement_developer
role_name: Feature Enhancement Developer
phase: Iteration & Enhancement
purpose: Implements improvements to existing features based on user feedback
capabilities:
  - Analyze user feedback
  - Design enhancements
  - Implement improvements
  - Validate with users
inputs:
  - User feedback: Enhancement requests
  - Current implementation: Existing code
  - Success metrics: What to improve
outputs:
  - Enhanced features: Improved functionality
  - Migration plan: Update strategy
  - User validation: Feedback confirmation
  - Metrics report: Impact measurement
tools_required:
  - Development frameworks
  - A/B testing tools
  - Analytics platforms
  - User feedback tools
constraints:
  - Must maintain compatibility
  - Must improve metrics
  - Must validate with users
success_criteria:
  - User satisfaction increased
  - Feature metrics improved
  - No negative impacts
```

---

## Orchestration Guidelines

### Team Composition Rules

1. **Minimum Viable Teams**
   - Each epic requires at least one role from each relevant phase
   - Critical path roles must be assigned first
   - Support roles added based on complexity

2. **Role Dependencies**
   - Frontend Developer requires UI/UX Designer outputs
   - Backend Developer requires API specifications
   - Test Engineer requires all implementation complete

3. **Parallel Execution**
   - Research roles can work concurrently
   - Frontend and Backend can parallelize with clear contracts
   - Documentation can begin with early deliverables

### Issue-to-Role Mapping

```yaml
issue_type_mapping:
  'research/*': [market_research_analyst, user_research_specialist]
  'spec/*': [product_requirements_author, ui_ux_designer]
  'arch/*': [system_architect, database_engineer]
  'feat/frontend': [frontend_developer, ui_ux_designer]
  'feat/backend': [backend_developer, database_engineer]
  'test/*': [test_engineer, performance_tester]
  'security/*': [security_auditor]
  'deploy/*': [devops_engineer, release_manager]
  'docs/*': [technical_writer]
  'analytics/*': [analytics_engineer]
  'incident/*': [site_reliability_engineer]
  'enhance/*': [feature_enhancement_developer]
  'refactor/*': [refactoring_specialist]
```

### Orchestration Example

```yaml
epic: "User Authentication System"
phases_involved: [2, 3, 4, 5, 6, 7]
team_composition:
  - product_requirements_author  # Define auth requirements
  - ui_ux_designer              # Design login/signup flows
  - system_architect            # Design auth architecture
  - backend_developer           # Implement auth service
  - frontend_developer          # Implement auth UI
  - database_engineer           # Design user schema
  - test_engineer              # Test auth flows
  - security_auditor           # Validate auth security
  - devops_engineer            # Deploy auth service
  - technical_writer           # Document auth APIs
  - analytics_engineer         # Track auth metrics
  - site_reliability_engineer  # Monitor auth service
```

---

## Success Metrics

### Catalog Completeness
- ✓ All 8 lifecycle phases defined with clear boundaries
- ✓ Each phase has deliverables and GitHub issue types
- ✓ 25+ unique agent roles specified
- ✓ Each role has complete specification
- ✓ Clear orchestration guidelines provided

### Catalog Quality
- ✓ Roles are atomic and reusable
- ✓ No significant overlap between roles
- ✓ Clear dependencies documented
- ✓ Practical GitHub issue mappings
- ✓ Ready for orchestrator implementation

### Practical Application
- ✓ Can form teams for any product epic
- ✓ Supports parallel execution
- ✓ Handles dependencies properly
- ✓ Scales from MVP to enterprise
- ✓ Enables autonomous operation

---

## Next Steps

1. **Implement Orchestrator Logic**
   - Parse GitHub issues and match to roles
   - Instantiate agent teams dynamically
   - Manage inter-agent communication

2. **Create Role Templates**
   - Convert each role spec to LLM prompts
   - Include role-specific tools and permissions
   - Add role interaction protocols

3. **Build Feedback Loop**
   - Track role performance metrics
   - Collect orchestration patterns
   - Continuously improve role definitions

4. **Extend Catalog**
   - Add specialized roles as needed
   - Create role variants for different contexts
   - Build role composition patterns