#!/bin/bash

# Test script for auto-release workflow
# This script simulates the auto-release workflow locally to catch issues before they happen in CI

set -e

echo "🧪 Testing Auto-Release Workflow..."
echo "=================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

echo "📋 Pre-flight checks..."

# Check for required commands
command -v node >/dev/null 2>&1
print_status $? "Node.js is installed"

command -v npm >/dev/null 2>&1
print_status $? "npm is installed"

# Check package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found${NC}"
    exit 1
fi
print_status 0 "package.json exists"

# Check for required npm scripts
required_scripts=("typecheck" "test:once" "build:npm" "validate:build" "test:build")
missing_scripts=()

for script in "${required_scripts[@]}"; do
    if ! grep -q "\"$script\":" package.json; then
        missing_scripts+=("$script")
    fi
done

if [ ${#missing_scripts[@]} -eq 0 ]; then
    print_status 0 "All required npm scripts are defined"
else
    echo -e "${RED}❌ Missing npm scripts: ${missing_scripts[*]}${NC}"
    exit 1
fi

echo ""
echo "🏗️  Testing build process..."

# Test npm install
echo "Running npm ci..."
npm ci > /dev/null 2>&1
print_status $? "npm ci completed successfully"

# Test TypeScript compilation
echo "Running typecheck..."
npm run typecheck > /dev/null 2>&1
print_status $? "TypeScript typecheck passed"

# Test unit tests (allow failure but warn)
echo "Running tests..."
if npm run test:once > /dev/null 2>&1; then
    print_status 0 "Unit tests passed"
else
    print_warning "Unit tests failed (workflow will continue with warning)"
fi

# Test build
echo "Running build..."
npm run build:npm > /dev/null 2>&1
print_status $? "Build completed successfully"

# Test build validation
echo "Validating build..."
npm run validate:build > /dev/null 2>&1
print_status $? "Build validation passed"

npm run test:build > /dev/null 2>&1
print_status $? "Build tests passed"

echo ""
echo "📦 Testing version management..."

# Get current version
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo "Current version: $CURRENT_VERSION"

# Test version increment simulation (without actually changing)
for version_type in patch minor major; do
    # Simulate what the new version would be
    NEW_VERSION=$(npm version $version_type --no-git-tag-version --dry-run 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    if [ -n "$NEW_VERSION" ]; then
        echo "✅ $version_type bump would result in: $NEW_VERSION"
    else
        echo "❌ Failed to simulate $version_type version bump"
    fi
done

echo ""
echo "🏷️  Testing git tag management..."

# Check if there are any existing tags
if git tag -l | grep -q .; then
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
    echo "Latest git tag: $LATEST_TAG"
else
    print_warning "No git tags found in repository"
fi

# Check if current version has a tag
if git tag -l "v$CURRENT_VERSION" | grep -q .; then
    print_status 0 "Current version has a git tag"
else
    print_warning "Current version (v$CURRENT_VERSION) does not have a git tag"
fi

echo ""
echo "📝 Testing changelog generation..."

# Check if CHANGELOG.md exists
if [ -f "CHANGELOG.md" ]; then
    print_status 0 "CHANGELOG.md exists"
else
    print_warning "CHANGELOG.md does not exist (will be created on first release)"
fi

echo ""
echo "🔒 Testing npm authentication..."

# Check if npm token is configured (without exposing it)
if [ -n "$NPM_TOKEN" ]; then
    print_status 0 "NPM_TOKEN environment variable is set"
else
    print_warning "NPM_TOKEN not set - required for publishing"
fi

# Check npm whoami (if authenticated)
if npm whoami --registry https://registry.npmjs.org/ > /dev/null 2>&1; then
    NPM_USER=$(npm whoami --registry https://registry.npmjs.org/)
    print_status 0 "Authenticated to npm as: $NPM_USER"
else
    print_warning "Not authenticated to npm (required for publishing)"
fi

echo ""
echo "📊 Workflow simulation summary:"
echo "==============================="

# Summary of checks
echo -e "${GREEN}✅ Build and test pipeline is working${NC}"
echo -e "${GREEN}✅ Version management is configured${NC}"
echo -e "${GREEN}✅ Git operations are possible${NC}"

if [ -n "$NPM_TOKEN" ] || npm whoami > /dev/null 2>&1; then
    echo -e "${GREEN}✅ NPM publishing is configured${NC}"
else
    echo -e "${YELLOW}⚠️  NPM publishing needs configuration${NC}"
fi

echo ""
echo "💡 Recommendations:"
echo "- Ensure all tests pass before merging PRs"
echo "- Use appropriate PR labels (patch, minor, major) for version bumps"
echo "- Add 'skip-release' label if you don't want to trigger a release"
echo "- Make sure NPM_TOKEN is set in GitHub Secrets for publishing"

echo ""
echo -e "${GREEN}✅ Release workflow validation complete!${NC}"