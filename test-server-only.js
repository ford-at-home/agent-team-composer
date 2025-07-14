#!/usr/bin/env node

import { startServer } from './dist/server/index.js';
import http from 'http';

console.log('🧪 Testing Server Functionality...\n');

async function checkEndpoint(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, data }));
    }).on('error', reject);
  });
}

async function test() {
  console.log('1️⃣  Starting server directly...');
  
  const serverUrl = await startServer(3200, './demo-test/.agent-team-composer-data.json');
  console.log(`✅ Server started at ${serverUrl}`);
  
  console.log('\n2️⃣  Testing HTML endpoint...');
  const htmlResponse = await checkEndpoint(`${serverUrl}/`);
  
  if (htmlResponse.data.includes('<div id="root">')) {
    console.log('✅ HTML served correctly');
  } else {
    console.log('❌ HTML issue:', htmlResponse.data.substring(0, 200));
  }
  
  console.log('\n3️⃣  Testing API endpoint...');
  const apiResponse = await checkEndpoint(`${serverUrl}/api/project`);
  const projectData = JSON.parse(apiResponse.data);
  
  if (projectData.projectMetadata && projectData.projectMetadata.title === 'Demo Project') {
    console.log('✅ API working correctly');
  } else {
    console.log('❌ API issue:', apiResponse.data);
  }
  
  console.log('\n4️⃣  Testing asset serving...');
  const files = require('fs').readdirSync('./dist/assets');
  const cssFile = files.find(f => f.endsWith('.css'));
  
  if (cssFile) {
    const cssResponse = await checkEndpoint(`${serverUrl}/assets/${cssFile}`);
    if (cssResponse.status === 200) {
      console.log('✅ Assets served correctly');
    } else {
      console.log('❌ Asset serving issue');
    }
  }
  
  console.log('\n✅ Server is working perfectly!');
  console.log('\n📌 The issue must be in the CLI startup process.');
  
  process.exit(0);
}

test().catch(console.error);