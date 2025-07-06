# Contributing to Agent Team Composer

## Development Setup

1. Clone the repository
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`

## Build System

This project uses an ESM (ECMAScript Modules) build system. Please read [docs/BUILD-SYSTEM.md](docs/BUILD-SYSTEM.md) for detailed information about:
- How the build process works
- Common issues and solutions
- Best practices for imports

## Quick Start

### Before You Commit

Always run these commands before committing:

```bash
# Type checking
npm run typecheck

# Build the package
npm run build:npm

# Test the CLI works
npx . --help

# Run tests
npm run test:once
```

## Code Style

### Imports

**Do:**
- Use relative imports for internal modules: `import { foo } from './foo'`
- Omit `.js` extensions in TypeScript source files
- Use destructuring when importing multiple exports

**Don't:**
- Use path aliases (`@/*`) in distributable code
- Add `.js` extensions in TypeScript files
- Use absolute imports for internal modules

### TypeScript

- Enable strict mode for new files
- Add proper types, avoid `any`
- Use interfaces for object shapes
- Document public APIs with JSDoc

## Testing

### Unit Tests
```bash
npm run test        # Watch mode
npm run test:once   # Single run
```

### Build Integration Tests
```bash
npm run test:build  # Test the built package
```

### Manual Testing
After making changes to the CLI:
```bash
npm run build:npm
npx . init --dry-run
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Run `npm run typecheck` and fix any errors
4. Run `npm run build:npm` to ensure it builds
5. Add tests for new functionality
6. Update documentation if needed
7. Submit a pull request

## Common Issues

### "Cannot find module" Errors

This usually means the build script didn't properly add `.js` extensions. Check:
1. Your imports use relative paths (not aliases)
2. The build script regex patterns match your import style
3. Run `npm run validate:build` to check imports

### Build Failures

1. Clear the dist directory: `rm -rf dist`
2. Check TypeScript errors: `npm run typecheck`
3. Ensure all dependencies are installed: `npm install`
4. Try building step by step:
   ```bash
   npm run build:dev
   npx tsc -p tsconfig.cli.json
   ```

## Project Structure

```
agent-team-composer/
├── src/
│   ├── cli/          # CLI entry point
│   ├── services/     # Core services
│   ├── prompts/      # LLM prompts
│   ├── types/        # TypeScript types
│   └── components/   # React components
├── scripts/
│   ├── build-npm.js  # Build script
│   └── validate-build.js
├── dist/             # Build output (git-ignored)
└── bin/              # CLI executable
```

## Release Process

1. Update version in `package.json`
2. Run full test suite: `npm run test:once && npm run test:build`
3. Build the package: `npm run build:npm`
4. Test the package locally: `npm link && agent-team-composer --version`
5. Create a git tag: `git tag v1.0.0`
6. Publish to NPM: `npm publish`

## Future Plans

The project will eventually be ported to Rust. Until then, we need to maintain the JavaScript/TypeScript build system carefully to avoid module resolution issues.