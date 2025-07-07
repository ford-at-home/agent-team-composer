interface CircuitBreakerOptions {
  failureThreshold: number;
  resetTimeout: number;
  halfOpenRequests: number;
}

interface RateLimiterOptions {
  maxRequests: number;
  windowMs: number;
}

export class CircuitBreaker {
  private failures = 0;
  private successes = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private nextAttempt = Date.now();
  private halfOpenAttempts = 0;

  constructor(private options: CircuitBreakerOptions) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN - service unavailable');
      }
      this.state = 'half-open';
      this.halfOpenAttempts = 0;
    }

    if (this.state === 'half-open' && this.halfOpenAttempts >= this.options.halfOpenRequests) {
      // Enough successful requests in half-open state, close the circuit
      if (this.successes >= this.options.halfOpenRequests) {
        this.close();
      } else {
        this.open();
        throw new Error('Circuit breaker is OPEN - service still failing');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    if (this.state === 'half-open') {
      this.successes++;
      this.halfOpenAttempts++;
      if (this.successes >= this.options.halfOpenRequests) {
        this.close();
      }
    }
  }

  private onFailure(): void {
    this.failures++;
    this.successes = 0;
    if (this.failures >= this.options.failureThreshold) {
      this.open();
    }
  }

  private open(): void {
    this.state = 'open';
    this.nextAttempt = Date.now() + this.options.resetTimeout;
    console.warn(`Circuit breaker opened. Will retry after ${new Date(this.nextAttempt).toISOString()}`);
  }

  private close(): void {
    this.state = 'closed';
    this.failures = 0;
    this.successes = 0;
    console.info('Circuit breaker closed');
  }

  getState(): string {
    return this.state;
  }
}

export class RateLimiter {
  private requests: number[] = [];

  constructor(private options: RateLimiterOptions) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    const now = Date.now();
    
    // Remove old requests outside the window
    this.requests = this.requests.filter(time => now - time < this.options.windowMs);
    
    // Check if we're at the limit
    if (this.requests.length >= this.options.maxRequests) {
      const oldestRequest = this.requests[0];
      const waitTime = this.options.windowMs - (now - oldestRequest);
      throw new Error(`Rate limit exceeded. Try again in ${Math.ceil(waitTime / 1000)} seconds`);
    }
    
    // Add current request
    this.requests.push(now);
    
    // Execute the function
    return await fn();
  }

  getRemainingRequests(): number {
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.options.windowMs);
    return Math.max(0, this.options.maxRequests - this.requests.length);
  }
}

// Singleton instances for global rate limiting
export class ResilienceManager {
  private static instance: ResilienceManager;
  private circuitBreakers = new Map<string, CircuitBreaker>();
  private rateLimiters = new Map<string, RateLimiter>();

  static getInstance(): ResilienceManager {
    if (!ResilienceManager.instance) {
      ResilienceManager.instance = new ResilienceManager();
    }
    return ResilienceManager.instance;
  }

  getCircuitBreaker(key: string, options?: CircuitBreakerOptions): CircuitBreaker {
    if (!this.circuitBreakers.has(key)) {
      this.circuitBreakers.set(key, new CircuitBreaker(options || {
        failureThreshold: 5,
        resetTimeout: 60000, // 1 minute
        halfOpenRequests: 3
      }));
    }
    return this.circuitBreakers.get(key)!;
  }

  getRateLimiter(key: string, options?: RateLimiterOptions): RateLimiter {
    if (!this.rateLimiters.has(key)) {
      this.rateLimiters.set(key, new RateLimiter(options || {
        maxRequests: 10,
        windowMs: 60000 // 1 minute
      }));
    }
    return this.rateLimiters.get(key)!;
  }

  getStatus(): Record<string, unknown> {
    const status: Record<string, unknown> = {
      circuitBreakers: {},
      rateLimiters: {}
    };

    this.circuitBreakers.forEach((cb, key) => {
      status.circuitBreakers[key] = cb.getState();
    });

    this.rateLimiters.forEach((rl, key) => {
      status.rateLimiters[key] = rl.getRemainingRequests();
    });

    return status;
  }
}