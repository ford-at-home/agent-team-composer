import { describe, it, expect, vi, beforeEach } from 'vitest';
import { GitHubService } from '../github-service';
import { Octokit } from '@octokit/rest';

// Mock Octokit
vi.mock('@octokit/rest', () => ({
  Octokit: vi.fn().mockImplementation(() => ({
    repos: {
      get: vi.fn()
    },
    issues: {
      create: vi.fn()
    },
    users: {
      getAuthenticated: vi.fn()
    },
    rateLimit: {
      get: vi.fn()
    },
    request: vi.fn()
  }))
}));

describe('GitHubService', () => {
  let service: GitHubService;
  let mockOctokit: any;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new GitHubService('test-token');
    mockOctokit = new Octokit();
  });

  describe('parseRepository', () => {
    it('should parse valid repository names', () => {
      const result = service['parseRepository']('owner/repo');
      expect(result).toEqual({ owner: 'owner', repo: 'repo' });
    });

    it('should reject invalid repository formats', () => {
      expect(() => service['parseRepository']('invalid')).toThrow('Invalid repository format');
      expect(() => service['parseRepository']('owner/repo/extra')).toThrow('Invalid repository format');
      expect(() => service['parseRepository']('owner/<script>')).toThrow('Invalid repository name format');
    });
  });

  describe('sanitizeText', () => {
    it('should remove HTML-like characters', () => {
      const result = service['sanitizeText']('Hello <script>alert("xss")</script> World');
      expect(result).toBe('Hello scriptalert("xss")/script World');
    });

    it('should enforce length limits', () => {
      const longText = 'a'.repeat(100000);
      const result = service['sanitizeText'](longText);
      expect(result.length).toBeLessThanOrEqual(65536);
    });
  });

  describe('sanitizeLabel', () => {
    it('should convert labels to valid GitHub format', () => {
      expect(service['sanitizeLabel']('Product Owner')).toBe('product-owner');
      expect(service['sanitizeLabel']('UI/UX Designer!!!')).toBe('ui-ux-designer');
      expect(service['sanitizeLabel']('---test---')).toBe('test');
    });

    it('should enforce length limits', () => {
      const longLabel = 'a'.repeat(100);
      const result = service['sanitizeLabel'](longLabel);
      expect(result.length).toBeLessThanOrEqual(50);
    });
  });

  describe('checkAuthentication', () => {
    it('should return authenticated status with user info', async () => {
      mockOctokit.users.getAuthenticated.mockResolvedValue({
        data: { login: 'testuser' }
      });
      
      mockOctokit.request.mockResolvedValue({
        headers: { 'x-oauth-scopes': 'repo, user' }
      });

      const result = await service.checkAuthentication();
      
      expect(result.authenticated).toBe(true);
      expect(result.user).toBe('testuser');
      expect(result.scopes).toContain('repo');
    });

    it('should detect missing required scopes', async () => {
      mockOctokit.users.getAuthenticated.mockResolvedValue({
        data: { login: 'testuser' }
      });
      
      mockOctokit.request.mockResolvedValue({
        headers: { 'x-oauth-scopes': 'user' }
      });

      const result = await service.checkAuthentication();
      
      expect(result.authenticated).toBe(true);
      expect(result.error).toContain('Missing required GitHub scopes');
    });

    it('should handle authentication failures', async () => {
      mockOctokit.users.getAuthenticated.mockRejectedValue(new Error('Unauthorized'));

      const result = await service.checkAuthentication();
      
      expect(result.authenticated).toBe(false);
      expect(result.error).toBe('Not authenticated with GitHub');
    });
  });

  describe('createIssuesFromPhases', () => {
    const mockPhases = [
      {
        id: 'phase1',
        title: 'Test Phase',
        description: 'Test Description',
        roles: ['Developer'],
        issues: [
          {
            title: 'Test Issue',
            description: 'Test issue description',
            role: 'Developer'
          }
        ],
        approved: true
      }
    ];

    it('should validate repository access before creating issues', async () => {
      mockOctokit.repos.get.mockRejectedValue(new Error('Not found'));

      await expect(
        service.createIssuesFromPhases('owner/repo', mockPhases)
      ).rejects.toThrow('Cannot access repository');
    });

    it('should create epic and issues successfully', async () => {
      mockOctokit.repos.get.mockResolvedValue({ data: {} });
      mockOctokit.issues.create.mockResolvedValue({ data: { number: 1 } });

      const result = await service.createIssuesFromPhases('owner/repo', mockPhases);

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        phase: 'Test Phase',
        epicNumber: 1,
        issueCount: 1
      });

      // Verify epic was created with proper sanitization
      expect(mockOctokit.issues.create).toHaveBeenCalledWith(
        expect.objectContaining({
          owner: 'owner',
          repo: 'repo',
          title: '[Epic] Test Phase',
          labels: ['epic', 'phase:phase1']
        })
      );
    });

    it('should skip non-approved phases', async () => {
      const phasesWithUnapproved = [
        ...mockPhases,
        { ...mockPhases[0], id: 'phase2', approved: false }
      ];

      mockOctokit.repos.get.mockResolvedValue({ data: {} });
      mockOctokit.issues.create.mockResolvedValue({ data: { number: 1 } });

      const result = await service.createIssuesFromPhases('owner/repo', phasesWithUnapproved);

      expect(result).toHaveLength(1);
      expect(mockOctokit.issues.create).toHaveBeenCalledTimes(2); // 1 epic + 1 issue
    });
  });
});