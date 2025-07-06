import { execSync } from 'child_process';

export interface EnvironmentCheck {
  isValid: boolean;
  missing: string[];
  warnings: string[];
}

export async function validateEnvironment(skipGhCheck: boolean = false): Promise<EnvironmentCheck> {
  const missing: string[] = [];
  const warnings: string[] = [];

  // Check for Anthropic API key
  if (!process.env.ANTHROPIC_API_KEY) {
    missing.push('ANTHROPIC_API_KEY environment variable');
  }

  // Check for GitHub CLI (unless skipped)
  if (!skipGhCheck) {
    try {
      execSync('gh --version', { stdio: 'ignore' });
      
      // Check if GitHub CLI is authenticated
      try {
        execSync('gh auth status', { stdio: 'ignore' });
      } catch (error) {
        warnings.push('GitHub CLI is not authenticated. Run: gh auth login');
      }
    } catch (error) {
      missing.push('GitHub CLI');
    }
  }

  // Check for Node.js version
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.split('.')[0].substring(1));
  if (majorVersion < 16) {
    missing.push(`Node.js 16+ (current: ${nodeVersion})`);
  }

  // Check for Git
  try {
    execSync('git --version', { stdio: 'ignore' });
  } catch (error) {
    warnings.push('Git is not installed (optional but recommended)');
  }

  // Check if we're in a git repository
  try {
    execSync('git rev-parse --git-dir', { stdio: 'ignore' });
  } catch (error) {
    warnings.push('Not in a git repository (some features may be limited)');
  }

  return {
    isValid: missing.length === 0,
    missing,
    warnings
  };
}

export function setupGitHubCLI(): void {
  // This function could help users install GitHub CLI
  console.log('\nTo install GitHub CLI:');
  console.log('- macOS: brew install gh');
  console.log('- Windows: winget install --id GitHub.cli');
  console.log('- Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md');
  console.log('\nAfter installation, authenticate with: gh auth login');
}