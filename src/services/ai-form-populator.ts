import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';
import { RobustLLMHandler } from './json-extractor';
import { PromptSanitizer } from './prompt-sanitizer';

export interface FormFieldSuggestions {
  targetUsers: string[];
  techStack: string[];
  features: string[];
  domain: string;
  complexity: 'simple' | 'moderate' | 'complex';
}

const FORM_POPULATION_PROMPT = `You are an AI assistant that analyzes project README content to intelligently suggest form field values for a project planning tool.

Given the README content below, analyze it and provide intelligent suggestions for the following fields:

1. **Target Users**: Identify the primary user groups or personas who would use this product based on the README content. Consider both explicitly mentioned users and inferred users based on features.

2. **Tech Stack**: Extract and infer the technologies, frameworks, libraries, and tools used in the project. Look for:
   - Explicitly mentioned technologies
   - Dependencies in package files
   - File extensions and project structure clues
   - API mentions and integrations

3. **Key Features**: Extract the main features and capabilities of the project. Look for:
   - Feature lists
   - Functionality descriptions
   - Use cases mentioned
   - Problem-solving capabilities

4. **Domain**: Determine the most appropriate domain category based on the project's purpose and functionality.

5. **Complexity**: Assess the project complexity as simple, moderate, or complex based on:
   - Number of features
   - Technical stack diversity
   - Integration requirements
   - Scalability mentions

README CONTENT:
{readmeContent}

EXISTING PARSED DATA (use this as context but provide enhanced suggestions):
Title: {title}
Description: {description}
Basic Features: {basicFeatures}
Basic Tech Stack: {basicTechStack}

Provide your analysis in the following JSON format:
{
  "targetUsers": ["user group 1", "user group 2", ...],
  "techStack": ["technology 1", "technology 2", ...],
  "features": ["feature 1", "feature 2", ...],
  "domain": "domain_category",
  "complexity": "simple|moderate|complex"
}`;

export class AIFormPopulator {
  private anthropic: Anthropic;
  private model = 'claude-3-sonnet-20240229';

  constructor(apiKey: string = process.env.ANTHROPIC_API_KEY!) {
    this.anthropic = new Anthropic({ apiKey });
  }

  async populateFormFields(
    readmeContent: string,
    existingData?: {
      title?: string;
      description?: string;
      features?: string[];
      techStack?: string[];
    }
  ): Promise<FormFieldSuggestions> {
    // Sanitize inputs
    const sanitizedReadme = PromptSanitizer.sanitizeReadme(readmeContent);
    
    // Check for suspicious patterns
    if (PromptSanitizer.containsSuspiciousPatterns(readmeContent)) {
      throw new Error('Input contains potentially malicious patterns');
    }

    // Build the prompt with existing data as context
    const prompt = PromptSanitizer.buildSafePrompt(FORM_POPULATION_PROMPT, {
      readmeContent: sanitizedReadme,
      title: existingData?.title || 'Not provided',
      description: existingData?.description || 'Not provided',
      basicFeatures: existingData?.features?.join(', ') || 'None detected',
      basicTechStack: existingData?.techStack?.join(', ') || 'None detected'
    });

    // Define schema for validation
    const FormSuggestionsSchema = z.object({
      targetUsers: z.array(z.string()).min(1),
      techStack: z.array(z.string()).min(1),
      features: z.array(z.string()).min(1),
      domain: z.string(),
      complexity: z.enum(['simple', 'moderate', 'complex'])
    });

    try {
      // Use bulletproof extraction
      const suggestions = await RobustLLMHandler.getStructuredResponse(
        this.anthropic,
        prompt,
        FormSuggestionsSchema,
        'form-field-population'
      );

      // Post-process suggestions to ensure quality
      return {
        targetUsers: this.deduplicateAndClean(suggestions.targetUsers),
        techStack: this.deduplicateAndClean(suggestions.techStack),
        features: this.deduplicateAndClean(suggestions.features),
        domain: this.validateDomain(suggestions.domain),
        complexity: suggestions.complexity
      };
    } catch (error) {
      console.error('AI form population failed:', error);
      // Return fallback suggestions based on basic parsing
      return this.getFallbackSuggestions(existingData);
    }
  }

  private deduplicateAndClean(items: string[]): string[] {
    // Remove duplicates and clean up strings
    const seen = new Set<string>();
    return items
      .map(item => item.trim())
      .filter(item => item.length > 0 && item.length < 100) // Reasonable length
      .filter(item => {
        const normalized = item.toLowerCase();
        if (seen.has(normalized)) return false;
        seen.add(normalized);
        return true;
      });
  }

  private validateDomain(domain: string): string {
    const validDomains = [
      'e-commerce', 'social-media', 'productivity', 'healthcare',
      'education', 'finance', 'entertainment', 'devtools',
      'iot', 'general', 'communication', 'analytics', 'gaming'
    ];

    const normalized = domain.toLowerCase().replace(/\s+/g, '-');
    return validDomains.includes(normalized) ? normalized : 'general';
  }

  private getFallbackSuggestions(existingData?: {
    features?: string[];
    techStack?: string[];
  }): FormFieldSuggestions {
    return {
      targetUsers: ['developers', 'end-users'],
      techStack: existingData?.techStack || ['JavaScript', 'Node.js'],
      features: existingData?.features || ['Core functionality'],
      domain: 'general',
      complexity: 'moderate'
    };
  }
}

// Singleton instance for easy access
export async function populateFormWithAI(
  readmeContent: string,
  existingData?: {
    title?: string;
    description?: string;
    features?: string[];
    techStack?: string[];
  }
): Promise<FormFieldSuggestions> {
  const populator = new AIFormPopulator();
  return populator.populateFormFields(readmeContent, existingData);
}