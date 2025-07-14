#!/usr/bin/env node

import { exec } from 'child_process';
import { promisify } from 'util';
import chokidar from 'chokidar';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = path.join(__dirname, '..');

let isBuilding = false;

async function rebuild() {
  if (isBuilding) return;
  isBuilding = true;

  console.log('🔄 Detected changes, rebuilding...');
  
  try {
    // Build the project
    console.log('📦 Building project...');
    await execAsync('npm run build', { cwd: projectRoot });
    
    // Re-link globally
    console.log('🔗 Re-linking package...');
    await execAsync('npm unlink -g agent-team-composer', { cwd: projectRoot }).catch(() => {});
    await execAsync('npm link', { cwd: projectRoot });
    
    console.log('✅ Ready! Changes are now available in your test workspace');
    console.log('');
  } catch (error) {
    console.error('❌ Build failed:', error.message);
  } finally {
    isBuilding = false;
  }
}

// Watch for changes
const watcher = chokidar.watch([
  path.join(projectRoot, 'src/**/*.{ts,tsx,js,jsx,css}'),
  path.join(projectRoot, 'package.json')
], {
  ignored: [
    /node_modules/,
    /dist/,
    /\.git/
  ],
  persistent: true,
  ignoreInitial: true
});

console.log('👀 Watching for changes...');
console.log('📍 Any changes will automatically rebuild and re-link the package');
console.log('🚀 Test in your other workspace with: agent-team-composer init');
console.log('');

// Initial build
rebuild();

watcher.on('change', (path) => {
  console.log(`📝 Changed: ${path}`);
  rebuild();
});

// Handle exit
process.on('SIGINT', () => {
  console.log('\n👋 Stopping auto-deploy...');
  watcher.close();
  process.exit(0);
});