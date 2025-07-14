# Agent Team Composer - Preservation Strategy

## Current Working State (v1.0.7)

This document captures the current working state and provides a strategy to prevent regression.

### What's Working

1. **UI Flow**: Parse Product form displays correctly on initial load
2. **Auto-Population**: README content automatically populates form fields
3. **No Manual Trigger**: AI Populate button removed - happens automatically
4. **Build Process**: `npm run build:npm` creates proper ES module builds
5. **Testing**: Playwright E2E tests verify the complete flow

### Critical Files and Their Purpose

#### Core UI Components

- `/src/pages/Index.tsx` - Main UI orchestrator with step navigation
  - Uses `summary: null` to show ParseProduct form initially
  - Manages loading states with overlay
- `/src/components/ParseProduct.tsx` - Form component with auto-population
  - `useEffect` hook triggers AI population when README loads
  - No manual AI button - automatic behavior
- `/src/components/ProjectSummary.tsx` - Displays parsed project data
  - Shows all fields including target users, tech stack, features

#### Build Configuration

- `/package.json` - Defines both CJS and ESM builds
  - `build:cjs` for CommonJS (development)
  - `build:npm` for ES modules (npm package)
  - Peer dependencies prevent React context issues

#### Server & CLI

- `/src/cli/index.ts` - CLI entry point
  - `--fresh` flag clears cached data
  - Creates initial data with `summary: null`
  - Dynamic version from package.json
- `/src/server/index.ts` - Express server
  - Cache-busting headers prevent browser caching
  - Serves built UI files

### Version Control & Backup Strategy

1. **Tag Current Working Version**

   ```bash
   git tag -a v1.0.7-stable -m "Stable version with working UI auto-population"
   git push origin v1.0.7-stable
   ```

2. **Create Release Branch**

   ```bash
   git checkout -b release/1.0.7-stable
   git push origin release/1.0.7-stable
   ```

3. **Backup Built Artifacts**

   ```bash
   # Create backup of working build
   tar -czf agent-team-composer-1.0.7-stable.tar.gz \
     dist/ \
     bin/ \
     package.json \
     package-lock.json

   # Store in safe location
   cp agent-team-composer-1.0.7-stable.tar.gz ~/backups/
   ```

### Testing Strategy

1. **Automated Tests**
   - Run before ANY changes: `npm run test:e2e`
   - Tests verify: UI loads, auto-population works, no AI button exists
2. **Manual Verification Checklist**

   ```bash
   # Clean test
   rm -rf node_modules dist .agent-team-composer-data.json
   npm install
   npm run build:npm
   npm link --force
   agent-team-composer init --fresh --port 3000
   ```

   Then verify:
   - [ ] Parse Product form shows on load
   - [ ] "Analyzing README..." appears briefly
   - [ ] Form populates automatically
   - [ ] No AI Populate button visible
   - [ ] Can proceed to next step

3. **Integration Tests**
   Create `test-integration.sh`:

   ```bash
   #!/bin/bash
   set -e

   echo "Running integration tests..."

   # Test 1: Fresh install
   npm run build:npm
   npm link --force

   # Test 2: UI loads
   timeout 30s agent-team-composer init --fresh --port 8999 &
   PID=$!
   sleep 10

   # Test 3: Check if accessible
   curl -s http://localhost:8999 > /dev/null || exit 1

   kill $PID
   echo "✅ All integration tests passed"
   ```

### CI/CD Pipeline

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: |
          npm run lint
          npm run typecheck
          npm run build:npm
          npx playwright install
          npm run test:e2e

      - name: Integration test
        run: |
          npm link --force
          timeout 30s agent-team-composer init --fresh --port 8999 &
          sleep 15
          curl -f http://localhost:8999 || exit 1
```

### Recovery Procedures

If the UI breaks in the future:

1. **Quick Recovery**

   ```bash
   # Checkout stable version
   git checkout v1.0.7-stable
   npm install
   npm run build:npm
   npm link --force
   ```

2. **From Backup**

   ```bash
   # Extract backup
   tar -xzf ~/backups/agent-team-composer-1.0.7-stable.tar.gz
   npm link --force
   ```

3. **Debug Checklist**
   - Check browser console for errors
   - Verify `summary: null` in initial data
   - Check for React context errors
   - Clear browser cache
   - Run with `--fresh` flag

### Critical Dependencies

Lock these versions to prevent breaking changes:

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@radix-ui/react-tabs": "^1.0.4",
    "commander": "^11.1.0",
    "express": "^4.18.2"
  }
}
```

### Development Rules

1. **Never modify these without extensive testing:**
   - Initial data structure (`summary: null`)
   - Build process (`npm run build:npm`)
   - React context setup
   - Auto-population useEffect

2. **Always run before committing:**

   ```bash
   npm run lint
   npm run typecheck
   npm run build:npm
   npm run test:e2e
   ```

3. **Test on different devices:**
   - Clear browser cache
   - Test in incognito mode
   - Test on different browsers
   - Test with slow network

### Monitoring

Add logging to track issues:

```typescript
// In ParseProduct.tsx
console.log('[ParseProduct] Mounted with README length:', readmeContent?.length);
console.log('[ParseProduct] Auto-populate triggered');
console.log('[ParseProduct] AI response received:', suggestions);
```

### Contact for Issues

If critical issues arise:

1. Check this document first
2. Review test results in `test-results/` directory
3. Check GitHub issues for similar problems
4. Create detailed bug report with:
   - Browser console errors
   - Network tab screenshots
   - Steps to reproduce
   - Environment details

## Summary

This version (1.0.7) represents a stable, working implementation with:

- Automatic README parsing
- No manual intervention needed
- Robust error handling
- Comprehensive test coverage

Preserve this state through version control, backups, and strict testing discipline.
