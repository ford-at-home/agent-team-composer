# Auto-Release Workflow Documentation

## Overview

The auto-release workflow automatically publishes new versions of the `agent-team-composer` package to npm when pull requests are merged to the main branch. This document explains how it works and how to troubleshoot common issues.

## How It Works

### 1. Trigger Conditions

- **When**: A pull request is merged to the `main` branch
- **Skip**: If the PR has a `skip-release` label

### 2. Version Determination

The workflow determines the version bump type based on PR labels:

- **Major version** (`1.0.0` → `2.0.0`): Labels `breaking-change` or `major`
- **Minor version** (`1.0.0` → `1.1.0`): Labels `feature` or `minor`
- **Patch version** (`1.0.0` → `1.0.1`): Default for all other PRs (bug fixes, docs, etc.)

### 3. Release Process

1. **Tests**: Runs TypeScript checks and unit tests
2. **Build**: Creates the npm package
3. **Version**: Increments version in package.json
4. **Changelog**: Updates CHANGELOG.md with PR details
5. **Git**: Commits changes and creates a git tag
6. **Publish**: Publishes to npm registry
7. **GitHub Release**: Creates a GitHub release
8. **PR Comment**: Adds a comment with the release info

## Testing the Workflow

### Local Testing

Run the test script to validate your environment:

```bash
./scripts/test-release-workflow.sh
```

This script checks:

- Required npm scripts exist
- Build process works
- Version management is configured
- Git operations are possible
- npm authentication (if configured)

### Workflow Validation

The `validate-workflows.yml` workflow automatically validates all GitHub Actions workflows on:

- Pull requests that modify workflows
- Pushes to main/develop branches
- Manual trigger via GitHub UI

### Unit Tests

Run the workflow logic tests:

```bash
npm test src/test/workflow-utils.test.ts
```

## Common Issues and Solutions

### 1. "Cannot push to protected branch"

**Problem**: The workflow fails when trying to push to main.
**Solution**: Ensure the GitHub Actions bot has permission to push to main. Go to Settings → Branches → Edit protection rules → Allow GitHub Actions to bypass.

### 2. "npm ERR! 401 Unauthorized"

**Problem**: npm publish fails with authentication error.
**Solution**:

1. Ensure `NPM_TOKEN` is set in repository secrets
2. Generate a new token at https://www.npmjs.com/settings/YOUR_USERNAME/tokens
3. Add it to GitHub: Settings → Secrets → Actions → New repository secret

### 3. "Tests failed but continuing with release"

**Problem**: Unit tests are failing but release continues.
**Solution**: This is temporary behavior. Fix the failing tests to ensure quality:

```bash
npm test
```

### 4. "Tag already exists"

**Problem**: Git tag for the version already exists.
**Solution**:

1. Check existing tags: `git tag -l`
2. If needed, delete the tag: `git tag -d vX.Y.Z && git push origin :vX.Y.Z`
3. Or manually increment version: `npm version patch`

### 5. "PREVIOUS_VERSION is undefined"

**Problem**: The workflow references an undefined variable.
**Solution**: This has been fixed in the latest workflow version. The workflow now captures the previous version before incrementing.

## Manual Release Process

If the auto-release fails, you can release manually:

```bash
# 1. Ensure you're on main branch with latest changes
git checkout main
git pull origin main

# 2. Run tests
npm test
npm run build:npm

# 3. Increment version
npm version patch  # or minor/major

# 4. Push changes and tag
git push origin main
git push origin --tags

# 5. Publish to npm
npm publish

# 6. Create GitHub release manually via UI
```

## Best Practices

1. **Always label PRs appropriately** to ensure correct version bumps
2. **Fix failing tests** before merging PRs
3. **Use `skip-release` label** for PRs that shouldn't trigger a release (e.g., CI changes, documentation)
4. **Test locally** with the provided script before major changes
5. **Monitor releases** by watching the Actions tab after PR merges

## Environment Variables

The workflow uses these secrets (configured in repository settings):

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- `NPM_TOKEN`: Must be manually configured for npm publishing

## Debugging

To debug workflow issues:

1. Check the Actions tab in GitHub for detailed logs
2. Run the local test script: `./scripts/test-release-workflow.sh`
3. Validate workflow syntax: Manually trigger the validate-workflows action
4. Test version bumping locally: `npm version patch --dry-run`

## Workflow File Locations

- Main workflow: `.github/workflows/auto-release.yml`
- Validation workflow: `.github/workflows/validate-workflows.yml`
- Test script: `scripts/test-release-workflow.sh`
- Unit tests: `src/test/workflow-utils.test.ts`
