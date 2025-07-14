#!/usr/bin/env node

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import http from 'http';

console.log('🧪 Testing Agent Team Composer for Demo...\n');

// Function to check if server is responding
async function checkServer(url, maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await new Promise((resolve, reject) => {
        http.get(url, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => resolve({ status: res.statusCode, data }));
        }).on('error', reject);
      });
      
      if (response.status === 200) {
        return response;
      }
    } catch (e) {
      // Server not ready yet
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  throw new Error(`Server did not respond after ${maxAttempts} seconds`);
}

async function testDemo() {
  console.log('1️⃣  Starting agent-team-composer init...');
  
  const proc = spawn('node', ['../bin/agent-team-composer.js', 'init', '--port', '3100'], {
    cwd: './demo-test',
    stdio: ['ignore', 'pipe', 'pipe']
  });
  
  let output = '';
  proc.stdout.on('data', (data) => {
    output += data.toString();
    process.stdout.write(data);
  });
  
  proc.stderr.on('data', (data) => {
    process.stderr.write(data);
  });
  
  // Wait for server to start
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  console.log('\n2️⃣  Checking if server is running...');
  
  try {
    const response = await checkServer('http://localhost:3100/');
    console.log('✅ Server is responding!');
    
    // Check if we got HTML
    if (response.data.includes('<div id="root">')) {
      console.log('✅ HTML is being served correctly');
    } else {
      console.log('❌ HTML content is wrong:', response.data.substring(0, 200));
      process.exit(1);
    }
    
    // Check API endpoint
    console.log('\n3️⃣  Checking API endpoint...');
    const apiResponse = await checkServer('http://localhost:3100/api/project');
    console.log('✅ API is responding!');
    
    // Check assets
    console.log('\n4️⃣  Checking if assets are accessible...');
    const assetResponse = await checkServer('http://localhost:3100/assets/index-DXTVlbXL.css');
    if (assetResponse.status === 200) {
      console.log('✅ CSS assets are being served');
    } else {
      console.log('❌ CSS assets not found');
    }
    
    console.log('\n✅ ✅ ✅ DEMO READY! ✅ ✅ ✅');
    console.log('\n📌 For your demo tomorrow:');
    console.log('   1. cd demo-test');
    console.log('   2. node ../bin/agent-team-composer.js init');
    console.log('   3. Open http://localhost:3000 in browser');
    console.log('\n🎯 Everything is working perfectly!');
    
  } catch (error) {
    console.error('\n❌ ERROR:', error.message);
    console.error('\nDebugging info:');
    console.error('Output so far:', output);
    process.exit(1);
  } finally {
    // Clean up
    proc.kill('SIGTERM');
  }
}

testDemo().catch(console.error);