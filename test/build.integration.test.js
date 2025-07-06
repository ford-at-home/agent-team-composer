import { describe, test, expect, beforeAll } from 'vitest';
import { execSync } from 'child_process';
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.join(__dirname, '..');

describe('Build Integration Tests', () => {
  beforeAll(() => {
    // Build the package
    execSync('npm run build:npm', { 
      cwd: rootDir,
      stdio: 'pipe'
    });
  });

  test('CLI can be executed after build', () => {
    const result = execSync('node bin/agent-team-composer.js --version', {
      cwd: rootDir,
      encoding: 'utf-8'
    });
    expect(result.trim()).toMatch(/^\d+\.\d+\.\d+$/);
  });

  test('CLI help command works', () => {
    const result = execSync('node bin/agent-team-composer.js --help', {
      cwd: rootDir,
      encoding: 'utf-8'
    });
    expect(result).toContain('agent-team-composer');
    expect(result).toContain('init');
    expect(result).toContain('validate');
  });

  test('All required files exist in dist', () => {
    const requiredFiles = [
      'dist/cli/index.js',
      'dist/index.js',
      'dist/index.d.ts',
      'dist/services/github-service.js',
      'dist/services/llm-orchestrator.js',
      'dist/services/prompt-sanitizer.js',
      'dist/services/readme-parser.js'
    ];

    for (const file of requiredFiles) {
      const filePath = join(rootDir, file);
      expect(existsSync(filePath), `Missing file: ${file}`).toBe(true);
    }
  });

  test('All imports have .js extensions', () => {
    const distDir = join(rootDir, 'dist');
    const checkFile = (filePath) => {
      if (!filePath.endsWith('.js')) return;
      
      const content = readFileSync(filePath, 'utf-8');
      const relativeImports = content.match(/from\s+['"](\.[\/\w.-]+)['"]/g) || [];
      
      for (const imp of relativeImports) {
        const importPath = imp.match(/['"](\.[\/\w.-]+)['"]/)[1];
        if (!importPath.endsWith('.json') && !importPath.endsWith('.css')) {
          expect(importPath).toMatch(/\.js$/);
        }
      }
    };

    // Check key files
    checkFile(join(distDir, 'cli/index.js'));
    checkFile(join(distDir, 'services/llm-orchestrator.js'));
    checkFile(join(distDir, 'services/github-service.js'));
  });

  test('Package can be imported as ESM module', async () => {
    // Dynamic import to test ESM compatibility
    const module = await import(join(rootDir, 'dist/index.js'));
    expect(module).toBeDefined();
    expect(module.LLMOrchestrator).toBeDefined();
  });

  test('No path aliases (@/) in dist files', () => {
    const distDir = join(rootDir, 'dist');
    const checkFile = (filePath) => {
      if (!filePath.endsWith('.js')) return;
      
      const content = readFileSync(filePath, 'utf-8');
      const aliasImports = content.match(/from\s+['"]@\/[^'"]+['"]/g) || [];
      
      expect(aliasImports.length).toBe(0);
    };

    checkFile(join(distDir, 'cli/index.js'));
    checkFile(join(distDir, 'services/llm-orchestrator.js'));
  });
});