import Anthropic from '@anthropic-ai/sdk';
import { ProjectData, Phase, Issue, LLMPhaseGeneration, LLMEpicGeneration } from '../types';
import { PHASE_GENERATOR_PROMPT } from '../prompts/phase-generator';
import { EPIC_GENERATOR_PROMPT } from '../prompts/epic-generator';
import { ISSUE_FORMATTER_PROMPT } from '../prompts/issue-formatter';
import { PromptSanitizer } from './prompt-sanitizer';
import { z } from 'zod';

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

    const response = await this.anthropic.messages.create({
      model: this.model,
      max_tokens: 4000,
      temperature: 0.7,
      system: 'You are a helpful assistant that generates project plans. Always respond with valid JSON in the specified format.',
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const content = response.content[0].type === 'text' ? response.content[0].text : '';
    
    // Extract and validate JSON from response
    let jsonStr = '';
    const jsonMatch = content.match(/```(?:json)?\n?([\s\S]*?)\n?```/);
    
    if (jsonMatch) {
      jsonStr = jsonMatch[1].trim();
    } else {
      // Try to find JSON without code block markers
      const jsonStart = content.indexOf('{');
      const jsonEnd = content.lastIndexOf('}');
      
      if (jsonStart !== -1 && jsonEnd !== -1 && jsonEnd > jsonStart) {
        jsonStr = content.substring(jsonStart, jsonEnd + 1);
      } else {
        console.error('Failed to extract JSON from LLM response');
        console.error('LLM Response:', content);
        throw new Error('Failed to extract JSON from LLM response. Response did not contain valid JSON.');
      }
    }

    try {
      const parsed = JSON.parse(jsonStr);
      
      // Validate response structure
      const PhaseGenerationSchema = z.object({
        phases: z.array(z.object({
          id: z.string(),
          title: z.string(),
          description: z.string(),
          suggestedRoles: z.array(z.string())
        }))
      });
      
      const result = PhaseGenerationSchema.parse(parsed);
      // Ensure all fields are non-optional
      return result.phases.map(phase => ({
        id: phase.id,
        title: phase.title,
        description: phase.description,
        suggestedRoles: phase.suggestedRoles
      }));
    } catch (error) {
      console.error('Failed to parse LLM response:', error);
      throw new Error('Invalid response format from LLM');
    }
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

        const response = await this.anthropic.messages.create({
          model: this.model,
          max_tokens: 4000,
          temperature: 0.7,
          messages: [{
            role: 'user',
            content: prompt
          }]
        });

        const content = response.content[0].type === 'text' ? response.content[0].text : '';
        
        // Try to extract JSON with code block markers first
        let jsonStr = '';
        const jsonMatch = content.match(/```(?:json)?\n?([\s\S]*?)\n?```/);
        
        if (jsonMatch) {
          jsonStr = jsonMatch[1].trim();
        } else {
          // Try to find JSON without code block markers
          const jsonStart = content.indexOf('{');
          const jsonEnd = content.lastIndexOf('}');
          
          if (jsonStart !== -1 && jsonEnd !== -1 && jsonEnd > jsonStart) {
            jsonStr = content.substring(jsonStart, jsonEnd + 1);
          } else {
            console.error('Failed to extract JSON from LLM response for phase:', phase.title);
            console.error('LLM Response:', content);
            throw new Error(`Failed to extract JSON for phase ${phase.title}. Response did not contain valid JSON.`);
          }
        }

        let epicGeneration: LLMEpicGeneration;
        try {
          epicGeneration = JSON.parse(jsonStr);
        } catch (parseError) {
          console.error('Failed to parse JSON for phase:', phase.title);
          console.error('JSON string:', jsonStr);
          console.error('Parse error:', parseError);
          throw new Error(`Failed to parse JSON for phase ${phase.title}. Invalid JSON format.`);
        }

        return {
          id: phase.id,
          title: phase.title,
          description: phase.description,
          roles: epicGeneration.roles,
          tasks: epicGeneration.tasks,
          issues: [], // Will be populated in next step
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

            const response = await this.anthropic.messages.create({
              model: this.model,
              max_tokens: 2000,
              temperature: 0.5,
              messages: [{
                role: 'user',
                content: prompt
              }]
            });

            const content = response.content[0].type === 'text' ? response.content[0].text : '';
            
            // Try to extract JSON
            let jsonStr = '';
            const jsonMatch = content.match(/```(?:json)?\n?([\s\S]*?)\n?```/);
            
            if (jsonMatch) {
              jsonStr = jsonMatch[1].trim();
            } else {
              // Try to find JSON without code block markers
              const jsonStart = content.indexOf('{');
              const jsonEnd = content.lastIndexOf('}');
              
              if (jsonStart !== -1 && jsonEnd !== -1 && jsonEnd > jsonStart) {
                jsonStr = content.substring(jsonStart, jsonEnd + 1);
              }
            }

            if (!jsonStr) {
              // Fallback to simple format
              return {
                title: task.title,
                description: task.description,
                role: task.suggestedRole
              };
            }

            try {
              const formatted = JSON.parse(jsonStr);
              return {
                title: formatted.title || task.title,
                description: formatted.body || task.description,
                role: task.suggestedRole
              };
            } catch (parseError) {
              console.error('Failed to parse issue format JSON:', parseError);
              console.error('JSON string:', jsonStr);
              // Fallback to simple format
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