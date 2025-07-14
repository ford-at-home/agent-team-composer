#!/bin/bash

echo "🧪 Testing distribution package..."

# Clean up
rm -rf test-distribution
mkdir -p test-distribution
cd test-distribution

# Create a test project
echo "# Test Project" > README.md
echo "A simple test project" >> README.md

# Pack the parent directory
echo "📦 Creating package..."
npm pack ../

# Install the package
echo "📥 Installing package..."
npm init -y > /dev/null 2>&1
npm install agent-team-composer-*.tgz

# Test the command
echo "🚀 Testing init command..."
npx agent-team-composer init --skip-gh-check &
INIT_PID=$!

# Wait a bit and check if server started
sleep 5

# Check if process is still running
if ps -p $INIT_PID > /dev/null; then
   echo "✅ Init command is running!"
   
   # Check if server is responding
   if curl -s http://localhost:3000 > /dev/null || curl -s http://localhost:3001 > /dev/null || curl -s http://localhost:3002 > /dev/null; then
      echo "✅ Server is responding!"
   else
      echo "❌ Server not responding"
   fi
   
   # Kill the process
   kill $INIT_PID
else
   echo "❌ Init command failed to start"
fi

# Cleanup
cd ..
rm -rf test-distribution

echo "🧪 Test complete!"