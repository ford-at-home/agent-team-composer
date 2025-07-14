#!/bin/bash

echo "🔧 Fixing agent-team-composer distribution..."

# 1. Use the EXISTING npm build script that already works
echo "📦 Building with npm build script..."
npm run build:npm

# 2. Test it locally
echo "🧪 Testing local installation..."
cd /tmp
rm -rf test-atc
mkdir test-atc
cd test-atc

# Create test project
echo "# Test Project" > README.md
git init

# Link to the built package
npm link agent-team-composer

# Test the command
echo "🚀 Testing init command..."
agent-team-composer init --skip-gh-check &
PID=$!

sleep 5

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ SUCCESS! Server is running!"
    kill $PID
else
    echo "❌ FAILED! Server not responding"
    kill $PID 2>/dev/null
fi

# Cleanup
cd /
rm -rf /tmp/test-atc

echo "✅ Done!"