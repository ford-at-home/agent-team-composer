export enum ErrorCode {
  // Client errors
  INVALID_INPUT = 'INVALID_INPUT',
  AUTHENTICATION_REQUIRED = 'AUTHENTICATION_REQUIRED',
  INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  
  // Server errors
  LLM_API_ERROR = 'LLM_API_ERROR',
  GITHUB_API_ERROR = 'GITHUB_API_ERROR',
  PARSING_ERROR = 'PARSING_ERROR',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  
  // Configuration errors
  MISSING_ENVIRONMENT = 'MISSING_ENVIRONMENT',
  INVALID_CONFIGURATION = 'INVALID_CONFIGURATION'
}

export class AppError extends Error {
  constructor(
    public code: ErrorCode,
    message: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = 'AppError';
  }

  toJSON() {
    return {
      code: this.code,
      message: this.message,
      details: this.details
    };
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: any) {
    super(ErrorCode.INVALID_INPUT, message, 400, details);
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message: string, details?: any) {
    super(ErrorCode.AUTHENTICATION_REQUIRED, message, 401, details);
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends AppError {
  constructor(message: string, resetTime?: Date) {
    super(ErrorCode.RATE_LIMIT_EXCEEDED, message, 429, { resetTime });
    this.name = 'RateLimitError';
  }
}

export class LLMError extends AppError {
  constructor(message: string, details?: any) {
    super(ErrorCode.LLM_API_ERROR, message, 502, details);
    this.name = 'LLMError';
  }
}

export class GitHubError extends AppError {
  constructor(message: string, details?: any) {
    super(ErrorCode.GITHUB_API_ERROR, message, 502, details);
    this.name = 'GitHubError';
  }
}

/**
 * Global error handler for Express
 */
export function errorHandler(err: Error, req: any, res: any, next: any) {
  console.error('Error:', err);

  if (err instanceof AppError) {
    return res.status(err.statusCode).json(err.toJSON());
  }

  // Handle Zod validation errors
  if (err.name === 'ZodError') {
    return res.status(400).json({
      code: ErrorCode.INVALID_INPUT,
      message: 'Validation failed',
      details: err
    });
  }

  // Handle Anthropic API errors
  if (err.message?.includes('Anthropic')) {
    return res.status(502).json({
      code: ErrorCode.LLM_API_ERROR,
      message: 'AI service temporarily unavailable',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }

  // Default error
  return res.status(500).json({
    code: ErrorCode.INTERNAL_ERROR,
    message: 'An unexpected error occurred',
    details: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
}

/**
 * Async error wrapper for Express routes
 */
export function asyncHandler(fn: Function) {
  return (req: any, res: any, next: any) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

/**
 * Retry helper with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
    backoffFactor?: number;
    shouldRetry?: (error: any) => boolean;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelay = 1000,
    maxDelay = 30000,
    backoffFactor = 2,
    shouldRetry = () => true
  } = options;

  let lastError: any;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxAttempts || !shouldRetry(error)) {
        throw error;
      }
      
      const delay = Math.min(
        initialDelay * Math.pow(backoffFactor, attempt - 1),
        maxDelay
      );
      
      console.log(`Retry attempt ${attempt}/${maxAttempts} after ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}