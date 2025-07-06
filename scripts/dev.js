#!/usr/bin/env node
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');

// Start Vite dev server
const vite = spawn('npm', ['run', 'dev'], {
  cwd: rootDir,
  stdio: 'inherit',
  shell: true
});

// Start backend server
const server = spawn('npx', ['tsx', 'src/server/dev.ts'], {
  cwd: rootDir,
  stdio: 'inherit',
  shell: true,
  env: { ...process.env, NODE_ENV: 'development' }
});

// Handle cleanup
process.on('SIGINT', () => {
  vite.kill();
  server.kill();
  process.exit();
});

console.log('🚀 Starting Agent Team Composer development environment...');
console.log('📱 Frontend: http://localhost:5173');
console.log('🔧 Backend: http://localhost:3000');
console.log('\nPress Ctrl+C to stop all servers');