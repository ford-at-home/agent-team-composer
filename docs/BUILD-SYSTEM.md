# Build System Documentation

## Overview

This document explains the build system for the agent-team-composer NPM package and how to avoid common ESM module resolution issues.

## Build Process

The build process (`npm run build:npm`) performs the following steps:

1. **Clean**: Removes the existing `dist/` directory
2. **Frontend Build**: Builds the Vite-based frontend assets
3. **TypeScript Compilation**: Compiles TypeScript files to JavaScript
4. **Import Fix**: Adds `.js` extensions to all relative imports for ESM compatibility
5. **Validation**: Verifies all imports have proper extensions
6. **Package Creation**: Creates entry points and bin scripts
7. **Testing**: Runs a basic CLI execution test

## Common Issues and Solutions

### Issue: ERR_MODULE_NOT_FOUND

**Cause**: Node.js ESM requires explicit `.js` extensions for relative imports, but TypeScript doesn't add them during compilation.

**Solution**: The build script automatically adds `.js` extensions to all relative imports:
- `./file` → `./file.js`
- `../utils/helper` → `../utils/helper.js`
- `./components/index` → `./components/index.js`

### Issue: Path Aliases Not Resolved

**Cause**: TypeScript path aliases (like `@/*`) don't work in the distributed package.

**Solution**: Avoid using path aliases in code that will be distributed. Use relative imports instead.

## Build Configuration

### TypeScript Configuration

The project uses multiple TypeScript configurations:

- `tsconfig.json`: Base configuration with path aliases for development
- `tsconfig.cli.json`: Configuration for building the CLI and services
- `tsconfig.app.json`: Configuration for the frontend application

Key settings for ESM compatibility:
```json
{
  "compilerOptions": {
    "module": "ES2022",
    "target": "ES2022",
    "moduleResolution": "node"
  }
}
```

### Package.json Configuration

Essential fields for ESM packages:
```json
{
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "bin": {
    "agent-team-composer": "./bin/agent-team-composer.js"
  }
}
```

## Build Scripts

### `npm run build:npm`
Main build script that creates the distributable package.

### `npm run validate:build`
Validates that the build output has proper ESM imports.

### `npm run test:build`
Runs integration tests to ensure the built package works correctly.

## CI/CD Integration

The GitHub Actions workflow (`build-validation.yml`) ensures:
- Build succeeds on multiple Node.js versions
- All imports have proper extensions
- CLI can be executed
- Package can be imported as an ESM module

## Developer Guidelines

### Writing New Code

1. **Use relative imports** instead of path aliases for distributable code
2. **Don't include `.js` extensions** in TypeScript source files
3. **Run `npm run build:npm` locally** before pushing changes
4. **Test the CLI** with `npx . --help` after building

### Import Patterns

✅ **Good**:
```typescript
import { GitHubService } from './services/github-service';
import { readFile } from '../utils/file-helper';
```

❌ **Avoid**:
```typescript
import { GitHubService } from '@/services/github-service';
import { readFile } from 'src/utils/file-helper';
```

### Testing Changes

After making changes:
```bash
# Build the package
npm run build:npm

# Test the CLI
npx . --version
npx . --help

# Run build tests
npm run test:build

# Validate imports
npm run validate:build
```

## Troubleshooting

### Build Fails with Import Errors

1. Check that all relative imports in source files don't have `.js` extensions
2. Ensure TypeScript compilation succeeds: `npm run typecheck`
3. Run validation separately: `npm run validate:build`

### CLI Doesn't Execute

1. Check bin script has proper shebang: `#!/usr/bin/env node`
2. Ensure bin script has execute permissions: `chmod +x bin/agent-team-composer.js`
3. Verify the bin points to the correct file in `package.json`

### Module Import Fails

1. Ensure `"type": "module"` is in `package.json`
2. Check that all imports in dist files have `.js` extensions
3. Verify the main entry point exists: `dist/index.js`

## Future Improvements

### Consider Using a Bundler

Tools like `tsup`, `esbuild`, or `rollup` can handle these issues automatically:

```bash
# Example with tsup
tsup src/cli/index.ts --format esm --dts --clean
```

Benefits:
- Automatic import resolution
- Smaller bundle sizes
- Better tree-shaking
- No manual import fixing needed

### Migrate to Rust

As mentioned, the plan is to eventually port to Rust, which will eliminate these JavaScript module resolution issues entirely.