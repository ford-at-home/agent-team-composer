#!/bin/bash

# Script to rebuild and re-link the package for testing
echo "🔄 Rebuilding and linking agent-team-composer for testing..."

# Build the project
echo "📦 Building project..."
npm run build

# Build npm version
echo "📦 Building npm version..."
npm run build:npm

# Unlink existing global link
echo "🔗 Unlinking old version..."
npm unlink -g agent-team-composer 2>/dev/null || true

# Create new link
echo "🔗 Creating fresh link..."
npm link

echo "✅ Done! You can now test with 'agent-team-composer' command"
echo "📍 Version: $(node -p "require('./package.json').version")"