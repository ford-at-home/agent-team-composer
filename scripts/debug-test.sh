#!/bin/bash

echo "🔍 Debug Test Script"
echo "==================="
echo ""

# 1. Check version
echo "1. CLI Version Check:"
agent-team-composer --version
echo ""

# 2. Check where it's installed
echo "2. Installation Path:"
WHICH_PATH=$(which agent-team-composer)
echo "   Command: $WHICH_PATH"
echo "   Links to: $(readlink $WHICH_PATH)"
echo "   Real path: $(readlink -f $WHICH_PATH 2>/dev/null || echo 'readlink -f not supported')"
echo ""

# 3. Check dist files
echo "3. Distribution Files:"
DIST_PATH="/Users/williamprior/Development/GitHub/agent-team-composer/dist"
echo "   Assets in dist:"
ls -la $DIST_PATH/assets/ | grep index
echo ""

# 4. Check for README in build
echo "4. Build Content Check:"
if grep -q "README Content" $DIST_PATH/assets/index-*.js 2>/dev/null; then
  echo "   ❌ ERROR: README preview STILL in build!"
else
  echo "   ✅ README preview removed from build"
fi
echo ""

# 5. Check actual file being served
echo "5. Actual Served File:"
LINKED_DIR=$(cd /usr/local/lib/node_modules/agent-team-composer && pwd)
echo "   Linked directory: $LINKED_DIR"
echo "   Assets in linked dir:"
ls -la $LINKED_DIR/dist/assets/ | grep index
echo ""

# 6. Compare files
echo "6. File Comparison:"
ORIG_FILE=$(ls $DIST_PATH/assets/index-*.js | head -1)
LINKED_FILE=$(ls $LINKED_DIR/dist/assets/index-*.js | head -1)
if [ -f "$ORIG_FILE" ] && [ -f "$LINKED_FILE" ]; then
  if diff -q "$ORIG_FILE" "$LINKED_FILE" >/dev/null; then
    echo "   ✅ Files are identical"
  else
    echo "   ❌ ERROR: Files are DIFFERENT!"
  fi
else
  echo "   ❌ ERROR: Could not compare files"
fi
echo ""

echo "7. Browser Cache:"
echo "   To force refresh in browser:"
echo "   - Chrome/Edge: Cmd+Shift+R"
echo "   - Safari: Cmd+Option+R"
echo "   - Or open in Incognito/Private window"
echo ""

echo "8. Test Command:"
echo "   Kill all existing processes first:"
echo "   lsof -ti:3000-3010 | xargs kill -9"
echo ""
echo "   Then run with fresh data:"
echo "   agent-team-composer init --fresh --port 4567"