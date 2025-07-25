#!/bin/bash
# Run automated browser tests for UI components

set -e

echo "🧪 Running E2E tests..."

# Check if tests exist
if [ -f "tests/test_cli_modular.py" ]; then
    echo "📋 Found modular CLI tests"
    
    # Run pytest if available
    if command -v pytest &> /dev/null; then
        pytest tests/test_cli_modular.py -v
    elif command -v python3 &> /dev/null && python3 -m pytest --version &> /dev/null; then
        python3 -m pytest tests/test_cli_modular.py -v
    else
        echo "⚠️  pytest not available, skipping automated tests"
        echo "   Install with: pip install pytest"
    fi
else
    echo "❌ No E2E tests found"
    exit 1
fi

echo "✅ Testing complete!"