import { z } from 'zod';
import { TelemetryService } from './telemetry';
import Anthropic from '@anthropic-ai/sdk';

interface ExtractionResult<T> {
  success: boolean;
  data?: T;
  error?: string;
  rawContent?: string;
  extractionMethod?: string;
}

export class BulletproofJSONExtractor {
  private static extractionMethods = [
    this.extractWithCodeBlocks,
    this.extractWithoutCodeBlocks,
    this.extractWithRegexCleanup,
    this.extractWithJSONRepair,
    this.extractWithManualParsing,
    this.extractWithFuzzyMatching
  ];

  /**
   * Main extraction method that tries multiple strategies
   */
  static async extract<T>(
    content: string,
    schema: z.ZodSchema<T>,
    context?: string
  ): Promise<ExtractionResult<T>> {
    const startTime = Date.now();
    const telemetry = TelemetryService.getInstance();
    
    // Store original for debugging
    const originalContent = content;

    // Try each extraction method in order
    for (const [index, method] of this.extractionMethods.entries()) {
      try {
        const extracted = method(content);
        if (extracted) {
          // Validate against schema
          const parsed = schema.safeParse(extracted);
          if (parsed.success) {
            // Track successful extraction
            telemetry.trackExtractionMetrics({
              method: method.name,
              success: true,
              duration: Date.now() - startTime,
              retryCount: index,
              context: context || 'unknown',
              contentLength: content.length
            });
            
            return {
              success: true,
              data: parsed.data,
              extractionMethod: method.name
            };
          }
        }
      } catch (error) {
        // Continue to next method
        continue;
      }
    }

    // All methods failed - track failure
    telemetry.trackExtractionMetrics({
      method: 'all_failed',
      success: false,
      duration: Date.now() - startTime,
      retryCount: this.extractionMethods.length,
      context: context || 'unknown',
      errorType: 'extraction_failed',
      contentLength: content.length
    });

    return {
      success: false,
      error: 'Failed to extract valid JSON after trying all methods',
      rawContent: originalContent
    };
  }

  /**
   * Method 1: Standard code block extraction
   */
  private static extractWithCodeBlocks(content: string): unknown {
    const patterns = [
      /```json\s*\n([\s\S]*?)\n```/,
      /```JSON\s*\n([\s\S]*?)\n```/,
      /```\s*\n(\{[\s\S]*?\})\n```/,
      /```\s*\n(\[[\s\S]*?\])\n```/
    ];

    for (const pattern of patterns) {
      const match = content.match(pattern);
      if (match) {
        return JSON.parse(match[1].trim());
      }
    }
    return null;
  }

  /**
   * Method 2: Extract JSON without code blocks
   */
  private static extractWithoutCodeBlocks(content: string): unknown {
    // Find the first { or [ and the last } or ]
    const jsonStart = Math.min(
      content.indexOf('{') !== -1 ? content.indexOf('{') : Infinity,
      content.indexOf('[') !== -1 ? content.indexOf('[') : Infinity
    );
    
    const jsonEnd = Math.max(
      content.lastIndexOf('}'),
      content.lastIndexOf(']')
    );

    if (jsonStart !== Infinity && jsonEnd > jsonStart) {
      const jsonStr = content.substring(jsonStart, jsonEnd + 1);
      return JSON.parse(jsonStr);
    }
    return null;
  }

  /**
   * Method 3: Clean up common formatting issues
   */
  private static extractWithRegexCleanup(content: string): unknown {
    let cleaned = content;
    
    // Remove common prefixes/suffixes
    cleaned = cleaned.replace(/^.*?(?=\{|\[)/s, '');
    cleaned = cleaned.replace(/(\}|\])(?!.*(\}|\]))[\s\S]*$/s, '$1');
    
    // Fix common JSON issues
    cleaned = cleaned
      .replace(/,\s*\}/g, '}') // Remove trailing commas
      .replace(/,\s*\]/g, ']')
      .replace(/'/g, '"') // Replace single quotes
      .replace(/(\w+):/g, '"$1":') // Quote unquoted keys
      .replace(/:\s*undefined/g, ': null') // Replace undefined
      .replace(/\n/g, ' ') // Remove newlines in strings
      .replace(/\t/g, ' '); // Remove tabs

    return JSON.parse(cleaned);
  }

  /**
   * Method 4: Use JSON repair library logic
   */
  private static extractWithJSONRepair(content: string): unknown {
    // Extract potential JSON
    const jsonMatch = content.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
    if (!jsonMatch) return null;

    let json = jsonMatch[0];
    
    // Common repairs
    const repairs = [
      // Fix quotes
      (s: string) => s.replace(/([^"\\])'([^']*)'([^"])/g, '$1"$2"$3'),
      // Fix trailing commas
      (s: string) => s.replace(/,(\s*[}\]])/g, '$1'),
      // Quote unquoted keys
      (s: string) => s.replace(/([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:/g, '$1"$2":'),
      // Fix boolean values
      (s: string) => s.replace(/:\s*(true|false|null)\s*([,}])/gi, ': $1$2'),
      // Escape unescaped quotes in strings
      (s: string) => {
        // This is complex but handles quotes inside string values
        return s.replace(/"([^"]*)":/g, (match, key) => {
          return `"${key.replace(/"/g, '\\"')}":`;
        });
      }
    ];

    for (const repair of repairs) {
      try {
        json = repair(json);
      } catch {
        // Continue with next repair
      }
    }

    return JSON.parse(json);
  }

  /**
   * Method 5: Manual character-by-character parsing
   */
  private static extractWithManualParsing(content: string): unknown {
    const stack: string[] = [];
    let inString = false;
    let escaped = false;
    let jsonStart = -1;
    let jsonEnd = -1;

    for (let i = 0; i < content.length; i++) {
      const char = content[i];
      
      if (escaped) {
        escaped = false;
        continue;
      }

      if (char === '\\') {
        escaped = true;
        continue;
      }

      if (char === '"' && !escaped) {
        inString = !inString;
        continue;
      }

      if (!inString) {
        if (char === '{' || char === '[') {
          if (stack.length === 0) jsonStart = i;
          stack.push(char);
        } else if (char === '}' || char === ']') {
          const expected = char === '}' ? '{' : '[';
          if (stack[stack.length - 1] === expected) {
            stack.pop();
            if (stack.length === 0) {
              jsonEnd = i;
              break;
            }
          }
        }
      }
    }

    if (jsonStart !== -1 && jsonEnd !== -1) {
      const jsonStr = content.substring(jsonStart, jsonEnd + 1);
      return JSON.parse(jsonStr);
    }
    return null;
  }

  /**
   * Method 6: Fuzzy matching with structure detection
   */
  private static extractWithFuzzyMatching(content: string): unknown {
    // Look for JSON-like structures even if malformed
    const structures = [
      // Object with phases array
      /phases\s*:\s*\[([\s\S]*?)\]/,
      // Object with tasks array
      /tasks\s*:\s*\[([\s\S]*?)\]/,
      // Generic object pattern
      /\{\s*"?\w+"?\s*:\s*[\s\S]*?\}/
    ];

    for (const pattern of structures) {
      const match = content.match(pattern);
      if (match) {
        // Try to reconstruct valid JSON
        try {
          // This is a last resort - try to build valid JSON from fragments
          const reconstructed = `{${match[0]}}`;
          return JSON.parse(reconstructed);
        } catch {
          continue;
        }
      }
    }
    return null;
  }

  /**
   * Retry with explicit format instructions
   */
  static createRetryPrompt(originalPrompt: string, error: string): string {
    return `${originalPrompt}

CRITICAL: Your previous response could not be parsed as JSON. Error: ${error}

Please respond with ONLY valid JSON, no additional text. Start your response with { or [ and end with } or ].

Example of correct format:
{
  "field": "value",
  "array": ["item1", "item2"]
}`;
  }

  /**
   * Log extraction failures for monitoring
   */
  static logFailure(context: string, content: string, error: string): void {
    // In production, this would send to telemetry service
    console.error('JSON Extraction Failure:', {
      context,
      contentLength: content.length,
      contentPreview: content.substring(0, 200),
      error,
      timestamp: new Date().toISOString()
    });
  }
}

import { ResilienceManager } from './resilience';

/**
 * Enhanced LLM response handler with retries and resilience
 */
export class RobustLLMHandler {
  private static MAX_RETRIES = 3;
  private static telemetry = TelemetryService.getInstance();
  private static resilience = ResilienceManager.getInstance();
  
  static async getStructuredResponse<T>(
    anthropic: Anthropic,
    prompt: string,
    schema: z.ZodSchema<T>,
    context: string
  ): Promise<T> {
    const circuitBreaker = this.resilience.getCircuitBreaker('anthropic-api');
    const rateLimiter = this.resilience.getRateLimiter('anthropic-api', {
      maxRequests: 50, // Adjust based on your API limits
      windowMs: 60000 // 1 minute
    });
    
    return await circuitBreaker.execute(async () => {
      return await rateLimiter.execute(async () => {
        return await this.executeWithRetries(anthropic, prompt, schema, context);
      });
    });
  }
  
  private static async executeWithRetries<T>(
    anthropic: Anthropic,
    prompt: string,
    schema: z.ZodSchema<T>,
    context: string
  ): Promise<T> {
    let lastError: string = '';
    const startTime = Date.now();
    
    for (let attempt = 0; attempt < this.MAX_RETRIES; attempt++) {
      try {
        // Add explicit JSON instructions on retry
        const enhancedPrompt = attempt === 0 
          ? prompt 
          : BulletproofJSONExtractor.createRetryPrompt(prompt, lastError);

        // Track API call
        this.telemetry.trackEvent('llm_api_call', {
          context,
          attempt,
          promptLength: enhancedPrompt.length
        });

        const response = await anthropic.messages.create({
          model: 'claude-3-sonnet-20240229',
          max_tokens: 4000,
          temperature: attempt === 0 ? 0.7 : 0.3, // Lower temperature on retry
          system: attempt === 0 
            ? 'You are a helpful assistant that generates project plans. Always respond with valid JSON in the specified format.'
            : 'You MUST respond with ONLY valid JSON. No explanations, no markdown, just JSON.',
          messages: [{
            role: 'user',
            content: enhancedPrompt
          }]
        });

        const content = response.content[0].type === 'text' ? response.content[0].text : '';
        const result = await BulletproofJSONExtractor.extract(content, schema, context);
        
        if (result.success && result.data) {
          // Track successful response
          this.telemetry.trackEvent('llm_api_success', {
            context,
            attempt,
            duration: Date.now() - startTime,
            extractionMethod: result.extractionMethod
          });
          return result.data;
        }
        
        lastError = result.error || 'Unknown extraction error';
      } catch (error) {
        lastError = error instanceof Error ? error.message : 'Unknown error';
        
        // Track API errors
        this.telemetry.trackEvent('llm_api_error', {
          context,
          attempt,
          error: lastError,
          duration: Date.now() - startTime
        });
      }
    }
    
    // Log failure for monitoring
    BulletproofJSONExtractor.logFailure(context, prompt, lastError);
    
    throw new Error(`Failed to get valid response after ${this.MAX_RETRIES} attempts. Last error: ${lastError}`);
  }
}