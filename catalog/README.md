# Agent Catalog - Dynamic Product Roadmap Generator

Transform any README.md into a comprehensive development roadmap with autonomous agent teams automatically assigned to handle every aspect of product development.

## Overview

This repository contains two powerful tools that work together to automate product development planning:

1. **Product Lifecycle Agent Role Catalog**: Defines 25+ specialized agent roles across 8 development phases
2. **README Roadmap Generator**: Analyzes README files to create detailed roadmaps and GitHub issues

## Features

### 🤖 Agent Role Catalog
- **25+ Specialized Roles**: From Market Research Analyst to Site Reliability Engineer
- **8 Lifecycle Phases**: Complete coverage from Discovery to Enhancement
- **YAML Specifications**: Each role has detailed capabilities, inputs, outputs, and success criteria
- **Issue Mapping**: Automatic role assignment based on GitHub issue types
- **Orchestration Ready**: Designed for autonomous agent coordination

### 📋 Dynamic Roadmap Generation
- **README Analysis**: Extracts project vision, features, tech stack, and complexity
- **Intelligent Planning**: Maps requirements to appropriate lifecycle phases
- **GitHub Issues**: Generates complete issue templates with labels and milestones
- **Team Composition**: Automatically determines required agent roles
- **Timeline Estimation**: Calculates realistic project timelines

## Quick Start

### Generate a Roadmap

```bash
# Install dependencies
npm install

# Generate roadmap from README
node readme-roadmap-generator.js example-readme.md ./output

# View generated files
ls ./output/
# -> roadmap.json, github-issues.json, summary.md
```

### Example Output

For a project management platform README, the generator produces:
- **Timeline**: 20 weeks
- **Issues**: 22 detailed GitHub issues
- **Team**: 2+ specialized agent roles
- **Phases**: 8 development phases with clear deliverables

## How It Works

### 1. README Analysis
The generator analyzes README content to extract:
- **Project Title & Description**
- **Features & Functionality**
- **Technology Stack**
- **User Types & Integrations**
- **Complexity Assessment**
- **Domain Classification**

### 2. Roadmap Generation
Based on the analysis, it generates:
- **Required Phases**: Selects relevant lifecycle phases
- **Phase Issues**: Creates specific tasks for each phase
- **Role Assignment**: Maps issues to agent roles
- **Timeline Calculation**: Estimates realistic timelines

### 3. Output Generation
Produces three output files:
- **`roadmap.json`**: Complete structured roadmap
- **`github-issues.json`**: Ready-to-import GitHub issues
- **`summary.md`**: Human-readable project overview

## Agent Role Catalog

### Research & Analysis
- **Market Research Analyst**: Conducts market research and competitive analysis
- **User Research Specialist**: Performs user interviews and creates personas

### Product Definition
- **Product Requirements Author**: Creates comprehensive PRDs and user stories
- **UI/UX Designer**: Designs wireframes, mockups, and user interfaces

### Architecture & Planning
- **System Architect**: Designs scalable system architecture
- **Sprint Planner**: Creates actionable sprint plans and capacity planning

### Implementation
- **Frontend Developer**: Implements responsive UI components
- **Backend Developer**: Builds secure and scalable APIs
- **Database Engineer**: Designs efficient schemas and queries
- **DevOps Engineer**: Implements CI/CD and infrastructure automation

### Quality Assurance
- **Test Engineer**: Creates comprehensive test plans and automation
- **Security Auditor**: Identifies vulnerabilities and ensures compliance
- **Performance Tester**: Validates system performance and optimization

### Release & Deployment
- **Release Manager**: Coordinates deployments with minimal risk
- **Technical Writer**: Creates clear documentation for all audiences

### Monitoring & Feedback
- **Analytics Engineer**: Implements tracking and generates insights
- **Site Reliability Engineer**: Ensures system reliability and incident response

### Enhancement & Iteration
- **Refactoring Specialist**: Improves code quality and maintainability
- **Feature Enhancement Developer**: Implements user feedback-driven improvements

## File Structure

```
agent-catalog/
├── product-lifecycle-agent-roles.md     # Complete agent role catalog
├── readme-roadmap-generator.js          # Main generator script
├── example-readme.md                    # Sample README for testing
├── demo-output/                         # Generated example output
│   ├── roadmap.json                     # Structured roadmap data
│   ├── github-issues.json               # GitHub issues ready for import
│   └── summary.md                       # Human-readable summary
└── README.md                           # This documentation
```

## Usage Examples

### Basic Usage
```bash
node readme-roadmap-generator.js path/to/README.md ./output
```

### Programmatic Usage
```javascript
const ReadmeRoadmapGenerator = require('./readme-roadmap-generator');

const generator = new ReadmeRoadmapGenerator();
const result = generator.generate('README.md', { outputDir: './output' });

console.log(`Generated ${result.roadmap.totalIssues} issues for ${result.roadmap.project}`);
```

## Configuration

The generator uses the agent catalog to determine:
- **Phase Selection**: Which lifecycle phases are needed
- **Issue Generation**: What tasks are required per phase
- **Role Assignment**: Which agents handle which issues
- **Timeline Estimation**: Realistic project duration

## Integration

### GitHub Integration
Import generated issues directly into GitHub:
```bash
# Using GitHub CLI
gh issue create --title "Market research for e-commerce domain" \
  --body-file ./output/github-issues.json
```

### Agent Orchestration
Use the catalog with orchestration systems:
```javascript
// Spawn agents based on team composition
result.roadmap.teamComposition.forEach(role => {
  orchestrator.spawnAgent(role.id, role.capabilities);
});
```

## Customization

### Adding Agent Roles
1. Define role specification in YAML format
2. Add to appropriate phase section in catalog
3. Update issue-to-role mappings

### Modifying Analysis
Extend the README analysis by:
- Adding new extraction patterns
- Updating complexity assessment
- Expanding domain classification

### Custom Issue Templates
Modify issue generation logic to:
- Add custom acceptance criteria
- Include additional metadata
- Integrate with specific tools

## Generated Output Format

### Roadmap Structure
```json
{
  "project": "Project Name",
  "complexity": "complex",
  "domain": "e-commerce", 
  "phases": [...],
  "teamComposition": [...],
  "estimatedTimeline": {...},
  "totalIssues": 22
}
```

### GitHub Issue Format
```json
{
  "title": "Issue Title",
  "body": "Detailed description with acceptance criteria",
  "labels": ["priority", "category", "phase"],
  "milestone": "Phase Name"
}
```

## Example: TaskFlow Platform

Input: README for project management platform
Output:
- **8 Phases**: Discovery through Enhancement
- **22 Issues**: Comprehensive development tasks
- **20 Week Timeline**: Realistic project duration
- **2+ Agent Roles**: Specialized team composition

## Contributing

1. **Extend Agent Catalog**: Add new roles or refine existing ones
2. **Improve Analysis**: Enhance README parsing and extraction
3. **Add Templates**: Create issue templates for specific domains
4. **Build Integrations**: Connect with orchestration platforms

## Future Enhancements

- **Real-time Collaboration**: Live roadmap updates during development
- **Agent Performance Tracking**: Monitor role effectiveness
- **Domain-Specific Catalogs**: Specialized roles for different industries
- **Visual Roadmap UI**: Interactive roadmap visualization
- **Integration APIs**: Connect with popular project management tools

---

Transform your README into a complete development roadmap with autonomous agent teams ready to deliver your product vision.