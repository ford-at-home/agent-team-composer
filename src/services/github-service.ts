import { Octokit } from '@octokit/rest';
import { Phase, GitHubIssue, GitHubEpic } from '../types';
import { z } from 'zod';

// Input validation schemas
const IssueSchema = z.object({
  title: z.string().min(1).max(256),
  body: z.string().max(65536),
  labels: z.array(z.string()).max(100),
  assignees: z.array(z.string()).optional()
});

const PhaseSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  roles: z.array(z.string()),
  issues: z.array(z.object({
    title: z.string(),
    description: z.string(),
    role: z.string()
  })),
  approved: z.boolean()
});

export class GitHubService {
  private octokit: Octokit;
  private owner: string;
  private repo: string;

  constructor(token?: string) {
    // Use GitHub token from environment or GitHub CLI config
    this.octokit = new Octokit({
      auth: token || process.env.GITHUB_TOKEN,
      userAgent: 'agent-team-composer/1.0.0'
    });
    
    // These will be set when creating issues
    this.owner = '';
    this.repo = '';
  }

  /**
   * Safely extract repository info from string
   */
  private parseRepository(repository: string): { owner: string; repo: string } {
    const parts = repository.split('/').filter(Boolean);
    if (parts.length !== 2) {
      throw new Error('Invalid repository format. Expected: owner/repo');
    }
    
    const [owner, repo] = parts;
    
    // Validate repository name format
    const repoNameRegex = /^[a-zA-Z0-9._-]+$/;
    if (!repoNameRegex.test(owner) || !repoNameRegex.test(repo)) {
      throw new Error('Invalid repository name format');
    }
    
    return { owner, repo };
  }

  /**
   * Sanitize text for GitHub issues
   */
  private sanitizeText(text: string): string {
    return text
      .replace(/[<>]/g, '') // Remove potential HTML
      .trim()
      .slice(0, 65536); // GitHub's max issue body length
  }

  /**
   * Create GitHub milestones from phases
   */
  async createMilestones(
    repository: string,
    phases: Phase[]
  ): Promise<{ phase: string; milestoneNumber: number }[]> {
    // Validate inputs
    const { owner, repo } = this.parseRepository(repository);
    this.owner = owner;
    this.repo = repo;

    // Validate phases
    const validatedPhases = phases
      .filter(p => p.approved)
      .map(phase => PhaseSchema.parse(phase));

    const results = [];

    try {
      // Check repository access
      await this.octokit.repos.get({ owner, repo });
    } catch (error) {
      throw new Error(`Cannot access repository ${owner}/${repo}. Please check permissions.`);
    }

    // Create milestones for each phase
    for (let i = 0; i < validatedPhases.length; i++) {
      const phase = validatedPhases[i];
      try {
        const milestoneResponse = await this.octokit.issues.createMilestone({
          owner,
          repo,
          title: this.sanitizeText(phase.title),
          description: this.sanitizeText(phase.description),
          due_on: this.calculateDueDate(i + 1), // Optional: add due dates
          state: 'open'
        });

        results.push({
          phase: phase.title,
          milestoneNumber: milestoneResponse.data.number
        });
      } catch (error) {
        // Check if milestone already exists
        const err = error as { status?: number; message?: string };
        if (err.status === 422 && err.message?.includes('already exists')) {
          console.warn(`Milestone "${phase.title}" already exists, skipping...`);
        } else {
          console.error(`Failed to create milestone: ${phase.title}`, error);
          throw error;
        }
      }
    }

    return results;
  }

  /**
   * Calculate due date for milestone (optional)
   */
  private calculateDueDate(phaseNumber: number): string | undefined {
    // Example: each phase gets 2 weeks
    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + (phaseNumber * 14));
    return dueDate.toISOString();
  }

  /**
   * Create GitHub issues from phases
   */
  async createIssuesFromPhases(
    repository: string,
    phases: Phase[],
    milestoneMap?: Map<string, number>
  ): Promise<{ phase: string; epicNumber: number; issueCount: number }[]> {
    // Validate inputs
    const { owner, repo } = this.parseRepository(repository);
    this.owner = owner;
    this.repo = repo;

    // Validate phases
    const validatedPhases = phases
      .filter(p => p.approved)
      .map(phase => {
        const parsed = PhaseSchema.parse(phase);
        return {
          ...parsed,
          id: parsed.id!,
          title: parsed.title!,
          description: parsed.description!,
          roles: parsed.roles!,
          issues: parsed.issues!,
          approved: parsed.approved!
        } as Phase;
      });

    const results = [];

    try {
      // Check repository access
      await this.octokit.repos.get({ owner, repo });
    } catch (error) {
      throw new Error(`Cannot access repository ${owner}/${repo}. Please check permissions.`);
    }

    // Create issues for each phase
    for (const phase of validatedPhases) {
      try {
        // Create epic issue
        const epicTitle = this.sanitizeText(`[Epic] ${phase.title}`);
        const epicBody = this.createEpicBody(phase);
        
        const milestoneNumber = milestoneMap?.get(phase.title);
        
        const epicResponse = await this.octokit.issues.create({
          owner,
          repo,
          title: epicTitle,
          body: epicBody,
          labels: ['epic', `phase:${phase.id}`],
          milestone: milestoneNumber // Associate epic with milestone
        });

        const epicNumber = epicResponse.data.number;

        // Create individual issues
        let issueCount = 0;
        for (const issue of phase.issues) {
          try {
            const issueTitle = this.sanitizeText(issue.title);
            const issueBody = this.createIssueBody(issue, epicNumber);
            const labels = [
              `phase:${phase.id}`,
              `role:${this.sanitizeLabel(issue.role)}`
            ];

            const milestoneNumber = milestoneMap?.get(phase.title);
            
            await this.octokit.issues.create({
              owner,
              repo,
              title: issueTitle,
              body: issueBody,
              labels,
              milestone: milestoneNumber // Associate with milestone if available
            });

            issueCount++;
          } catch (error) {
            console.error(`Failed to create issue: ${issue.title}`, error);
            // Continue with other issues
          }
        }

        results.push({
          phase: phase.title,
          epicNumber,
          issueCount
        });

      } catch (error) {
        console.error(`Failed to create epic for phase: ${phase.title}`, error);
        throw new Error(`Failed to create issues for phase ${phase.title}`);
      }
    }

    return results;
  }

  /**
   * Create epic body with proper formatting
   */
  private createEpicBody(phase: Phase): string {
    const rolesList = phase.roles.map(r => `- ${this.sanitizeText(r)}`).join('\n');
    const tasksList = phase.issues.map(i => `- [ ] ${this.sanitizeText(i.title)}`).join('\n');
    
    return this.sanitizeText(`
## ${phase.description}

### Roles
${rolesList}

### Tasks
${tasksList}

---
*This epic was generated by Agent Team Composer*
    `.trim());
  }

  /**
   * Create issue body with proper formatting
   */
  private createIssueBody(issue: any, epicNumber: number): string {
    return this.sanitizeText(`
${issue.description}

**Assigned Role:** ${issue.role}  
**Epic:** #${epicNumber}

---
*This issue was generated by Agent Team Composer and is optimized for Claude Flow SPARC agents*
    `.trim());
  }

  /**
   * Sanitize label names
   */
  private sanitizeLabel(label: string): string {
    return label
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 50); // GitHub's max label length
  }

  /**
   * Check GitHub authentication status
   */
  async checkAuthentication(): Promise<{
    authenticated: boolean;
    user?: string;
    scopes?: string[];
    error?: string;
  }> {
    try {
      const { data } = await this.octokit.users.getAuthenticated();
      
      // Check if we have required scopes
      const response = await this.octokit.request('GET /user');
      const scopes = response.headers['x-oauth-scopes']?.split(', ') || [];
      
      const hasRequiredScopes = scopes.includes('repo') || scopes.includes('public_repo');
      
      if (!hasRequiredScopes) {
        return {
          authenticated: true,
          user: data.login,
          scopes,
          error: 'Missing required GitHub scopes. Need "repo" or "public_repo" scope.'
        };
      }
      
      return {
        authenticated: true,
        user: data.login,
        scopes
      };
    } catch (error) {
      return {
        authenticated: false,
        error: 'Not authenticated with GitHub'
      };
    }
  }

  /**
   * Get rate limit status
   */
  async getRateLimit(): Promise<{
    limit: number;
    remaining: number;
    reset: Date;
  }> {
    const { data } = await this.octokit.rateLimit.get();
    return {
      limit: data.rate.limit,
      remaining: data.rate.remaining,
      reset: new Date(data.rate.reset * 1000)
    };
  }

  /**
   * Get user's repositories with write access
   */
  async getUserRepositories(): Promise<Array<{
    full_name: string;
    name: string;
    owner: { login: string };
    private: boolean;
    permissions: {
      admin: boolean;
      push: boolean;
      pull: boolean;
    };
  }>> {
    const repos = [];
    let page = 1;
    const perPage = 100;
    
    while (true) {
      const { data } = await this.octokit.repos.listForAuthenticatedUser({
        page,
        per_page: perPage,
        sort: 'updated',
        direction: 'desc'
      });
      
      if (data.length === 0) break;
      
      repos.push(...data);
      
      if (data.length < perPage) break;
      page++;
    }
    
    return repos;
  }

  /**
   * Get branches for a repository
   */
  async getRepositoryBranches(repoFullName: string): Promise<string[]> {
    const { owner, repo } = this.parseRepository(repoFullName);
    
    const branches = [];
    let page = 1;
    const perPage = 100;
    
    while (true) {
      const { data } = await this.octokit.repos.listBranches({
        owner,
        repo,
        page,
        per_page: perPage
      });
      
      if (data.length === 0) break;
      
      branches.push(...data.map(branch => branch.name));
      
      if (data.length < perPage) break;
      page++;
    }
    
    return branches;
  }
}