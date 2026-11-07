#!/bin/bash
# Verify that changes are in the built files

set -e

echo "🔍 Verifying deployment..."

# Check version
VERSION=$(python3 -c "import toml; print(toml.load('pyproject.toml')['project']['version'])" 2>/dev/null || echo "1.0.0")
echo "📌 Package version: $VERSION"

# Check if commands are available
if command -v github-backlog-generator &> /dev/null; then
    echo "✅ Global command 'github-backlog-generator' is available"
    # Try to get version (may not be implemented)
    INSTALLED_VERSION=$(github-backlog-generator --version 2>&1 || echo "Version command not implemented")
    echo "   Installed version output: $INSTALLED_VERSION"
else
    echo "❌ Global command 'github-backlog-generator' not found"
    exit 1
fi

if command -v github-backlog &> /dev/null; then
    echo "✅ Global command 'github-backlog' is available"
else
    echo "❌ Global command 'github-backlog' not found"
fi

# Check if unified CLI module exists
if [ -f "src/github_backlog_generator/cli_unified.py" ]; then
    echo "✅ Unified CLI module exists"
    # Check for key features
    if grep -q "class BacklogManager" src/github_backlog_generator/cli_unified.py; then
        echo "✅ BacklogManager class found"
    else
        echo "❌ BacklogManager class not found"
    fi
    if grep -q "def init(" src/github_backlog_generator/cli_unified.py && grep -q "def milestones(" src/github_backlog_generator/cli_unified.py; then
        echo "✅ Unified commands (init, milestones) found"
    else
        echo "❌ Unified commands not found"
    fi
    if grep -q "\-\-cost" src/github_backlog_generator/cli_unified.py && grep -q "\-\-time" src/github_backlog_generator/cli_unified.py; then
        echo "✅ Cost and timing tracking options found"
    else
        echo "❌ Cost and timing tracking options not found"
    fi
else
    echo "❌ Unified CLI module not found"
    exit 1
fi

echo "✨ Verification complete!"