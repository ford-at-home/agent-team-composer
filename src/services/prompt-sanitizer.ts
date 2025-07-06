import { z } from 'zod';

// Maximum lengths for different input types
const MAX_LENGTHS = {
  title: 256,
  description: 2048,
  readme: 50000,
  domain: 100,
  role: 100,
  phase: 200
};

// Schemas for validation
export const PromptInputSchema = z.object({
  title: z.string().max(MAX_LENGTHS.title),
  description: z.string().max(MAX_LENGTHS.description),
  domain: z.string().max(MAX_LENGTHS.domain),
  features: z.array(z.string().max(200)).max(50),
  techStack: z.array(z.string().max(100)).max(30),
  complexity: z.enum(['simple', 'moderate', 'complex'])
});

export class PromptSanitizer {
  /**
   * Sanitize user input for safe inclusion in prompts
   * Prevents prompt injection attacks
   */
  static sanitizeInput(input: string, maxLength: number = 1000): string {
    if (!input || typeof input !== 'string') {
      return '';
    }

    return input
      // Remove potential prompt injection patterns
      .replace(/\{[^}]*\}/g, '') // Remove template syntax
      .replace(/\$\{[^}]*\}/g, '') // Remove template literals
      .replace(/<%[^%>]*%>/g, '') // Remove ERB-style tags
      .replace(/\{\{[^}]*\}\}/g, '') // Remove mustache templates
      
      // Remove potential command sequences
      .replace(/\n\s*Human:/gi, '\n[User]:')
      .replace(/\n\s*Assistant:/gi, '\n[Agent]:')
      .replace(/\n\s*System:/gi, '\n[Note]:')
      
      // Limit consecutive newlines
      .replace(/\n{3,}/g, '\n\n')
      
      // Remove control characters
      .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')
      
      // Normalize whitespace
      .replace(/\s+/g, ' ')
      .trim()
      
      // Enforce length limit
      .slice(0, maxLength);
  }

  /**
   * Sanitize README content specifically
   */
  static sanitizeReadme(readme: string): string {
    return this.sanitizeInput(readme, MAX_LENGTHS.readme);
  }

  /**
   * Escape special characters for JSON inclusion
   */
  static escapeForJson(str: string): string {
    return str
      .replace(/\\/g, '\\\\')
      .replace(/"/g, '\\"')
      .replace(/\n/g, '\\n')
      .replace(/\r/g, '\\r')
      .replace(/\t/g, '\\t');
  }

  /**
   * Build safe prompt with sanitized inputs
   */
  static buildSafePrompt(template: string, variables: Record<string, any>): string {
    let prompt = template;
    
    // Sort by key length descending to avoid partial replacements
    const sortedKeys = Object.keys(variables).sort((a, b) => b.length - a.length);
    
    for (const key of sortedKeys) {
      const placeholder = `{${key}}`;
      const value = variables[key];
      
      let sanitizedValue: string;
      
      if (Array.isArray(value)) {
        sanitizedValue = value
          .map(v => this.sanitizeInput(String(v), 200))
          .join(', ');
      } else {
        sanitizedValue = this.sanitizeInput(String(value), 2000);
      }
      
      // Use a function replacer to avoid issues with $ in replacement
      prompt = prompt.replace(
        new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'),
        () => sanitizedValue
      );
    }
    
    return prompt;
  }

  /**
   * Validate and sanitize project info for LLM
   */
  static sanitizeProjectInfo(projectInfo: any): z.infer<typeof PromptInputSchema> {
    // Validate with schema
    const validated = PromptInputSchema.parse({
      title: this.sanitizeInput(projectInfo.title, MAX_LENGTHS.title),
      description: this.sanitizeInput(projectInfo.description, MAX_LENGTHS.description),
      domain: this.sanitizeInput(projectInfo.domain, MAX_LENGTHS.domain),
      features: projectInfo.features?.map((f: string) => 
        this.sanitizeInput(f, 200)
      ) || [],
      techStack: projectInfo.techStack?.map((t: string) => 
        this.sanitizeInput(t, 100)
      ) || [],
      complexity: projectInfo.complexity || 'moderate'
    });
    
    return validated;
  }

  /**
   * Check for potentially malicious patterns
   */
  static containsSuspiciousPatterns(input: string): boolean {
    const suspiciousPatterns = [
      /ignore\s+previous\s+instructions/i,
      /disregard\s+all\s+prior/i,
      /new\s+instructions:/i,
      /system\s+prompt:/i,
      /\[INST\]/i,
      /<\|im_start\|>/i,
      /\n\s*###\s*Instruction/i
    ];
    
    return suspiciousPatterns.some(pattern => pattern.test(input));
  }
}