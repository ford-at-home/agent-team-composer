interface TelemetryEvent {
  event: string;
  properties: Record<string, unknown>;
  timestamp: Date;
  sessionId?: string;
  userId?: string;
}

interface ExtractionMetrics {
  method: string;
  success: boolean;
  duration: number;
  retryCount: number;
  context: string;
  errorType?: string;
  contentLength?: number;
}

export class TelemetryService {
  private static instance: TelemetryService;
  private events: TelemetryEvent[] = [];
  private metrics: ExtractionMetrics[] = [];
  private sessionId: string;
  
  private constructor() {
    this.sessionId = this.generateSessionId();
  }

  static getInstance(): TelemetryService {
    if (!TelemetryService.instance) {
      TelemetryService.instance = new TelemetryService();
    }
    return TelemetryService.instance;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  }

  trackEvent(event: string, properties: Record<string, unknown> = {}): void {
    const telemetryEvent: TelemetryEvent = {
      event,
      properties,
      timestamp: new Date(),
      sessionId: this.sessionId
    };

    this.events.push(telemetryEvent);
    
    // In production, send to analytics service
    if (process.env.NODE_ENV === 'production') {
      this.sendToAnalytics(telemetryEvent);
    } else {
      console.debug('[Telemetry]', event, properties);
    }
  }

  trackExtractionMetrics(metrics: ExtractionMetrics): void {
    this.metrics.push(metrics);
    
    // Track patterns for improvement
    if (!metrics.success) {
      this.trackEvent('extraction_failure', {
        method: metrics.method,
        context: metrics.context,
        errorType: metrics.errorType,
        duration: metrics.duration
      });
    }
  }

  getExtractionSuccessRate(): number {
    if (this.metrics.length === 0) return 0;
    const successful = this.metrics.filter(m => m.success).length;
    return (successful / this.metrics.length) * 100;
  }

  getMethodSuccessRates(): Record<string, number> {
    const methodGroups = this.groupBy(this.metrics, 'method');
    const rates: Record<string, number> = {};
    
    for (const [method, metrics] of Object.entries(methodGroups)) {
      const successful = metrics.filter(m => m.success).length;
      rates[method] = (successful / metrics.length) * 100;
    }
    
    return rates;
  }

  getMostCommonErrors(): Array<{ error: string; count: number }> {
    const errors = this.metrics
      .filter(m => !m.success && m.errorType)
      .map(m => m.errorType!);
    
    const errorCounts = errors.reduce((acc, error) => {
      acc[error] = (acc[error] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return Object.entries(errorCounts)
      .map(([error, count]) => ({ error, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }

  private groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
    return array.reduce((result, item) => {
      const group = String(item[key]);
      if (!result[group]) result[group] = [];
      result[group].push(item);
      return result;
    }, {} as Record<string, T[]>);
  }

  private async sendToAnalytics(event: TelemetryEvent): Promise<void> {
    // In production, this would send to your analytics service
    // For now, we'll just log to a file or remote service
    try {
      // Example: await fetch('https://analytics.yourservice.com/track', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(event)
      // });
    } catch (error) {
      console.error('Failed to send telemetry:', error);
    }
  }

  generateDailyReport(): string {
    const report = {
      sessionId: this.sessionId,
      date: new Date().toISOString(),
      totalEvents: this.events.length,
      extractionMetrics: {
        totalAttempts: this.metrics.length,
        successRate: this.getExtractionSuccessRate(),
        methodSuccessRates: this.getMethodSuccessRates(),
        commonErrors: this.getMostCommonErrors(),
        averageRetries: this.metrics.reduce((sum, m) => sum + m.retryCount, 0) / this.metrics.length || 0
      },
      eventSummary: this.events.reduce((acc, event) => {
        acc[event.event] = (acc[event.event] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    };

    return JSON.stringify(report, null, 2);
  }
}