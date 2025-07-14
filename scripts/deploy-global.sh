#!/bin/bash

# Deploy Agent Team Composer globally for testing
# This script builds the package and makes it globally available

set -e

echo "🚀 Deploying Agent Team Composer globally..."

# Clean up existing global installation
echo "🧹 Cleaning up previous installation..."
npm uninstall -g agent-team-composer 2>/dev/null || true
rm -f /usr/local/bin/agent-team-composer 2>/dev/null || true

# Build the npm package
echo "📦 Building package..."
npm run build:npm

# Link globally with force to overwrite existing
echo "🔗 Linking globally..."
npm link --force

# Verify installation
echo "✅ Verifying installation..."
INSTALLED_VERSION=$(agent-team-composer --version)
echo "Global version: $INSTALLED_VERSION"

# Show location
BINARY_PATH=$(which agent-team-composer)
echo "Binary location: $BINARY_PATH"

echo ""
echo "🎉 Ready for testing!"
echo "You can now run 'agent-team-composer init --fresh' from any directory."