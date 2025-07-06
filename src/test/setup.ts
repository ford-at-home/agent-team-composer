import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock environment variables
process.env.ANTHROPIC_API_KEY = 'test-api-key';
process.env.GITHUB_TOKEN = 'test-github-token';

// Mock fetch globally
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: async () => ({}),
    text: async () => '',
    headers: new Headers(),
    status: 200,
    statusText: 'OK',
  } as Response)
);

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
  debug: vi.fn()
};

// Mock pointer events for jsdom (Radix UI compatibility)
if (typeof window !== 'undefined') {
  Object.defineProperty(window.Element.prototype, 'hasPointerCapture', {
    value: vi.fn(),
  });

  Object.defineProperty(window.Element.prototype, 'setPointerCapture', {
    value: vi.fn(),
  });

  Object.defineProperty(window.Element.prototype, 'releasePointerCapture', {
    value: vi.fn(),
  });
}

// Increase default test timeout
vi.setConfig({ testTimeout: 10000 });