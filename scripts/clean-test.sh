#!/bin/bash

echo "🧹 Cleaning up for fresh test..."

# Kill any running instances
echo "🔪 Killing existing processes..."
lsof -ti:3000-3010 | xargs kill -9 2>/dev/null || true

# Remove cached data file in current directory
echo "🗑️  Removing cached data..."
rm -f .agent-team-composer-data.json

# Clear any browser cache by using a different port
PORT=${1:-3456}
echo "🚀 Starting fresh on port $PORT..."

# Run with explicit port to avoid conflicts
agent-team-composer init --port $PORT --fresh

echo ""
echo "📝 Notes:"
echo "1. If you still see old UI, force refresh browser (Cmd+Shift+R)"
echo "2. Check browser dev tools Network tab - are assets from cache?"
echo "3. Try incognito/private window to avoid browser cache"