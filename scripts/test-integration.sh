#!/bin/bash
set -e

echo "Running integration tests..."

# Test 1: Fresh install
echo "Building package..."
npm run build:npm
npm link --force

# Test 2: UI loads
echo "Starting server..."
timeout 30s agent-team-composer init --fresh --port 8999 &
PID=$!
sleep 10

# Test 3: Check if accessible
echo "Checking if server is accessible..."
if curl -s http://localhost:8999 > /dev/null; then
    echo "✅ Server is accessible"
else
    echo "❌ Server is not accessible"
    kill $PID 2>/dev/null || true
    exit 1
fi

# Test 4: Check for expected content
echo "Checking for Parse Product form..."
if curl -s http://localhost:8999 | grep -q "Parse Product"; then
    echo "✅ Parse Product form found"
else
    echo "❌ Parse Product form not found"
    kill $PID 2>/dev/null || true
    exit 1
fi

kill $PID 2>/dev/null || true
echo "✅ All integration tests passed"