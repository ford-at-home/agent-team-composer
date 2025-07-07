import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { validateEnvironment, setupGitHubCLI } from '../environment';
import { execSync } from 'child_process';

// Mock child_process
vi.mock('child_process', () => ({
  execSync: vi.fn()
}));

describe('validateEnvironment', () => {
  const originalEnv = process.env;
  const mockExecSync = execSync as any;

  beforeEach(() => {
    // Reset environment
    process.env = { ...originalEnv };
    vi.clearAllMocks();
    
    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.restoreAllMocks();
  });

  describe('environment variable checks', () => {
    it('should report missing ANTHROPIC_API_KEY', async () => {
      delete process.env.ANTHROPIC_API_KEY;
      mockExecSync.mockImplementation(() => {}); // All commands succeed

      const result = await validateEnvironment();

      expect(result.isValid).toBe(false);
      expect(result.missing).toContain('ANTHROPIC_API_KEY environment variable');
    });

    it('should pass when ANTHROPIC_API_KEY is present', async () => {
      process.env.ANTHROPIC_API_KEY = 'test-key';
      mockExecSync.mockImplementation(() => {});

      const result = await validateEnvironment();

      expect(result.missing).not.toContain('ANTHROPIC_API_KEY environment variable');
    });
  });

  describe('GitHub CLI checks', () => {
    beforeEach(() => {
      process.env.ANTHROPIC_API_KEY = 'test-key';
    });

    it('should report missing GitHub CLI when gh command fails', async () => {
      mockExecSync.mockImplementation((cmd: string) => {
        if (cmd === 'gh --version') {
          throw new Error('Command not found');
        }
      });

      const result = await validateEnvironment();

      expect(result.isValid).toBe(false);
      expect(result.missing).toContain('GitHub CLI');
    });

    it('should check GitHub CLI authentication status', async () => {
      mockExecSync.mockImplementation((cmd: string) => {
        if (cmd === 'gh auth status') {
          throw new Error('Not authenticated');
        }
      });

      const result = await validateEnvironment();

      expect(result.warnings).toContain('GitHub CLI is not authenticated. Run: gh auth login');
      expect(result.isValid).toBe(true); // Warnings don't affect validity
    });

    it('should pass when GitHub CLI is installed and authenticated', async () => {
      mockExecSync.mockImplementation(() => {}); // All commands succeed

      const result = await validateEnvironment();

      expect(result.missing).not.toContain('GitHub CLI');
      expect(result.warnings).not.toContain('GitHub CLI is not authenticated. Run: gh auth login');
    });

    it('should skip GitHub CLI check when skipGhCheck is true', async () => {
      mockExecSync.mockImplementation((cmd: string) => {
        if (cmd.includes('gh')) {
          throw new Error('Should not be called');
        }
      });

      const result = await validateEnvironment(true);

      expect(result.missing).not.toContain('GitHub CLI');
      expect(result.warnings).toHaveLength(0);
    });
  });

  describe('Node.js version checks', () => {
    beforeEach(() => {
      process.env.ANTHROPIC_API_KEY = 'test-key';
    });

    it('should report old Node.js version', async () => {
      // Mock Node.js version 14
      Object.defineProperty(process, 'version', {
        value: 'v14.17.0',
        configurable: true
      });
      mockExecSync.mockImplementation(() => {});

      const result = await validateEnvironment();

      expect(result.isValid).toBe(false);
      expect(result.missing).toContain('Node.js 16+ (current: v14.17.0)');
    });

    it('should accept Node.js 16', async () => {
      Object.defineProperty(process, 'version', {
        value: 'v16.0.0',
        configurable: true
      });
      mockExecSync.mockImplementation(() => {});

      const result = await validateEnvironment();

      expect(result.missing).not.toContain(expect.stringMatching(/Node\.js 16\+/));
    });

    it('should accept Node.js 18', async () => {
      Object.defineProperty(process, 'version', {
        value: 'v18.12.0',
        configurable: true
      });
      mockExecSync.mockImplementation(() => {});

      const result = await validateEnvironment();

      expect(result.missing).not.toContain(expect.stringMatching(/Node\.js 16\+/));
    });

    it('should accept Node.js 20', async () => {
      Object.defineProperty(process, 'version', {
        value: 'v20.0.0',
        configurable: true
      });
      mockExecSync.mockImplementation(() => {});

      const result = await validateEnvironment();

      expect(result.missing).not.toContain(expect.stringMatching(/Node\.js 16\+/));
    });
  });

  describe('Git checks', () => {
    beforeEach(() => {
      process.env.ANTHROPIC_API_KEY = 'test-key';
    });

    it('should warn when Git is not installed', async () => {
      mockExecSync.mockImplementation((cmd: string) => {
        if (cmd === 'git --version') {
          throw new Error('Command not found');
        }
      });

      const result = await validateEnvironment();

      expect(result.warnings).toContain('Git is not installed (optional but recommended)');
      expect(result.isValid).toBe(true); // Git is optional
    });

    it('should warn when not in a git repository', async () => {
      mockExecSync.mockImplementation((cmd: string) => {
        if (cmd === 'git rev-parse --git-dir') {
          throw new Error('Not a git repository');
        }
      });

      const result = await validateEnvironment();

      expect(result.warnings).toContain('Not in a git repository (some features may be limited)');
    });

    it('should not warn when Git is installed and in a repository', async () => {
      mockExecSync.mockImplementation(() => {}); // All commands succeed

      const result = await validateEnvironment();

      expect(result.warnings).not.toContain('Git is not installed (optional but recommended)');
      expect(result.warnings).not.toContain('Not in a git repository (some features may be limited)');
    });
  });

  describe('complex scenarios', () => {
    it('should handle multiple missing requirements', async () => {
      delete process.env.ANTHROPIC_API_KEY;
      Object.defineProperty(process, 'version', {
        value: 'v14.0.0',
        configurable: true
      });
      mockExecSync.mockImplementation((cmd: string) => {
        if (cmd === 'gh --version') {
          throw new Error('Command not found');
        }
      });

      const result = await validateEnvironment();

      expect(result.isValid).toBe(false);
      expect(result.missing).toHaveLength(3);
      expect(result.missing).toContain('ANTHROPIC_API_KEY environment variable');
      expect(result.missing).toContain('GitHub CLI');
      expect(result.missing).toContain('Node.js 16+ (current: v14.0.0)');
    });

    it('should handle all requirements met', async () => {
      process.env.ANTHROPIC_API_KEY = 'test-key';
      Object.defineProperty(process, 'version', {
        value: 'v18.0.0',
        configurable: true
      });
      mockExecSync.mockImplementation(() => {}); // All commands succeed

      const result = await validateEnvironment();

      expect(result.isValid).toBe(true);
      expect(result.missing).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
    });

    it('should be valid with warnings only', async () => {
      process.env.ANTHROPIC_API_KEY = 'test-key';
      mockExecSync.mockImplementation((cmd: string) => {
        if (cmd === 'gh auth status') {
          throw new Error('Not authenticated');
        }
        if (cmd === 'git --version') {
          throw new Error('Command not found');
        }
      });

      const result = await validateEnvironment();

      expect(result.isValid).toBe(true);
      expect(result.missing).toHaveLength(0);
      expect(result.warnings).toHaveLength(2);
    });
  });

  describe('command execution', () => {
    it('should use ignore stdio option for all commands', async () => {
      process.env.ANTHROPIC_API_KEY = 'test-key';
      mockExecSync.mockImplementation(() => {});

      await validateEnvironment();

      // Verify all execSync calls used stdio: 'ignore'
      expect(mockExecSync).toHaveBeenCalledWith('gh --version', { stdio: 'ignore' });
      expect(mockExecSync).toHaveBeenCalledWith('gh auth status', { stdio: 'ignore' });
      expect(mockExecSync).toHaveBeenCalledWith('git --version', { stdio: 'ignore' });
      expect(mockExecSync).toHaveBeenCalledWith('git rev-parse --git-dir', { stdio: 'ignore' });
    });
  });
});

describe('setupGitHubCLI', () => {
  beforeEach(() => {
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should log installation instructions', () => {
    setupGitHubCLI();

    expect(console.log).toHaveBeenCalledWith('\nTo install GitHub CLI:');
    expect(console.log).toHaveBeenCalledWith('- macOS: brew install gh');
    expect(console.log).toHaveBeenCalledWith('- Windows: winget install --id GitHub.cli');
    expect(console.log).toHaveBeenCalledWith('- Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md');
    expect(console.log).toHaveBeenCalledWith('\nAfter installation, authenticate with: gh auth login');
  });

  it('should be called exactly 5 times', () => {
    setupGitHubCLI();

    expect(console.log).toHaveBeenCalledTimes(5);
  });
});