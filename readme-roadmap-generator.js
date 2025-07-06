#!/usr/bin/env node

/**
 * README to Roadmap Generator
 * 
 * Dynamically creates product roadmaps and agent team compositions
 * from README.md files using the Product Lifecycle Agent Role Catalog
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

class ReadmeRoadmapGenerator {
    constructor(catalogPath = './product-lifecycle-agent-roles.md') {
        this.catalog = this.loadCatalog(catalogPath);
        this.phases = this.extractPhases();
        this.roles = this.extractRoles();
        this.issueMappings = this.extractIssueMappings();
    }

    /**
     * Load and parse the agent role catalog
     */
    loadCatalog(catalogPath) {
        if (!fs.existsSync(catalogPath)) {
            throw new Error(`Catalog file not found: ${catalogPath}`);
        }
        return fs.readFileSync(catalogPath, 'utf8');
    }

    /**
     * Extract lifecycle phases from catalog
     */
    extractPhases() {
        const phasePattern = /### Phase \d+: (.+?)\n\*\*Objective\*\*: (.+?)\n- \*\*Duration\*\*: (.+?)\n- \*\*Entry Criteria\*\*: (.+?)\n- \*\*Exit Criteria\*\*: (.+?)(?=\n\n|\n###)/gs;
        const phases = [];
        let match;

        while ((match = phasePattern.exec(this.catalog)) !== null) {
            phases.push({
                name: match[1].trim(),
                objective: match[2].trim(),
                duration: match[3].trim(),
                entryCriteria: match[4].trim(),
                exitCriteria: match[5].trim()
            });
        }

        return phases;
    }

    /**
     * Extract agent roles from catalog
     */
    extractRoles() {
        const rolePattern = /```yaml\nrole_id: (.+?)\nrole_name: (.+?)\nphase: (.+?)\npurpose: (.+?)\ncapabilities:\n((?:  - .+?\n)+)inputs:\n((?:  - .+?\n)+)outputs:\n((?:  - .+?\n)+)tools_required:\n((?:  - .+?\n)+)constraints:\n((?:  - .+?\n)+)success_criteria:\n((?:  - .+?\n)+)```/gs;
        const roles = [];
        let match;

        while ((match = rolePattern.exec(this.catalog)) !== null) {
            roles.push({
                id: match[1].trim(),
                name: match[2].trim(),
                phase: match[3].trim(),
                purpose: match[4].trim(),
                capabilities: this.parseListItems(match[5]),
                inputs: this.parseListItems(match[6]),
                outputs: this.parseListItems(match[7]),
                tools: this.parseListItems(match[8]),
                constraints: this.parseListItems(match[9]),
                successCriteria: this.parseListItems(match[10])
            });
        }

        return roles;
    }

    /**
     * Extract issue-to-role mappings
     */
    extractIssueMappings() {
        const mappingPattern = /issue_type_mapping:\n((?:  '.+?': \[.+?\]\n)+)/s;
        const match = mappingPattern.exec(this.catalog);
        
        if (!match) return {};

        const mappings = {};
        const lines = match[1].split('\n').filter(line => line.trim());
        
        lines.forEach(line => {
            const lineMatch = line.match(/'(.+?)': \[(.+?)\]/);
            if (lineMatch) {
                const issueType = lineMatch[1];
                const roles = lineMatch[2].split(',').map(r => r.trim());
                mappings[issueType] = roles;
            }
        });

        return mappings;
    }

    /**
     * Parse YAML list items
     */
    parseListItems(text) {
        return text.split('\n')
            .filter(line => line.trim().startsWith('- '))
            .map(line => line.trim().substring(2));
    }

    /**
     * Analyze README content and extract product information
     */
    analyzeReadme(readmePath) {
        if (!fs.existsSync(readmePath)) {
            throw new Error(`README file not found: ${readmePath}`);
        }

        const content = fs.readFileSync(readmePath, 'utf8');
        
        return {
            title: this.extractTitle(content),
            description: this.extractDescription(content),
            features: this.extractFeatures(content),
            techStack: this.extractTechStack(content),
            installation: this.extractInstallation(content),
            usage: this.extractUsage(content),
            api: this.extractAPI(content),
            complexity: this.assessComplexity(content),
            domain: this.identifyDomain(content),
            userTypes: this.identifyUserTypes(content),
            integrations: this.identifyIntegrations(content)
        };
    }

    /**
     * Extract title from README
     */
    extractTitle(content) {
        const titleMatch = content.match(/^#\s+(.+?)$/m);
        return titleMatch ? titleMatch[1].trim() : 'Untitled Project';
    }

    /**
     * Extract description
     */
    extractDescription(content) {
        const lines = content.split('\n');
        let description = '';
        let inDescription = false;
        
        for (const line of lines) {
            if (line.match(/^#\s+/)) {
                if (inDescription) break;
                inDescription = true;
                continue;
            }
            if (line.match(/^##\s+/) && inDescription) break;
            if (inDescription && line.trim()) {
                description += line.trim() + ' ';
            }
        }
        
        return description.trim();
    }

    /**
     * Extract features
     */
    extractFeatures(content) {
        const features = [];
        const featurePatterns = [
            /## Features?\n((?:- .+?\n)+)/i,
            /## What (does|can) .+?\n((?:- .+?\n)+)/i,
            /## Functionality\n((?:- .+?\n)+)/i
        ];

        for (const pattern of featurePatterns) {
            const match = content.match(pattern);
            if (match) {
                const featureList = match[match.length - 1];
                features.push(...featureList.split('\n')
                    .filter(line => line.trim().startsWith('-'))
                    .map(line => line.trim().substring(1).trim()));
                break;
            }
        }

        return features;
    }

    /**
     * Extract technology stack
     */
    extractTechStack(content) {
        const techStack = [];
        const techPatterns = [
            /## Tech(?:nology)? Stack\n((?:- .+?\n)+)/i,
            /## Built With\n((?:- .+?\n)+)/i,
            /## Technologies\n((?:- .+?\n)+)/i
        ];

        // Common technology keywords
        const techKeywords = [
            'react', 'vue', 'angular', 'node', 'express', 'fastapi', 'django', 
            'flask', 'spring', 'rails', 'laravel', 'php', 'python', 'javascript',
            'typescript', 'java', 'go', 'rust', 'c#', 'swift', 'kotlin',
            'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'firebase'
        ];

        // Extract from dedicated sections
        for (const pattern of techPatterns) {
            const match = content.match(pattern);
            if (match) {
                const stackList = match[1];
                techStack.push(...stackList.split('\n')
                    .filter(line => line.trim().startsWith('-'))
                    .map(line => line.trim().substring(1).trim()));
                break;
            }
        }

        // Extract from content if no dedicated section
        if (techStack.length === 0) {
            const lowerContent = content.toLowerCase();
            techStack.push(...techKeywords.filter(tech => 
                lowerContent.includes(tech)
            ));
        }

        return [...new Set(techStack)]; // Remove duplicates
    }

    /**
     * Extract installation instructions
     */
    extractInstallation(content) {
        const installMatch = content.match(/## Installation\n((?:.|\n)+?)(?=\n## |$)/i);
        return installMatch ? installMatch[1].trim() : '';
    }

    /**
     * Extract usage information
     */
    extractUsage(content) {
        const usageMatch = content.match(/## Usage\n((?:.|\n)+?)(?=\n## |$)/i);
        return usageMatch ? usageMatch[1].trim() : '';
    }

    /**
     * Extract API information
     */
    extractAPI(content) {
        const apiMatch = content.match(/## API\n((?:.|\n)+?)(?=\n## |$)/i);
        return apiMatch ? apiMatch[1].trim() : '';
    }

    /**
     * Assess project complexity
     */
    assessComplexity(content) {
        let score = 0;
        const indicators = {
            simple: ['todo', 'calculator', 'hello world', 'example'],
            medium: ['dashboard', 'crud', 'blog', 'shop', 'api'],
            complex: ['platform', 'system', 'enterprise', 'microservice', 'distributed']
        };

        const lowerContent = content.toLowerCase();
        
        if (indicators.complex.some(word => lowerContent.includes(word))) score += 3;
        if (indicators.medium.some(word => lowerContent.includes(word))) score += 2;
        if (indicators.simple.some(word => lowerContent.includes(word))) score += 1;

        // Additional complexity indicators
        if (content.includes('database') || content.includes('DB')) score += 1;
        if (content.includes('authentication') || content.includes('auth')) score += 1;
        if (content.includes('API') || content.includes('api')) score += 1;
        if (content.includes('real-time') || content.includes('websocket')) score += 2;
        if (content.includes('machine learning') || content.includes('AI')) score += 2;

        if (score >= 6) return 'complex';
        if (score >= 3) return 'medium';
        return 'simple';
    }

    /**
     * Identify product domain
     */
    identifyDomain(content) {
        const domains = {
            'e-commerce': ['shop', 'store', 'cart', 'payment', 'product', 'checkout'],
            'social': ['social', 'chat', 'message', 'friend', 'post', 'feed'],
            'productivity': ['todo', 'task', 'project', 'calendar', 'note'],
            'content': ['blog', 'cms', 'article', 'content', 'publish'],
            'fintech': ['finance', 'banking', 'payment', 'wallet', 'transaction'],
            'health': ['health', 'medical', 'patient', 'doctor', 'clinic'],
            'education': ['learn', 'course', 'student', 'teacher', 'education'],
            'saas': ['platform', 'service', 'subscription', 'tenant', 'multi']
        };

        const lowerContent = content.toLowerCase();
        
        for (const [domain, keywords] of Object.entries(domains)) {
            if (keywords.some(keyword => lowerContent.includes(keyword))) {
                return domain;
            }
        }

        return 'general';
    }

    /**
     * Identify user types
     */
    identifyUserTypes(content) {
        const userTypes = [];
        const patterns = [
            /users?\s+(?:can|will|are able to)/gi,
            /for\s+(\w+)\s+(?:users?|people)/gi,
            /(\w+)\s+(?:dashboard|panel|interface)/gi
        ];

        const commonUserTypes = ['admin', 'customer', 'manager', 'student', 'teacher', 'doctor', 'patient'];
        const lowerContent = content.toLowerCase();

        commonUserTypes.forEach(type => {
            if (lowerContent.includes(type)) {
                userTypes.push(type);
            }
        });

        return [...new Set(userTypes)];
    }

    /**
     * Identify external integrations
     */
    identifyIntegrations(content) {
        const integrations = [];
        const commonIntegrations = [
            'stripe', 'paypal', 'google', 'facebook', 'twitter', 'github',
            'slack', 'discord', 'sendgrid', 'twilio', 'aws', 'firebase'
        ];

        const lowerContent = content.toLowerCase();
        
        commonIntegrations.forEach(integration => {
            if (lowerContent.includes(integration)) {
                integrations.push(integration);
            }
        });

        return integrations;
    }

    /**
     * Generate roadmap from README analysis
     */
    generateRoadmap(readmeAnalysis) {
        const roadmap = {
            project: readmeAnalysis.title,
            complexity: readmeAnalysis.complexity,
            domain: readmeAnalysis.domain,
            phases: [],
            teamComposition: [],
            estimatedTimeline: this.calculateTimeline(readmeAnalysis),
            totalIssues: 0
        };

        // Determine which phases are needed
        const requiredPhases = this.determineRequiredPhases(readmeAnalysis);
        
        requiredPhases.forEach(phaseIndex => {
            const phase = this.phases[phaseIndex];
            const phaseRoadmap = this.generatePhaseRoadmap(phase, readmeAnalysis, phaseIndex + 1);
            roadmap.phases.push(phaseRoadmap);
            roadmap.totalIssues += phaseRoadmap.issues.length;
        });

        // Generate team composition
        roadmap.teamComposition = this.generateTeamComposition(roadmap.phases);

        return roadmap;
    }

    /**
     * Determine which phases are required based on project analysis
     */
    determineRequiredPhases(analysis) {
        const phases = [];
        
        // Phase 1: Discovery & Validation (always needed for new projects)
        phases.push(0);
        
        // Phase 2: Product Specification (always needed)
        phases.push(1);
        
        // Phase 3: Architecture & Planning (needed for medium+ complexity)
        if (analysis.complexity !== 'simple') {
            phases.push(2);
        }
        
        // Phase 4: Implementation (always needed)
        phases.push(3);
        
        // Phase 5: QA & Review (always needed)
        phases.push(4);
        
        // Phase 6: Release & Deployment (always needed)
        phases.push(5);
        
        // Phase 7: Monitoring & Feedback (needed for complex projects)
        if (analysis.complexity === 'complex' || analysis.features.length > 5) {
            phases.push(6);
        }
        
        // Phase 8: Iteration & Enhancement (needed for ongoing projects)
        if (analysis.complexity !== 'simple') {
            phases.push(7);
        }
        
        return phases;
    }

    /**
     * Generate roadmap for a specific phase
     */
    generatePhaseRoadmap(phase, analysis, phaseNumber) {
        const phaseRoadmap = {
            number: phaseNumber,
            name: phase.name,
            objective: phase.objective,
            duration: phase.duration,
            issues: [],
            requiredRoles: []
        };

        // Generate issues based on phase and project analysis
        const issues = this.generatePhaseIssues(phaseNumber, analysis);
        phaseRoadmap.issues = issues;

        // Determine required roles for this phase
        const roles = this.determinePhaseRoles(issues);
        phaseRoadmap.requiredRoles = roles;

        return phaseRoadmap;
    }

    /**
     * Generate issues for a specific phase
     */
    generatePhaseIssues(phaseNumber, analysis) {
        const issues = [];

        switch (phaseNumber) {
            case 1: // Discovery & Validation
                issues.push({
                    type: 'research/market-analysis',
                    title: `Market research for ${analysis.domain} domain`,
                    description: `Analyze market opportunities and competition in the ${analysis.domain} space`,
                    priority: 'high',
                    estimatedHours: 16
                });
                
                if (analysis.userTypes.length > 0) {
                    issues.push({
                        type: 'research/user-interviews',
                        title: `User research for ${analysis.userTypes.join(', ')} personas`,
                        description: `Conduct interviews with target users: ${analysis.userTypes.join(', ')}`,
                        priority: 'high',
                        estimatedHours: 24
                    });
                }
                
                issues.push({
                    type: 'docs/problem-statement',
                    title: 'Define core problem statement',
                    description: `Document the core problem that ${analysis.title} solves`,
                    priority: 'medium',
                    estimatedHours: 8
                });
                break;

            case 2: // Product Specification
                issues.push({
                    type: 'spec/prd',
                    title: 'Create Product Requirements Document',
                    description: `Comprehensive PRD for ${analysis.title}`,
                    priority: 'high',
                    estimatedHours: 20
                });
                
                analysis.features.forEach((feature, index) => {
                    issues.push({
                        type: 'spec/user-stories',
                        title: `User stories for ${feature}`,
                        description: `Create detailed user stories and acceptance criteria for: ${feature}`,
                        priority: index < 3 ? 'high' : 'medium',
                        estimatedHours: 4
                    });
                });
                
                issues.push({
                    type: 'design/wireframes',
                    title: 'Create UI wireframes',
                    description: 'Design wireframes for main user flows',
                    priority: 'medium',
                    estimatedHours: 16
                });
                break;

            case 3: // Architecture & Planning
                issues.push({
                    type: 'arch/system-design',
                    title: 'System architecture design',
                    description: `Design scalable architecture for ${analysis.title}`,
                    priority: 'high',
                    estimatedHours: 16
                });
                
                if (analysis.techStack.length > 0) {
                    issues.push({
                        type: 'arch/tech-stack',
                        title: 'Technology stack evaluation',
                        description: `Evaluate and finalize tech stack: ${analysis.techStack.join(', ')}`,
                        priority: 'high',
                        estimatedHours: 12
                    });
                }
                
                issues.push({
                    type: 'planning/sprint',
                    title: 'Sprint planning and roadmap',
                    description: 'Create detailed implementation sprint plan',
                    priority: 'medium',
                    estimatedHours: 8
                });
                break;

            case 4: // Implementation
                // Frontend issues
                if (analysis.features.length > 0) {
                    issues.push({
                        type: 'feat/frontend',
                        title: 'Core frontend application',
                        description: 'Implement main frontend application structure',
                        priority: 'high',
                        estimatedHours: 40
                    });
                    
                    analysis.features.forEach((feature, index) => {
                        issues.push({
                            type: 'feat/frontend',
                            title: `Frontend: ${feature}`,
                            description: `Implement frontend components for: ${feature}`,
                            priority: index < 2 ? 'high' : 'medium',
                            estimatedHours: 16
                        });
                    });
                }
                
                // Backend issues
                issues.push({
                    type: 'feat/backend',
                    title: 'Core backend services',
                    description: 'Implement core backend API and services',
                    priority: 'high',
                    estimatedHours: 32
                });
                
                analysis.features.forEach((feature, index) => {
                    issues.push({
                        type: 'feat/backend',
                        title: `Backend: ${feature}`,
                        description: `Implement backend logic for: ${feature}`,
                        priority: index < 2 ? 'high' : 'medium',
                        estimatedHours: 12
                    });
                });
                
                // Database
                issues.push({
                    type: 'feat/database',
                    title: 'Database schema implementation',
                    description: 'Create and implement database schema',
                    priority: 'high',
                    estimatedHours: 16
                });
                
                // CI/CD
                issues.push({
                    type: 'infra/ci-cd',
                    title: 'CI/CD pipeline setup',
                    description: 'Setup continuous integration and deployment',
                    priority: 'medium',
                    estimatedHours: 12
                });
                break;

            case 5: // QA & Review
                issues.push({
                    type: 'test/unit',
                    title: 'Unit test suite',
                    description: 'Create comprehensive unit tests',
                    priority: 'high',
                    estimatedHours: 24
                });
                
                issues.push({
                    type: 'test/integration',
                    title: 'Integration tests',
                    description: 'Create integration test suite',
                    priority: 'high',
                    estimatedHours: 16
                });
                
                issues.push({
                    type: 'security/audit',
                    title: 'Security audit',
                    description: 'Comprehensive security review and testing',
                    priority: 'high',
                    estimatedHours: 12
                });
                
                if (analysis.complexity === 'complex') {
                    issues.push({
                        type: 'perf/benchmark',
                        title: 'Performance testing',
                        description: 'Load testing and performance optimization',
                        priority: 'medium',
                        estimatedHours: 16
                    });
                }
                break;

            case 6: // Release & Deployment
                issues.push({
                    type: 'deploy/config',
                    title: 'Production deployment',
                    description: 'Configure and execute production deployment',
                    priority: 'high',
                    estimatedHours: 8
                });
                
                issues.push({
                    type: 'monitor/setup',
                    title: 'Monitoring setup',
                    description: 'Setup monitoring and alerting systems',
                    priority: 'high',
                    estimatedHours: 12
                });
                
                issues.push({
                    type: 'docs/update',
                    title: 'Documentation update',
                    description: 'Update all user and technical documentation',
                    priority: 'medium',
                    estimatedHours: 8
                });
                break;

            case 7: // Monitoring & Feedback
                issues.push({
                    type: 'analytics/report',
                    title: 'Analytics implementation',
                    description: 'Implement user analytics and reporting',
                    priority: 'medium',
                    estimatedHours: 12
                });
                
                issues.push({
                    type: 'feedback/user',
                    title: 'User feedback system',
                    description: 'Setup user feedback collection and analysis',
                    priority: 'medium',
                    estimatedHours: 8
                });
                break;

            case 8: // Iteration & Enhancement
                issues.push({
                    type: 'enhance/feature',
                    title: 'Feature enhancement planning',
                    description: 'Plan and prioritize feature enhancements',
                    priority: 'low',
                    estimatedHours: 8
                });
                
                issues.push({
                    type: 'refactor/code',
                    title: 'Code refactoring',
                    description: 'Refactor code for maintainability',
                    priority: 'low',
                    estimatedHours: 16
                });
                break;
        }

        return issues;
    }

    /**
     * Determine required roles for a phase based on its issues
     */
    determinePhaseRoles(issues) {
        const requiredRoles = new Set();
        
        issues.forEach(issue => {
            const mappedRoles = this.issueMappings[issue.type] || [];
            mappedRoles.forEach(role => requiredRoles.add(role));
        });
        
        return Array.from(requiredRoles);
    }

    /**
     * Generate overall team composition
     */
    generateTeamComposition(phases) {
        const allRoles = new Set();
        const roleFrequency = {};
        
        phases.forEach(phase => {
            phase.requiredRoles.forEach(role => {
                allRoles.add(role);
                roleFrequency[role] = (roleFrequency[role] || 0) + 1;
            });
        });
        
        return Array.from(allRoles).map(roleId => {
            const roleSpec = this.roles.find(r => r.id === roleId);
            return {
                id: roleId,
                name: roleSpec ? roleSpec.name : roleId,
                frequency: roleFrequency[roleId],
                phase: roleSpec ? roleSpec.phase : 'Unknown'
            };
        }).sort((a, b) => b.frequency - a.frequency);
    }

    /**
     * Calculate estimated timeline
     */
    calculateTimeline(analysis) {
        const complexityMultipliers = {
            simple: 1,
            medium: 1.5,
            complex: 2.5
        };
        
        const baseWeeks = 8;
        const multiplier = complexityMultipliers[analysis.complexity] || 1;
        const featureWeeks = Math.ceil(analysis.features.length / 3);
        
        return {
            weeks: Math.ceil(baseWeeks * multiplier + featureWeeks),
            complexity: analysis.complexity,
            features: analysis.features.length
        };
    }

    /**
     * Generate GitHub issues output
     */
    generateGitHubIssues(roadmap) {
        const issues = [];
        
        roadmap.phases.forEach(phase => {
            phase.issues.forEach(issue => {
                issues.push({
                    title: issue.title,
                    body: this.formatIssueBody(issue, phase),
                    labels: this.generateIssueLabels(issue, phase),
                    assignees: [],
                    milestone: phase.name
                });
            });
        });
        
        return issues;
    }

    /**
     * Format issue body
     */
    formatIssueBody(issue, phase) {
        return `## Description
${issue.description}

## Phase
${phase.name} - ${phase.objective}

## Acceptance Criteria
- [ ] Implementation meets requirements
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code review completed

## Estimated Hours
${issue.estimatedHours}

## Required Roles
${phase.requiredRoles.map(role => `- ${role}`).join('\n')}

---
*Generated by README Roadmap Generator*`;
    }

    /**
     * Generate issue labels
     */
    generateIssueLabels(issue, phase) {
        const labels = [
            issue.priority,
            issue.type.split('/')[0], // category
            phase.name.toLowerCase().replace(/\s+/g, '-')
        ];
        
        return labels.filter(Boolean);
    }

    /**
     * Save roadmap to file
     */
    saveRoadmap(roadmap, outputPath) {
        const output = {
            metadata: {
                generatedAt: new Date().toISOString(),
                generator: 'README Roadmap Generator',
                version: '1.0.0'
            },
            roadmap
        };
        
        fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
        console.log(`Roadmap saved to: ${outputPath}`);
    }

    /**
     * Save GitHub issues to file
     */
    saveGitHubIssues(issues, outputPath) {
        fs.writeFileSync(outputPath, JSON.stringify(issues, null, 2));
        console.log(`GitHub issues saved to: ${outputPath}`);
    }

    /**
     * Main generation function
     */
    generate(readmePath, options = {}) {
        console.log('🔍 Analyzing README...');
        const analysis = this.analyzeReadme(readmePath);
        
        console.log('📋 Generating roadmap...');
        const roadmap = this.generateRoadmap(analysis);
        
        console.log('📝 Generating GitHub issues...');
        const issues = this.generateGitHubIssues(roadmap);
        
        // Save outputs
        if (options.outputDir) {
            const outputDir = options.outputDir;
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }
            
            this.saveRoadmap(roadmap, path.join(outputDir, 'roadmap.json'));
            this.saveGitHubIssues(issues, path.join(outputDir, 'github-issues.json'));
            
            // Generate summary
            this.generateSummary(roadmap, analysis, path.join(outputDir, 'summary.md'));
        }
        
        return {
            analysis,
            roadmap,
            issues
        };
    }

    /**
     * Generate human-readable summary
     */
    generateSummary(roadmap, analysis, outputPath) {
        const summary = `# ${roadmap.project} - Development Roadmap

## Project Overview
- **Domain**: ${analysis.domain}
- **Complexity**: ${analysis.complexity}
- **Estimated Timeline**: ${roadmap.estimatedTimeline.weeks} weeks
- **Total Issues**: ${roadmap.totalIssues}
- **Team Size**: ${roadmap.teamComposition.length} roles

## Project Analysis
- **Features**: ${analysis.features.length} identified
- **Tech Stack**: ${analysis.techStack.join(', ') || 'Not specified'}
- **User Types**: ${analysis.userTypes.join(', ') || 'General users'}
- **Integrations**: ${analysis.integrations.join(', ') || 'None identified'}

## Development Phases

${roadmap.phases.map(phase => `### ${phase.number}. ${phase.name}
**Objective**: ${phase.objective}
**Duration**: ${phase.duration}
**Issues**: ${phase.issues.length}
**Required Roles**: ${phase.requiredRoles.join(', ')}

#### Key Issues:
${phase.issues.slice(0, 3).map(issue => `- ${issue.title} (${issue.priority} priority)`).join('\n')}
${phase.issues.length > 3 ? `- ... and ${phase.issues.length - 3} more issues` : ''}
`).join('\n')}

## Team Composition

${roadmap.teamComposition.map(role => `### ${role.name}
- **Usage**: ${role.frequency} phase(s)
- **Phase**: ${role.phase}
`).join('\n')}

## Next Steps

1. Review and customize the generated roadmap
2. Create GitHub issues from \`github-issues.json\`
3. Form agent teams based on team composition
4. Begin Phase 1: ${roadmap.phases[0]?.name || 'Discovery & Validation'}

---
*Generated on ${new Date().toLocaleDateString()} by README Roadmap Generator*
`;

        fs.writeFileSync(outputPath, summary);
        console.log(`Summary saved to: ${outputPath}`);
    }
}

// CLI Usage
if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.log('Usage: node readme-roadmap-generator.js <README_PATH> [OUTPUT_DIR]');
        process.exit(1);
    }

    const readmePath = args[0];
    const outputDir = args[1] || './output';

    try {
        const generator = new ReadmeRoadmapGenerator();
        const result = generator.generate(readmePath, { outputDir });
        
        console.log('\n✅ Generation complete!');
        console.log(`📊 Project: ${result.roadmap.project}`);
        console.log(`⏱️  Timeline: ${result.roadmap.estimatedTimeline.weeks} weeks`);
        console.log(`📋 Issues: ${result.roadmap.totalIssues}`);
        console.log(`👥 Team: ${result.roadmap.teamComposition.length} roles`);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    }
}

module.exports = ReadmeRoadmapGenerator;