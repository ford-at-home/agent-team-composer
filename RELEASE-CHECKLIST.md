# Release Checklist for agent-team-composer

## Before Every Release:

1. **Build with the npm script**

   ```bash
   npm run build:npm
   ```

2. **Test locally**

   ```bash
   # In a test directory
   mkdir test-release && cd test-release
   echo "# Test" > README.md
   npm init -y
   npm install ../path/to/agent-team-composer
   npx agent-team-composer init --skip-gh-check
   ```

3. **Verify:**
   - ✅ No LLM calls during init
   - ✅ UI loads immediately
   - ✅ No "TabsContent" errors
   - ✅ Server starts successfully

4. **Update version**

   ```bash
   npm version patch
   ```

5. **Publish**
   ```bash
   npm publish
   ```

## Why this works:

- The `build:npm` script fixes ALL import issues
- It's already tested and proven
- Creates a proper distribution package

## What NOT to do:

- Don't use `npm run build` for publishing
- Don't test only in development mode
- Don't skip the local install test
