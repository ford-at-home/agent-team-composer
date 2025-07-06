import { promises as fs } from 'fs';
import { ProjectSummary } from '../types';

export class ReadmeParser {
  /**
   * Parse README content and extract project information
   */
  async parse(content: string): Promise<{
    title: string;
    description: string;
    domain: string;
    features: string[];
    techStack: string[];
    complexity: 'simple' | 'moderate' | 'complex';
    userTypes: string[];
    integrations: string[];
  }> {
    return {
      title: this.extractTitle(content),
      description: this.extractDescription(content),
      domain: this.identifyDomain(content),
      features: this.extractFeatures(content),
      techStack: this.extractTechStack(content),
      complexity: this.assessComplexity(content),
      userTypes: this.identifyUserTypes(content),
      integrations: this.identifyIntegrations(content)
    };
  }

  private extractTitle(content: string): string {
    const titleMatch = content.match(/^#\s+(.+?)$/m);
    return titleMatch ? titleMatch[1].trim() : 'Untitled Project';
  }

  private extractDescription(content: string): string {
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
    
    return description.trim() || 'No description provided';
  }

  private extractFeatures(content: string): string[] {
    const features: string[] = [];
    const featurePatterns = [
      /## Features?\n((?:[-*] .+?\n)+)/i,
      /## What (does|can) .+?\n((?:[-*] .+?\n)+)/i,
      /## Functionality\n((?:[-*] .+?\n)+)/i,
      /## Key Features?\n((?:[-*] .+?\n)+)/i
    ];

    for (const pattern of featurePatterns) {
      const match = content.match(pattern);
      if (match) {
        const featureList = match[match.length - 1];
        features.push(...featureList.split('\n')
          .filter(line => line.trim().match(/^[-*]/))
          .map(line => line.trim().replace(/^[-*]\s+/, '')));
        break;
      }
    }

    return features;
  }

  private extractTechStack(content: string): string[] {
    const techStack: string[] = [];
    const techPatterns = [
      /## Tech(?:nology)? Stack\n((?:[-*] .+?\n)+)/i,
      /## Built With\n((?:[-*] .+?\n)+)/i,
      /## Technologies\n((?:[-*] .+?\n)+)/i
    ];

    for (const pattern of techPatterns) {
      const match = content.match(pattern);
      if (match) {
        techStack.push(...match[1].split('\n')
          .filter(line => line.trim().match(/^[-*]/))
          .map(line => line.trim().replace(/^[-*]\s+/, '')));
        break;
      }
    }

    // Also look for common tech keywords throughout
    const techKeywords = [
      'React', 'Vue', 'Angular', 'Node.js', 'Express', 'Django', 'Flask',
      'PostgreSQL', 'MongoDB', 'MySQL', 'Redis', 'Docker', 'Kubernetes',
      'AWS', 'Azure', 'GCP', 'TypeScript', 'JavaScript', 'Python', 'Java',
      'Go', 'Rust', 'GraphQL', 'REST API', 'WebSocket', 'gRPC'
    ];

    techKeywords.forEach(tech => {
      if (content.includes(tech) && !techStack.includes(tech)) {
        techStack.push(tech);
      }
    });

    return techStack;
  }

  private assessComplexity(content: string): 'simple' | 'moderate' | 'complex' {
    let score = 0;

    // Feature count
    const features = this.extractFeatures(content);
    if (features.length > 10) score += 3;
    else if (features.length > 5) score += 2;
    else if (features.length > 0) score += 1;

    // Tech stack diversity
    const techStack = this.extractTechStack(content);
    if (techStack.length > 8) score += 3;
    else if (techStack.length > 4) score += 2;
    else if (techStack.length > 0) score += 1;

    // Keywords indicating complexity
    const complexityKeywords = [
      'microservices', 'distributed', 'scalable', 'enterprise',
      'real-time', 'machine learning', 'AI', 'blockchain',
      'multi-tenant', 'high availability', 'load balancing'
    ];

    complexityKeywords.forEach(keyword => {
      if (content.toLowerCase().includes(keyword.toLowerCase())) {
        score += 1;
      }
    });

    // Integration count
    const integrations = this.identifyIntegrations(content);
    if (integrations.length > 5) score += 2;
    else if (integrations.length > 2) score += 1;

    // Determine complexity
    if (score >= 8) return 'complex';
    if (score >= 4) return 'moderate';
    return 'simple';
  }

  private identifyDomain(content: string): string {
    const domainPatterns = {
      'e-commerce': /e-?commerce|shop|store|cart|checkout|payment|product catalog/i,
      'social-media': /social|feed|post|comment|like|follow|share|profile/i,
      'productivity': /task|todo|project|manage|workflow|collaborate|team/i,
      'healthcare': /health|medical|patient|doctor|appointment|prescription/i,
      'education': /learn|course|student|teacher|quiz|lesson|curriculum/i,
      'finance': /finance|bank|payment|transaction|wallet|budget|invoice/i,
      'entertainment': /video|music|stream|media|content|playlist|watch/i,
      'communication': /chat|message|call|video conference|email|notification/i,
      'analytics': /analytics|dashboard|metric|report|visualization|insight/i,
      'devtools': /developer|api|sdk|cli|debug|deploy|monitor|log/i,
      'iot': /iot|sensor|device|embedded|arduino|raspberry|mqtt/i,
      'gaming': /game|player|score|level|achievement|multiplayer/i
    };

    const scores: Record<string, number> = {};

    for (const [domain, pattern] of Object.entries(domainPatterns)) {
      const matches = content.match(pattern);
      if (matches) {
        scores[domain] = matches.length;
      }
    }

    // Find domain with highest score
    let maxScore = 0;
    let detectedDomain = 'general';

    for (const [domain, score] of Object.entries(scores)) {
      if (score > maxScore) {
        maxScore = score;
        detectedDomain = domain;
      }
    }

    return detectedDomain;
  }

  private identifyUserTypes(content: string): string[] {
    const userTypes: string[] = [];
    const userPatterns = {
      'developers': /developer|programmer|engineer|coder|api user/i,
      'administrators': /admin|administrator|operator|devops/i,
      'end-users': /user|customer|client|consumer|visitor/i,
      'business-users': /business|manager|executive|stakeholder/i,
      'analysts': /analyst|data scientist|researcher/i,
      'designers': /designer|ux|ui|creative/i
    };

    for (const [userType, pattern] of Object.entries(userPatterns)) {
      if (pattern.test(content)) {
        userTypes.push(userType);
      }
    }

    return userTypes.length > 0 ? userTypes : ['end-users'];
  }

  private identifyIntegrations(content: string): string[] {
    const integrations: string[] = [];
    const integrationPatterns = [
      'GitHub', 'GitLab', 'Bitbucket', 'Slack', 'Discord', 'Teams',
      'Jira', 'Trello', 'Asana', 'Stripe', 'PayPal', 'Square',
      'AWS', 'Azure', 'Google Cloud', 'Twilio', 'SendGrid', 'Mailgun',
      'OAuth', 'SAML', 'LDAP', 'Salesforce', 'HubSpot', 'Zendesk',
      'Datadog', 'New Relic', 'Sentry', 'Prometheus', 'Grafana'
    ];

    integrationPatterns.forEach(integration => {
      if (content.includes(integration)) {
        integrations.push(integration);
      }
    });

    return integrations;
  }
}

export async function parseReadme(content: string): Promise<ProjectSummary & {
  features: string[];
  techStack: string[];
  complexity: 'simple' | 'moderate' | 'complex';
  userTypes: string[];
  integrations: string[];
}> {
  const parser = new ReadmeParser();
  const parsed = await parser.parse(content);
  
  // Get repository info from git if available
  let repository = 'unknown/unknown';
  let branch = 'main';
  
  try {
    const { execSync } = require('child_process');
    const remoteUrl = execSync('git config --get remote.origin.url', { encoding: 'utf8' }).trim();
    
    // Extract owner/repo from various Git URL formats
    const match = remoteUrl.match(/(?:git@|https:\/\/)(?:github\.com)[\/:](.+?)(?:\.git)?$/);
    if (match) {
      repository = match[1];
    }
    
    branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
  } catch (error) {
    // Ignore git errors, use defaults
  }
  
  return {
    title: parsed.title,
    description: parsed.description,
    domain: parsed.domain,
    repository,
    branch,
    features: parsed.features,
    techStack: parsed.techStack,
    complexity: parsed.complexity,
    userTypes: parsed.userTypes,
    integrations: parsed.integrations
  };
}