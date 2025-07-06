import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from 'vitest';
import request from 'supertest';
import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';
import { ProjectData } from '../../types';

// Mock dependencies
vi.mock('../../services/github-service', () => ({
  GitHubService: vi.fn().mockImplementation(() => ({
    checkAuthentication: vi.fn(),
    createIssuesFromPhases: vi.fn()
  }))
}));

vi.mock('vite', () => ({
  createServer: vi.fn().mockResolvedValue({
    middlewares: (req: any, res: any, next: any) => next()
  })
}));

describe('Server API Integration Tests', () => {
  let serverUrl: string;
  let tempDir: string;
  let tempDataPath: string;
  let serverProcess: any;

  const mockProjectData: ProjectData = {
    summary: {
      title: 'Test Project',
      description: 'Test Description',
      domain: 'test',
      repository: 'test/repo',
      branch: 'main'
    },
    phases: [
      {
        id: 'phase1',
        title: 'Phase 1',
        description: 'First phase',
        roles: ['Developer'],
        issues: [
          {
            title: 'Task 1',
            description: 'Do something',
            role: 'Developer'
          }
        ],
        approved: true
      }
    ]
  };

  beforeAll(async () => {
    // Create temp directory and file
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'test-'));
    tempDataPath = path.join(tempDir, 'project-data.json');
    await fs.writeFile(tempDataPath, JSON.stringify(mockProjectData));

    // Import and start server
    const { startServer } = await import('../index');
    serverUrl = await startServer(0, tempDataPath);
  }, 30000);

  afterAll(async () => {
    // Clean up
    await fs.rm(tempDir, { recursive: true }).catch(() => {});
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('GET /api/health', () => {
    it('should return health status', async () => {
      const response = await request(serverUrl)
        .get('/api/health')
        .expect(200);

      expect(response.body).toMatchObject({
        status: 'healthy',
        timestamp: expect.any(String),
        version: expect.any(String)
      });
    });
  });

  describe('GET /api/project', () => {
    it('should return project data', async () => {
      const response = await request(serverUrl)
        .get('/api/project')
        .expect(200);

      expect(response.body).toEqual(mockProjectData);
    });
  });

  describe('PUT /api/project', () => {
    it('should update project data', async () => {
      const updatedData = {
        ...mockProjectData,
        summary: {
          ...mockProjectData.summary,
          title: 'Updated Title'
        }
      };

      await request(serverUrl)
        .put('/api/project')
        .send(updatedData)
        .expect(200);

      const response = await request(serverUrl)
        .get('/api/project')
        .expect(200);

      expect(response.body.summary.title).toBe('Updated Title');
    });

    it('should save to temp file', async () => {
      const updatedData = {
        ...mockProjectData,
        summary: {
          ...mockProjectData.summary,
          description: 'Saved Description'
        }
      };

      await request(serverUrl)
        .put('/api/project')
        .send(updatedData)
        .expect(200);

      const fileContent = await fs.readFile(tempDataPath, 'utf8');
      const savedData = JSON.parse(fileContent);
      expect(savedData.summary.description).toBe('Saved Description');
    });
  });

  describe('GET /api/github/auth', () => {
    it('should check GitHub authentication', async () => {
      const { GitHubService } = await import('../../services/github-service');
      const mockCheckAuth = vi.fn().mockResolvedValue({
        authenticated: true,
        user: 'testuser'
      });
      (GitHubService as any).mockImplementation(() => ({
        checkAuthentication: mockCheckAuth
      }));

      const response = await request(serverUrl)
        .get('/api/github/auth')
        .expect(200);

      expect(response.body).toEqual({
        authenticated: true,
        user: 'testuser'
      });
    });

    it('should handle auth errors', async () => {
      const { GitHubService } = await import('../../services/github-service');
      const mockCheckAuth = vi.fn().mockRejectedValue(new Error('Auth failed'));
      (GitHubService as any).mockImplementation(() => ({
        checkAuthentication: mockCheckAuth
      }));

      const response = await request(serverUrl)
        .get('/api/github/auth')
        .expect(500);

      expect(response.body).toMatchObject({
        error: 'Failed to check GitHub authentication',
        details: 'Auth failed'
      });
    });
  });

  describe('POST /api/github/create-issues', () => {
    it('should create GitHub issues', async () => {
      const { GitHubService } = await import('../../services/github-service');
      const mockCheckAuth = vi.fn().mockResolvedValue({ authenticated: true });
      const mockCreateIssues = vi.fn().mockResolvedValue({
        epicsCreated: 1,
        issuesCreated: 1
      });
      
      (GitHubService as any).mockImplementation(() => ({
        checkAuthentication: mockCheckAuth,
        createIssuesFromPhases: mockCreateIssues
      }));

      const response = await request(serverUrl)
        .post('/api/github/create-issues')
        .send({
          repository: 'owner/repo',
          phases: mockProjectData.phases
        })
        .expect(200);

      expect(response.body).toEqual({
        success: true,
        results: {
          epicsCreated: 1,
          issuesCreated: 1
        }
      });
    });

    it('should reject unauthenticated requests', async () => {
      const { GitHubService } = await import('../../services/github-service');
      const mockCheckAuth = vi.fn().mockResolvedValue({ authenticated: false });
      
      (GitHubService as any).mockImplementation(() => ({
        checkAuthentication: mockCheckAuth
      }));

      const response = await request(serverUrl)
        .post('/api/github/create-issues')
        .send({
          repository: 'owner/repo',
          phases: mockProjectData.phases
        })
        .expect(401);

      expect(response.body).toMatchObject({
        error: 'GitHub authentication required'
      });
    });

    it('should validate repository format', async () => {
      const response = await request(serverUrl)
        .post('/api/github/create-issues')
        .send({
          repository: 'invalid-format',
          phases: mockProjectData.phases
        })
        .expect(400);

      expect(response.body.error).toBe('Invalid request data');
    });

    it('should handle GitHub API errors', async () => {
      const { GitHubService } = await import('../../services/github-service');
      const mockCheckAuth = vi.fn().mockResolvedValue({ authenticated: true });
      const mockCreateIssues = vi.fn().mockRejectedValue(new Error('API error'));
      
      (GitHubService as any).mockImplementation(() => ({
        checkAuthentication: mockCheckAuth,
        createIssuesFromPhases: mockCreateIssues
      }));

      const response = await request(serverUrl)
        .post('/api/github/create-issues')
        .send({
          repository: 'owner/repo',
          phases: mockProjectData.phases
        })
        .expect(500);

      expect(response.body).toMatchObject({
        error: 'Failed to create GitHub issues',
        details: 'API error'
      });
    });
  });

  describe('CORS', () => {
    it('should allow CORS requests', async () => {
      const response = await request(serverUrl)
        .get('/api/health')
        .set('Origin', 'http://localhost:3000')
        .expect(200);

      expect(response.headers['access-control-allow-origin']).toBeDefined();
    });
  });

  describe('Error handling', () => {
    it('should handle 404', async () => {
      await request(serverUrl)
        .get('/api/unknown')
        .expect(404);
    });

    it('should handle invalid JSON', async () => {
      await request(serverUrl)
        .put('/api/project')
        .set('Content-Type', 'application/json')
        .send('invalid json')
        .expect(400);
    });

    it('should handle large payloads', async () => {
      const largeData = {
        ...mockProjectData,
        phases: Array(100).fill(mockProjectData.phases[0])
      };

      const response = await request(serverUrl)
        .put('/api/project')
        .send(largeData)
        .expect(200);

      expect(response.body).toEqual({ success: true });
    });
  });
});

describe('startServer function', () => {
  it('should handle invalid JSON file', async () => {
    const tempFile = path.join(os.tmpdir(), 'invalid.json');
    await fs.writeFile(tempFile, 'invalid json');

    const { startServer } = await import('../index');
    await expect(startServer(0, tempFile)).rejects.toThrow();
    
    await fs.unlink(tempFile).catch(() => {});
  });

  it('should handle missing file', async () => {
    const { startServer } = await import('../index');
    await expect(startServer(0, '/non/existent/file.json')).rejects.toThrow();
  });
});