# GitHub Actions Workflows

This project uses GitHub Actions for continuous integration and automated releases.

## Workflows

### 0. Auto Release on PR Merge (`.github/workflows/auto-release.yml`)

**Triggers**: When PR is merged to main

**What it does**:
- Detects version type from PR labels
- Runs tests and build validation
- Increments version automatically
- Publishes to NPM
- Creates GitHub release
- Updates CHANGELOG
- Comments on PR with release info

**PR Labels**:
- `major` or `breaking-change` → Major version bump
- `feature` or `minor` → Minor version bump
- Default (no label) → Patch version bump
- `skip-release` → Skip the release

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers**: Push to main/develop, Pull requests

**What it does**:
- Runs on Node.js 16, 18, and 20
- Linting (non-blocking)
- Type checking
- Unit tests
- Build validation
- Integration tests
- CLI execution tests
- Checks for uncommitted changes

### 2. Build Validation (`.github/workflows/build-validation.yml`)

**Triggers**: Push to main/develop, Pull requests

**What it does**:
- Validates build output
- Tests ESM imports
- Ensures CLI works
- Multi-node version testing

### 3. Release PR Creation (`.github/workflows/release-pr.yml`)

**Triggers**: Manual (workflow_dispatch)

**What it does**:
- Creates a release branch
- Bumps version (patch/minor/major)
- Updates CHANGELOG template
- Creates PR for review
- Runs all tests

**How to use**:
1. Go to Actions tab
2. Select "Create Release PR"
3. Choose version type
4. Run workflow
5. Review and merge PR
6. Tag and publish after merge

### 4. NPM Publishing (`.github/workflows/publish.yml`)

**Triggers**: 
- Manual (workflow_dispatch)
- Git tags (v*)

**What it does**:
- Increments version (if manual)
- Builds and validates
- Publishes to NPM
- Creates GitHub release
- Supports dry-run mode

**How to use**:
1. Go to Actions tab
2. Select "Publish to NPM"
3. Choose version type
4. Optional: Enable dry-run
5. Run workflow

## Setup Requirements

### NPM Token

1. Create token at https://www.npmjs.com/
2. Add to GitHub Secrets:
   - Go to Settings → Secrets → Actions
   - Create new secret: `NPM_TOKEN`
   - Paste your NPM access token

### Permissions

Ensure Actions have write permissions:
- Settings → Actions → General
- Workflow permissions: Read and write

## Version Strategy

- **Patch** (0.0.X): Bug fixes, docs, dependencies
- **Minor** (0.X.0): New features, non-breaking changes
- **Major** (X.0.0): Breaking changes

## Workflow Features

### Automatic Version Management
- Version bumps handled by workflows
- Git tags created automatically
- Changelog templates generated

### Quality Gates
- All tests must pass
- Build validation required
- Type checking enforced
- No uncommitted changes allowed

### Multi-Platform Testing
- Tests on Node.js 16, 18, and 20
- Ubuntu latest environment
- Caching for faster builds

### Safety Features
- Dry-run mode for testing
- Manual approval via PR process
- Rollback via git tags

## Troubleshooting

### Workflow Fails

1. Check Actions tab for logs
2. Verify secrets are set correctly
3. Ensure branch protections allow pushes
4. Check Node version compatibility

### NPM Publish Fails

1. Verify NPM_TOKEN is valid
2. Check package name availability
3. Ensure version doesn't exist
4. Review npm audit results

### PR Creation Fails

1. Check branch naming conflicts
2. Verify git permissions
3. Ensure base branch exists
4. Check for existing PRs