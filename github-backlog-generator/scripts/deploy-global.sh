#!/bin/bash
# Deploy script for global testing

set -e

echo "🚀 Building and deploying github-backlog-generator..."

# Check if pipx is available
if command -v pipx &> /dev/null; then
    echo "📦 Installing package with pipx..."
    # First uninstall if it exists
    pipx uninstall github-backlog-generator 2>/dev/null || true
    # Install from current directory
    pipx install . --force
else
    echo "📦 Installing package with pip (using --break-system-packages)..."
    pip install -e . --break-system-packages
fi

echo "✅ Deployment complete!"
echo "   Version: $(python3 -c "import toml; print(toml.load('pyproject.toml')['project']['version'])" 2>/dev/null || echo "1.0.0")"