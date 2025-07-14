#!/bin/bash

echo "🧪 Running Agent Team Composer UI Tests"
echo "======================================"
echo ""

# Kill any existing processes
echo "🔪 Killing existing processes..."
lsof -ti:8000-9000 | xargs kill -9 2>/dev/null || true

# Clean up test data
echo "🧹 Cleaning test data..."
rm -f .agent-team-composer-data.json
rm -rf test-results
mkdir -p test-results

# Run the diagnostic test first
echo ""
echo "📊 Running diagnostic test..."
npx playwright test e2e/diagnose-issue.spec.ts --config playwright-cli.config.ts --reporter=list

# Run the full UI test
echo ""
echo "🎯 Running full UI flow test..."
npx playwright test e2e/full-ui-test.spec.ts --config playwright-cli.config.ts --reporter=list

echo ""
echo "📸 Screenshots saved in test-results/"
echo "🎥 Videos and traces available in test-results/"
echo ""
echo "To view HTML report: npx playwright show-report"
echo "To view a trace: npx playwright show-trace test-results/[test-name]/trace.zip"