#!/usr/bin/env node
import { execSync } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.join(__dirname, '..');

async function fixImports(distDir) {
  const files = await fs.readdir(distDir, { recursive: true });
  
  for (const file of files) {
    const filePath = path.join(distDir, file);
    const stat = await fs.stat(filePath);
    
    if (stat.isFile() && file.endsWith('.js')) {
      let content = await fs.readFile(filePath, 'utf-8');
      
      // Fix all relative imports (both ./ and ../)
      content = content.replace(
        /from\s+['"](\.[\/\w.-]+)['"];?/g,
        (match, importPath) => {
          if (!importPath.endsWith('.js') && !importPath.endsWith('.json')) {
            // Resolve the actual path
            const fullPath = path.resolve(path.dirname(filePath), importPath);
            
            // Check if it's a file
            try {
              const stat = require('fs').statSync(fullPath + '.js');
              if (stat.isFile()) {
                return match.replace(importPath, importPath + '.js');
              }
            } catch {}
            
            // Check if it's a directory with index.js
            try {
              const stat = require('fs').statSync(fullPath);
              if (stat.isDirectory()) {
                const indexPath = path.join(fullPath, 'index.js');
                if (require('fs').existsSync(indexPath)) {
                  return match.replace(importPath, importPath + '/index.js');
                }
              }
            } catch {}
            
            // Default to .js extension
            return match.replace(importPath, importPath + '.js');
          }
          return match;
        }
      );
      
      // Fix import statements
      content = content.replace(
        /import\s+.*?from\s+['"](\.[\/\w.-]+)['"];?/g,
        (match, importPath) => {
          if (!importPath.endsWith('.js') && !importPath.endsWith('.json')) {
            const fullPath = path.resolve(path.dirname(filePath), importPath);
            
            try {
              const stat = require('fs').statSync(fullPath + '.js');
              if (stat.isFile()) {
                return match.replace(importPath, importPath + '.js');
              }
            } catch {}
            
            try {
              const stat = require('fs').statSync(fullPath);
              if (stat.isDirectory()) {
                const indexPath = path.join(fullPath, 'index.js');
                if (require('fs').existsSync(indexPath)) {
                  return match.replace(importPath, importPath + '/index.js');
                }
              }
            } catch {}
            
            return match.replace(importPath, importPath + '.js');
          }
          return match;
        }
      );
      
      // Fix export statements
      content = content.replace(
        /export\s+.*?from\s+['"](\.[\/\w.-]+)['"];?/g,
        (match, importPath) => {
          if (!importPath.endsWith('.js') && !importPath.endsWith('.json')) {
            const fullPath = path.resolve(path.dirname(filePath), importPath);
            
            try {
              const stat = require('fs').statSync(fullPath + '.js');
              if (stat.isFile()) {
                return match.replace(importPath, importPath + '.js');
              }
            } catch {}
            
            try {
              const stat = require('fs').statSync(fullPath);
              if (stat.isDirectory()) {
                const indexPath = path.join(fullPath, 'index.js');
                if (require('fs').existsSync(indexPath)) {
                  return match.replace(importPath, importPath + '/index.js');
                }
              }
            } catch {}
            
            return match.replace(importPath, importPath + '.js');
          }
          return match;
        }
      );
      
      // Fix dynamic imports
      content = content.replace(
        /import\s*\(\s*['"](\.[\/\w.-]+)['"]\s*\)/g,
        (match, importPath) => {
          if (!importPath.endsWith('.js') && !importPath.endsWith('.json')) {
            const fullPath = path.resolve(path.dirname(filePath), importPath);
            
            try {
              const stat = require('fs').statSync(fullPath + '.js');
              if (stat.isFile()) {
                return match.replace(importPath, importPath + '.js');
              }
            } catch {}
            
            try {
              const stat = require('fs').statSync(fullPath);
              if (stat.isDirectory()) {
                const indexPath = path.join(fullPath, 'index.js');
                if (require('fs').existsSync(indexPath)) {
                  return match.replace(importPath, importPath + '/index.js');
                }
              }
            } catch {}
            
            return match.replace(importPath, importPath + '.js');
          }
          return match;
        }
      );
      
      // Fix side-effect imports
      content = content.replace(
        /import\s+['"](\.[\/\w.-]+)['"];?/g,
        (match, importPath) => {
          if (!importPath.endsWith('.js') && !importPath.endsWith('.json') && !importPath.endsWith('.css')) {
            const fullPath = path.resolve(path.dirname(filePath), importPath);
            
            try {
              const stat = require('fs').statSync(fullPath + '.js');
              if (stat.isFile()) {
                return match.replace(importPath, importPath + '.js');
              }
            } catch {}
            
            return match.replace(importPath, importPath + '.js');
          }
          return match;
        }
      );
      
      await fs.writeFile(filePath, content);
    }
  }
}

async function validateBuild(distDir) {
  console.log('🔍 Validating build output...');
  const files = await fs.readdir(distDir, { recursive: true });
  const errors = [];
  
  for (const file of files) {
    if (file.endsWith('.js')) {
      const filePath = path.join(distDir, file);
      const content = await fs.readFile(filePath, 'utf-8');
      
      // Check for unresolved relative imports
      const patterns = [
        /from\s+['"](\.[\/\w.-]+)['"]/g,
        /export\s+.*from\s+['"](\.[\/\w.-]+)['"]/g,
        /import\s*\(\s*['"](\.[\/\w.-]+)['"]\s*\)/g
      ];
      
      for (const pattern of patterns) {
        let match;
        while ((match = pattern.exec(content)) !== null) {
          const importPath = match[1];
          if (!importPath.endsWith('.js') && 
              !importPath.endsWith('.json') && 
              !importPath.endsWith('.css')) {
            errors.push(`Missing .js extension in ${file}: ${match[0]}`);
          }
        }
      }
    }
  }
  
  if (errors.length > 0) {
    console.error('❌ Build validation failed:');
    errors.forEach(err => console.error(`   ${err}`));
    throw new Error('Import validation failed');
  }
  
  console.log('✅ Build validation passed');
}

async function buildForNPM() {
  console.log('🔨 Building Agent Team Composer for NPM...\n');
  
  try {
    // Clean dist directory
    console.log('📦 Cleaning dist directory...');
    await fs.rm(path.join(rootDir, 'dist'), { recursive: true, force: true });
    
    // Build frontend first (it might clean dist)
    console.log('🎨 Building frontend...');
    execSync('npm run build:dev', { stdio: 'inherit', cwd: rootDir });
    
    // Build TypeScript after frontend
    console.log('🔧 Compiling TypeScript...');
    execSync('npx tsc -p tsconfig.cli.json', { stdio: 'inherit', cwd: rootDir });
    
    // Fix ES module imports by adding .js extensions
    console.log('🔧 Fixing ES module imports...');
    await fixImports(path.join(rootDir, 'dist'));
    
    // Validate the build
    await validateBuild(path.join(rootDir, 'dist'));
    
    // Copy static files
    console.log('📄 Copying static files...');
    const staticFiles = [
      'product-lifecycle-agent-roles.md',
      'README-USAGE.md'
    ];
    
    for (const file of staticFiles) {
      const src = path.join(rootDir, file);
      const dest = path.join(rootDir, 'dist', file);
      
      if (await fs.access(src).then(() => true).catch(() => false)) {
        await fs.copyFile(src, dest);
      }
    }
    
    // Create package entry point
    console.log('📝 Creating package entry point...');
    const indexContent = `// Agent Team Composer - Main Entry Point
export * from './types/index.js';
export * from './services/github-service.js';
export * from './services/llm-orchestrator.js';
export * from './services/readme-parser.js';

// CLI is available via the 'agent-team-composer' command
console.log('Agent Team Composer - Use "npx agent-team-composer init" to get started');
`;
    
    await fs.writeFile(path.join(rootDir, 'dist', 'index.js'), indexContent);
    await fs.writeFile(path.join(rootDir, 'dist', 'index.d.ts'), indexContent.replace(/\.js/g, ''));
    
    // Update CLI shebang
    const cliPath = path.join(rootDir, 'dist', 'cli', 'index.js');
    
    // Wait for file to exist
    let attempts = 0;
    while (attempts < 10) {
      try {
        await fs.access(cliPath);
        break;
      } catch {
        attempts++;
        if (attempts === 10) {
          throw new Error(`CLI file not found at ${cliPath} after TypeScript compilation`);
        }
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    
    const cliContent = await fs.readFile(cliPath, 'utf-8');
    if (!cliContent.startsWith('#!/usr/bin/env node')) {
      await fs.writeFile(cliPath, '#!/usr/bin/env node\n' + cliContent);
    }
    
    // Make CLI executable
    await fs.chmod(cliPath, '755');
    
    // Create bin directory and entry point
    console.log('📦 Creating bin entry point...');
    const binDir = path.join(rootDir, 'bin');
    await fs.mkdir(binDir, { recursive: true });
    
    const binContent = `#!/usr/bin/env node
import('../dist/cli/index.js');
`;
    
    const binPath = path.join(binDir, 'agent-team-composer.js');
    await fs.writeFile(binPath, binContent);
    await fs.chmod(binPath, '755');
    
    // Test the CLI actually works
    console.log('🧪 Testing CLI execution...');
    try {
      execSync('node bin/agent-team-composer.js --version', { 
        stdio: 'pipe', 
        cwd: rootDir 
      });
      console.log('✅ CLI execution test passed');
    } catch (error) {
      console.error('❌ CLI execution test failed:', error.message);
      throw error;
    }
    
    console.log('\n✅ Build complete! Ready for NPM publish.\n');
    console.log('To test locally:');
    console.log('  npm link');
    console.log('  agent-team-composer init\n');
    console.log('To publish:');
    console.log('  npm publish\n');
    
  } catch (error) {
    console.error('❌ Build failed:', error.message);
    process.exit(1);
  }
}

buildForNPM();