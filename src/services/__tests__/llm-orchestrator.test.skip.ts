import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { LLMOrchestrator, generateProjectPlan } from '../llm-orchestrator';
import { ProjectData } from '../../types';

// Mock the Anthropic SDK
vi.mock('@anthropic-ai/sdk', () => {
  return {
    default: vi.fn().mockImplementation(() => ({
      messages: {
        create: vi.fn()
      }
    }))
  };
});

// Mock the prompt sanitizer
vi.mock('../prompt-sanitizer', () => ({
  PromptSanitizer: {
    sanitizeProjectInfo: vi.fn((info) => info),
    sanitizeReadme: vi.fn((readme) => readme),
    containsSuspiciousPatterns: vi.fn(() => false),
    buildSafePrompt: vi.fn((template, vars) => 
      Object.entries(vars).reduce((acc, [key, value]) => 
        acc.replace(`{{${key}}}`, String(value)), template)
    )
  }
}));

describe('LLMOrchestrator', () => {
  let orchestrator: LLMOrchestrator;
  let mockAnthropicCreate: any;

  beforeEach(() => {
    orchestrator = new LLMOrchestrator('test-api-key');
    // Access the mocked Anthropic instance
    const Anthropic = require('@anthropic-ai/sdk').default;
    mockAnthropicCreate = Anthropic.mock.results[0].value.messages.create;
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('generateProjectPlan', () => {
    const mockProjectInfo = {
      title: 'Test Project',
      description: 'A test project description',
      domain: 'e-commerce',
      features: ['Feature 1', 'Feature 2'],
      techStack: ['React', 'Node.js'],
      complexity: 'moderate'
    };

    const mockReadmeContent = '# Test Project\nA comprehensive e-commerce platform.';

    it('should generate a complete project plan', async () => {
      // Mock phase generation response
      mockAnthropicCreate
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "phases": [\n    {\n      "id": "discovery",\n      "title": "Discovery & Research",\n      "description": "Initial research phase",\n      "suggestedRoles": ["Market Research Analyst", "User Research Specialist"]\n    },\n    {\n      "id": "implementation",\n      "title": "Implementation",\n      "description": "Core development phase",\n      "suggestedRoles": ["Frontend Developer", "Backend Developer"]\n    }\n  ]\n}\n```'
          }]
        })
        // Mock epic generation responses (one for each phase)
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "roles": ["Market Research Analyst", "User Research Specialist"],\n  "tasks": [\n    {\n      "title": "Market Analysis",\n      "description": "Analyze competitors",\n      "suggestedRole": "Market Research Analyst"\n    }\n  ]\n}\n```'
          }]
        })
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "roles": ["Frontend Developer", "Backend Developer"],\n  "tasks": [\n    {\n      "title": "Build UI Components",\n      "description": "Create React components",\n      "suggestedRole": "Frontend Developer"\n    }\n  ]\n}\n```'
          }]
        })
        // Mock issue formatting responses
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "title": "Market Analysis",\n  "body": "## Task\\n\\nAnalyze competitors and market trends."\n}\n```'
          }]
        })
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "title": "Build UI Components",\n  "body": "## Task\\n\\nCreate reusable React components."\n}\n```'
          }]
        });

      const result = await orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent);

      expect(result).toMatchObject({
        summary: {
          title: 'Test Project',
          description: 'A test project description',
          domain: 'e-commerce',
          repository: 'unknown/unknown',
          branch: 'main'
        },
        phases: expect.arrayContaining([
          expect.objectContaining({
            id: 'discovery',
            title: 'Discovery & Research',
            description: 'Initial research phase',
            roles: ['Market Research Analyst', 'User Research Specialist'],
            issues: expect.arrayContaining([
              expect.objectContaining({
                title: 'Market Analysis',
                description: '## Task\n\nAnalyze competitors and market trends.',
                role: 'Market Research Analyst'
              })
            ]),
            approved: true
          }),
          expect.objectContaining({
            id: 'implementation',
            title: 'Implementation',
            description: 'Core development phase',
            roles: ['Frontend Developer', 'Backend Developer'],
            issues: expect.arrayContaining([
              expect.objectContaining({
                title: 'Build UI Components',
                description: '## Task\n\nCreate reusable React components.',
                role: 'Frontend Developer'
              })
            ]),
            approved: true
          })
        ])
      });

      // Verify API calls
      expect(mockAnthropicCreate).toHaveBeenCalledTimes(5); // 1 phase + 2 epics + 2 issues
    });

    it('should handle suspicious patterns in readme', async () => {
      const { PromptSanitizer } = await import('../prompt-sanitizer');
      (PromptSanitizer.containsSuspiciousPatterns as any).mockReturnValueOnce(true);

      await expect(
        orchestrator.generateProjectPlan(mockProjectInfo, 'Malicious content')
      ).rejects.toThrow('Input contains potentially malicious patterns');
    });

    it('should handle API errors gracefully', async () => {
      mockAnthropicCreate.mockRejectedValueOnce(new Error('API rate limit exceeded'));

      await expect(
        orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent)
      ).rejects.toThrow('API rate limit exceeded');
    });

    it('should handle invalid JSON response from LLM', async () => {
      mockAnthropicCreate.mockResolvedValueOnce({
        content: [{
          type: 'text',
          text: 'Invalid response without JSON'
        }]
      });

      await expect(
        orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent)
      ).rejects.toThrow('Failed to extract JSON from LLM response');
    });

    it('should handle malformed JSON in response', async () => {
      mockAnthropicCreate.mockResolvedValueOnce({
        content: [{
          type: 'text',
          text: '```json\n{ invalid json }\n```'
        }]
      });

      await expect(
        orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent)
      ).rejects.toThrow('Invalid response format from LLM');
    });

    it('should handle missing required fields in phase response', async () => {
      mockAnthropicCreate.mockResolvedValueOnce({
        content: [{
          type: 'text',
          text: '```json\n{\n  "phases": [\n    {\n      "id": "phase1",\n      "title": "Phase 1"\n    }\n  ]\n}\n```'
        }]
      });

      await expect(
        orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent)
      ).rejects.toThrow('Invalid response format from LLM');
    });

    it('should use fallback format when issue formatting fails', async () => {
      // Mock successful phase generation
      mockAnthropicCreate
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "phases": [\n    {\n      "id": "phase1",\n      "title": "Phase 1",\n      "description": "Test phase",\n      "suggestedRoles": ["Developer"]\n    }\n  ]\n}\n```'
          }]
        })
        // Mock successful epic generation
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "roles": ["Developer"],\n  "tasks": [\n    {\n      "title": "Task 1",\n      "description": "Task description",\n      "suggestedRole": "Developer"\n    }\n  ]\n}\n```'
          }]
        })
        // Mock failed issue formatting (no JSON)
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: 'Invalid response without JSON'
          }]
        });

      const result = await orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent);

      // Should fallback to simple format
      expect(result.phases[0].issues[0]).toMatchObject({
        title: 'Task 1',
        description: 'Task description',
        role: 'Developer'
      });
    });
  });

  describe('getCommonRolesForPhase', () => {
    it('should return discovery roles for discovery phase', async () => {
      // We need to test this through generateProjectPlan since it's private
      mockAnthropicCreate
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "phases": [\n    {\n      "id": "discovery",\n      "title": "Discovery & Research",\n      "description": "Research phase",\n      "suggestedRoles": []\n    }\n  ]\n}\n```'
          }]
        })
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "roles": ["Market Research Analyst"],\n  "tasks": []\n}\n```'
          }]
        });

      await orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent);

      // Verify the prompt contained discovery-specific roles
      const epicGeneratorCall = mockAnthropicCreate.mock.calls[1];
      expect(epicGeneratorCall[0].messages[0].content).toContain('Market Research Analyst');
      expect(epicGeneratorCall[0].messages[0].content).toContain('User Research Specialist');
    });

    it('should return implementation roles for implementation phase', async () => {
      mockAnthropicCreate
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "phases": [\n    {\n      "id": "impl",\n      "title": "Implementation Phase",\n      "description": "Build phase",\n      "suggestedRoles": []\n    }\n  ]\n}\n```'
          }]
        })
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "roles": ["Frontend Developer"],\n  "tasks": []\n}\n```'
          }]
        });

      await orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent);

      const epicGeneratorCall = mockAnthropicCreate.mock.calls[1];
      expect(epicGeneratorCall[0].messages[0].content).toContain('Frontend Developer');
      expect(epicGeneratorCall[0].messages[0].content).toContain('Backend Developer');
    });

    it('should return default roles for unmatched phase', async () => {
      mockAnthropicCreate
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "phases": [\n    {\n      "id": "custom",\n      "title": "Custom Phase",\n      "description": "Unique phase",\n      "suggestedRoles": []\n    }\n  ]\n}\n```'
          }]
        })
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "roles": ["Product Owner"],\n  "tasks": []\n}\n```'
          }]
        });

      await orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent);

      const epicGeneratorCall = mockAnthropicCreate.mock.calls[1];
      expect(epicGeneratorCall[0].messages[0].content).toContain('Product Owner');
      expect(epicGeneratorCall[0].messages[0].content).toContain('Software Engineer');
      expect(epicGeneratorCall[0].messages[0].content).toContain('QA Engineer');
    });
  });

  describe('parallel processing', () => {
    it('should process phases in parallel', async () => {
      const startTime = Date.now();

      // Create delays for mocked responses
      mockAnthropicCreate
        .mockImplementation(() => new Promise(resolve => {
          const response = {
            content: [{
              type: 'text',
              text: '```json\n{\n  "phases": [\n    {\n      "id": "phase1",\n      "title": "Phase 1",\n      "description": "First phase",\n      "suggestedRoles": ["Role1"]\n    },\n    {\n      "id": "phase2",\n      "title": "Phase 2",\n      "description": "Second phase",\n      "suggestedRoles": ["Role2"]\n    }\n  ]\n}\n```'
            }]
          };
          
          // First call returns phases immediately
          if (mockAnthropicCreate.mock.calls.length === 1) {
            resolve(response);
          } else {
            // Epic generation calls have a delay
            setTimeout(() => {
              resolve({
                content: [{
                  type: 'text',
                  text: '```json\n{\n  "roles": ["Role"],\n  "tasks": [{\n    "title": "Task",\n    "description": "Description",\n    "suggestedRole": "Role"\n  }]\n}\n```'
                }]
              });
            }, 50);
          }
        }));

      await orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent);

      const endTime = Date.now();
      const duration = endTime - startTime;

      // If processed sequentially, would take at least 100ms (2 * 50ms)
      // If parallel, should take around 50ms
      expect(duration).toBeLessThan(80); // Allow some overhead
    });
  });

  describe('error handling in different stages', () => {
    it('should handle error in epic generation for one phase', async () => {
      mockAnthropicCreate
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "phases": [\n    {\n      "id": "phase1",\n      "title": "Phase 1",\n      "description": "First",\n      "suggestedRoles": ["Role1"]\n    },\n    {\n      "id": "phase2",\n      "title": "Phase 2",\n      "description": "Second",\n      "suggestedRoles": ["Role2"]\n    }\n  ]\n}\n```'
          }]
        })
        .mockResolvedValueOnce({
          content: [{
            type: 'text',
            text: '```json\n{\n  "roles": ["Role1"],\n  "tasks": [{\n    "title": "Task 1",\n    "description": "Desc",\n    "suggestedRole": "Role1"\n  }]\n}\n```'
          }]
        })
        .mockRejectedValueOnce(new Error('Epic generation failed'));

      await expect(
        orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent)
      ).rejects.toThrow('Epic generation failed');
    });

    it('should handle non-text content in response', async () => {
      mockAnthropicCreate.mockResolvedValueOnce({
        content: [{
          type: 'image',
          source: { type: 'base64', media_type: 'image/png', data: 'fake' }
        }]
      });

      await expect(
        orchestrator.generateProjectPlan(mockProjectInfo, mockReadmeContent)
      ).rejects.toThrow('Failed to extract JSON from LLM response');
    });
  });
});

describe('generateProjectPlan function', () => {
  it('should create a new orchestrator and generate plan', async () => {
    const Anthropic = require('@anthropic-ai/sdk').default;
    const mockCreate = vi.fn()
      .mockResolvedValueOnce({
        content: [{
          type: 'text',
          text: '```json\n{\n  "phases": [{\n    "id": "test",\n    "title": "Test Phase",\n    "description": "Test",\n    "suggestedRoles": ["Tester"]\n  }]\n}\n```'
        }]
      })
      .mockResolvedValueOnce({
        content: [{
          type: 'text',
          text: '```json\n{\n  "roles": ["Tester"],\n  "tasks": []\n}\n```'
        }]
      });

    Anthropic.mockImplementation(() => ({
      messages: { create: mockCreate }
    }));

    const projectInfo = {
      title: 'Test',
      description: 'Test project',
      domain: 'testing',
      features: [],
      techStack: [],
      complexity: 'simple'
    };

    const result = await generateProjectPlan(projectInfo, '# Test');

    expect(result).toMatchObject({
      summary: {
        title: 'Test',
        description: 'Test project',
        domain: 'testing'
      },
      phases: expect.any(Array)
    });
  });
});