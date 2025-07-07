import Anthropic from '@anthropic-ai/sdk';
import { ProjectData, Phase, Issue, LLMPhaseGeneration, LLMEpicGeneration } from '../types';
import { PHASE_GENERATOR_PROMPT } from '../prompts/phase-generator';
import { EPIC_GENERATOR_PROMPT } from '../prompts/epic-generator';
import { ISSUE_FORMATTER_PROMPT } from '../prompts/issue-formatter';
import { PromptSanitizer } from './prompt-sanitizer';
import { z } from 'zod';
import { BulletproofJSONExtractor, RobustLLMHandler } from './json-extractor';

export class LLMOrchestrator {
  private anthropic: Anthropic;
  private model = 'claude-3-sonnet-20240229';

  constructor(apiKey: string = process.env.ANTHROPIC_API_KEY!) {
    this.anthropic = new Anthropic({ apiKey });
  }

  async generateProjectPlan(
    projectInfo: {
      title: string;
      description: string;
      domain: string;
      features: string[];
      techStack: string[];
      complexity: string;
      targetUsers?: string[];
    },
    readmeContent: string
  ): Promise<ProjectData> {
    // Step 1: Generate phases based on README
    console.log('🤖 Generating project phases...');
    const phases = await this.generatePhases(projectInfo, readmeContent);
    
    // Step 2: For each phase, generate epics/tasks with role assignments
    console.log('👥 Generating epics and assigning roles...');
    const phasesWithTasks = await this.generateEpicsForPhases(phases, projectInfo);
    
    // Step 3: Format issues for GitHub
    console.log('📝 Formatting issues for GitHub...');
    const finalPhases = await this.formatIssuesForGitHub(phasesWithTasks, projectInfo);

    return {
      summary: {
        title: projectInfo.title,
        description: projectInfo.description,
        domain: projectInfo.domain,
        repository: 'unknown/unknown', // Will be set by CLI
        branch: 'main'
      },
      phases: finalPhases
    };
  }

  private async generatePhases(
    projectInfo: {
      title: string;
      description: string;
      domain: string;
      features: string[];
    },
    readmeContent: string
  ): Promise<LLMPhaseGeneration['phases']> {
    // Sanitize inputs
    const sanitizedInfo = PromptSanitizer.sanitizeProjectInfo(projectInfo);
    const sanitizedReadme = PromptSanitizer.sanitizeReadme(readmeContent);
    
    // Check for suspicious patterns
    if (PromptSanitizer.containsSuspiciousPatterns(readmeContent)) {
      throw new Error('Input contains potentially malicious patterns');
    }
    
    const prompt = PromptSanitizer.buildSafePrompt(PHASE_GENERATOR_PROMPT, {
      domain: sanitizedInfo.domain,
      readmeContent: sanitizedReadme
    });

    // Define schema for validation
    const PhaseGenerationSchema = z.object({
      phases: z.array(z.object({
        id: z.string(),
        title: z.string(),
        description: z.string(),
        suggestedRoles: z.array(z.string())
      }))
    });

    // Use bulletproof extraction
    const result = await RobustLLMHandler.getStructuredResponse(
      this.anthropic,
      prompt,
      PhaseGenerationSchema,
      'phase-generation'
    );

    // Ensure all fields are non-optional
    return result.phases.map(phase => ({
      id: phase.id,
      title: phase.title,
      description: phase.description,
      suggestedRoles: phase.suggestedRoles
    }));
  }

  private async generateEpicsForPhases(
    phases: LLMPhaseGeneration['phases'],
    projectInfo: { title: string; description: string; }
  ): Promise<Array<Phase & { tasks: LLMEpicGeneration['tasks'] }>> {
    const results = await Promise.all(
      phases.map(async (phase) => {
        const commonRoles = this.getCommonRolesForPhase(phase.title);
        
        const prompt = PromptSanitizer.buildSafePrompt(EPIC_GENERATOR_PROMPT, {
          phaseTitle: phase.title,
          phaseDescription: phase.description,
          productContext: `${projectInfo.title}: ${projectInfo.description}`,
          commonRoles: commonRoles.join('\n'),
          phaseId: phase.id
        });

        // Define schema for epic generation
        const EpicGenerationSchema = z.object({
          phaseId: z.string(),
          roles: z.array(z.string()),
          tasks: z.array(z.object({
            title: z.string(),
            description: z.string(),
            suggestedRole: z.string()
          }))
        }) as z.ZodSchema<LLMEpicGeneration>;

        // Use bulletproof extraction
        const epicGeneration = await RobustLLMHandler.getStructuredResponse(
          this.anthropic,
          prompt,
          EpicGenerationSchema,
          `epic-generation-${phase.id}`
        );

        return {
          id: phase.id,
          title: phase.title,
          description: phase.description,
          roles: epicGeneration.roles,
          tasks: epicGeneration.tasks,
          issues: [] as Issue[], // Will be populated in next step
          approved: false
        };
      })
    );

    return results;
  }

  private async formatIssuesForGitHub(
    phasesWithTasks: Array<Phase & { tasks: LLMEpicGeneration['tasks'] }>,
    projectInfo: { title: string; }
  ): Promise<Phase[]> {
    const results = await Promise.all(
      phasesWithTasks.map(async (phase) => {
        const issues = await Promise.all(
          phase.tasks.map(async (task) => {
            const prompt = PromptSanitizer.buildSafePrompt(ISSUE_FORMATTER_PROMPT, {
              taskTitle: task.title,
              taskDescription: task.description,
              assignedRole: task.suggestedRole,
              phaseTitle: phase.title,
              productContext: projectInfo.title
            });

            // Define schema for issue formatting
            const IssueFormatSchema = z.object({
              title: z.string(),
              body: z.string()
            });

            try {
              // Use bulletproof extraction with optional schema
              const formatted = await RobustLLMHandler.getStructuredResponse(
                this.anthropic,
                prompt,
                IssueFormatSchema,
                `issue-format-${phase.id}-${task.title.substring(0, 20)}`
              );

              return {
                title: formatted.title,
                description: formatted.body,
                role: task.suggestedRole
              };
            } catch (error) {
              // Fallback to simple format if extraction fails
              console.warn('Failed to format issue, using fallback:', error);
              return {
                title: task.title,
                description: task.description,
                role: task.suggestedRole
              };
            }
          })
        );

        return {
          id: phase.id,
          title: phase.title,
          description: phase.description,
          roles: phase.roles,
          issues,
          approved: true // Default to approved for now
        };
      })
    );

    return results;
  }

  private getCommonRolesForPhase(phaseTitle: string): string[] {
    const rolesByPhase: Record<string, string[]> = {
      'Discovery': [
        'Market Research Analyst - Conducts market research and competitive analysis',
        'User Research Specialist - Performs user interviews and creates personas',
        'Product Owner - Defines vision and prioritizes features'
      ],
      'Specification': [
        'Product Requirements Author - Creates comprehensive PRDs',
        'UI/UX Designer - Designs wireframes and user interfaces',
        'System Architect - Reviews technical feasibility'
      ],
      'Architecture': [
        'System Architect - Designs scalable system architecture',
        'Sprint Planner - Creates actionable sprint plans',
        'Tech Lead - Reviews and approves technical decisions'
      ],
      'Implementation': [
        'Frontend Developer - Implements UI components',
        'Backend Developer - Builds APIs and services',
        'Database Engineer - Designs data models',
        'DevOps Engineer - Sets up CI/CD pipelines'
      ],
      'Testing': [
        'Test Engineer - Creates test plans and automation',
        'Security Auditor - Identifies vulnerabilities',
        'Performance Tester - Validates system performance'
      ],
      'Deployment': [
        'Release Manager - Coordinates deployments',
        'DevOps Engineer - Manages infrastructure',
        'Technical Writer - Creates documentation'
      ],
      'Monitoring': [
        'Analytics Engineer - Implements tracking',
        'Site Reliability Engineer - Ensures system reliability',
        'Support Engineer - Handles user issues'
      ],
      'Enhancement': [
        'Feature Developer - Implements new features',
        'Refactoring Specialist - Improves code quality',
        'Product Owner - Prioritizes enhancements'
      ]
    };

    // Find matching phase
    for (const [key, roles] of Object.entries(rolesByPhase)) {
      if (phaseTitle.toLowerCase().includes(key.toLowerCase())) {
        return roles;
      }
    }

    // Default roles if no match
    return [
      'Product Owner - Defines requirements and priorities',
      'Software Engineer - Implements features and fixes',
      'QA Engineer - Ensures quality standards'
    ];
  }
}

export async function generateProjectPlan(
  projectInfo: {
    title: string;
    description: string;
    domain: string;
    features: string[];
    techStack: string[];
    complexity: string;
    targetUsers?: string[];
  },
  readmeContent: string
): Promise<ProjectData> {
  const orchestrator = new LLMOrchestrator();
  return orchestrator.generateProjectPlan(projectInfo, readmeContent);
}