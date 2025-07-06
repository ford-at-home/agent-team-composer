#!/usr/bin/env node
import { readdir, readFile } from 'fs/promises';
import { join } from 'path';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.join(__dirname, '..');

async function validateImports(dir) {
  const files = await readdir(dir, { recursive: true });
  const errors = [];
  const warnings = [];
  
  for (const file of files) {
    if (file.endsWith('.js')) {
      const filePath = join(dir, file);
      const content = await readFile(filePath, 'utf-8');
      
      // Check for relative imports without .js extension
      const importPatterns = [
        // Regular imports - check if the path doesn't end with .js
        { pattern: /from\s+['"](\.[\/\w.-]+)['"]/g, type: 'import' },
        // Dynamic imports
        { pattern: /import\s*\(\s*['"](\.[\/\w.-]+)['"]\s*\)/g, type: 'dynamic' },
        // Export statements
        { pattern: /export\s+.*from\s+['"](\.[\/\w.-]+)['"]/g, type: 'export' },
        // Side-effect imports
        { pattern: /import\s+['"](\.[\/\w.-]+)['"]/g, type: 'side-effect' }
      ];
      
      for (const { pattern, type } of importPatterns) {
        let match;
        while ((match = pattern.exec(content)) !== null) {
          const importPath = match[1];
          // Only flag if it doesn't end with .js, .json, or .css
          if (!importPath.endsWith('.js') && 
              !importPath.endsWith('.json') && 
              !importPath.endsWith('.css')) {
            errors.push({
              file,
              line: content.substring(0, match.index).split('\n').length,
              import: match[0],
              path: importPath,
              type
            });
          }
        }
      }
      
      // Check for @/ imports (path aliases that shouldn't be in dist)
      const aliasImports = content.match(/from\s+['"]@\/[^'"]+['"]/g) || [];
      for (const imp of aliasImports) {
        warnings.push({
          file,
          import: imp,
          message: 'Path alias found in dist - should be resolved to relative path'
        });
      }
    }
  }
  
  return { errors, warnings };
}

async function validatePackageStructure(distDir) {
  const requiredFiles = [
    'cli/index.js',
    'index.js',
    'index.d.ts'
  ];
  
  const missing = [];
  for (const file of requiredFiles) {
    try {
      await readFile(join(distDir, file));
    } catch {
      missing.push(file);
    }
  }
  
  return missing;
}

async function main() {
  console.log('🔍 Validating build output...\n');
  
  const distDir = path.join(rootDir, 'dist');
  
  // Check package structure
  const missingFiles = await validatePackageStructure(distDir);
  if (missingFiles.length > 0) {
    console.error('❌ Missing required files:');
    missingFiles.forEach(file => console.error(`   - ${file}`));
    console.log();
  }
  
  // Validate imports
  const { errors, warnings } = await validateImports(distDir);
  
  if (warnings.length > 0) {
    console.warn('⚠️  Build warnings:');
    warnings.forEach(({ file, import: imp, message }) => {
      console.warn(`   ${file}: ${message}`);
      console.warn(`     ${imp}`);
    });
    console.log();
  }
  
  if (errors.length > 0) {
    console.error('❌ Import validation failed:');
    errors.forEach(({ file, line, import: imp, path }) => {
      console.error(`   ${file}:${line} - Missing .js extension for '${path}'`);
      console.error(`     ${imp}`);
    });
    console.log();
    console.error(`Total errors: ${errors.length}`);
    process.exit(1);
  }
  
  if (missingFiles.length === 0 && errors.length === 0) {
    console.log('✅ Build validation passed!');
    console.log(`   - All imports have proper extensions`);
    console.log(`   - Package structure is correct`);
    if (warnings.length > 0) {
      console.log(`   - ${warnings.length} warnings found (non-critical)`);
    }
  }
}

main().catch(error => {
  console.error('❌ Validation script failed:', error);
  process.exit(1);
});