#!/bin/bash

echo "🔍 Verifying changes in build..."
echo ""

# Check version
VERSION=$(node -p "require('./package.json').version")
echo "📦 Package version: $VERSION"

# Check if README preview was removed
if grep -q "README Content" dist/assets/index-*.js 2>/dev/null; then
  echo "❌ README preview still exists in build"
else
  echo "✅ README preview successfully removed"
fi

# Check if loading state was added
if grep -q "Generating Project Plan" dist/assets/index-*.js 2>/dev/null; then
  echo "✅ Loading state added"
else
  echo "❌ Loading state not found"
fi

# Check if all form fields are included
if grep -q "targetUsers" dist/assets/index-*.js 2>/dev/null; then
  echo "✅ Target users field included"
else
  echo "❌ Target users field missing"
fi

if grep -q "techStack" dist/assets/index-*.js 2>/dev/null; then
  echo "✅ Tech stack field included"
else
  echo "❌ Tech stack field missing"
fi

echo ""
echo "📍 Global link points to: $(readlink $(which agent-team-composer))"
echo "📍 Version from CLI: $(agent-team-composer --version 2>/dev/null || echo 'Failed to run')"