# Release Process

This document describes the release process for agent-team-composer.

## Automatic Releases on PR Merge

By default, every PR merged to main will trigger an automatic release. The version type is determined by PR labels:

- **`major`** or **`breaking-change`** → Major version (1.0.0)
- **`feature`** or **`minor`** → Minor version (0.1.0)  
- Any other PR → Patch version (0.0.1)
- **`skip-release`** → No release

### How it works

1. Create a PR with your changes
2. Add appropriate labels:
   - `feature` for new features
   - `breaking-change` for breaking changes
   - `skip-release` to skip automatic release
3. Merge the PR
4. GitHub Actions will automatically:
   - Increment version
   - Build and test
   - Publish to NPM
   - Create GitHub release
   - Update CHANGELOG

## Manual Release Process

### Option 1: Create Release PR (Recommended)

1. Go to Actions → "Create Release PR"
2. Choose version type: patch, minor, or major
3. Click "Run workflow"

This will:
- Create a new branch with version bump
- Update CHANGELOG.md template
- Create a PR for review
- Run all tests

After PR is merged:
- Create and push tag: `git tag v1.2.3 && git push origin v1.2.3`
- The publish workflow will automatically trigger

### Option 2: Direct Publish

1. Go to Actions → "Publish to NPM"
2. Choose version type: patch, minor, or major
3. Optional: Check "Dry run" to test without publishing
4. Click "Run workflow"

This will:
- Increment version
- Build and test
- Publish to NPM
- Create GitHub release
- Push version tag

## Manual Release Process

If you need to release manually:

```bash
# 1. Ensure you're on main branch with latest changes
git checkout main
git pull origin main

# 2. Run tests
npm run typecheck
npm run test:once
npm run build:npm
npm run test:build

# 3. Update version
npm version patch  # or minor, major

# 4. Update CHANGELOG.md
# Add your changes under a new version heading

# 5. Commit changes
git add CHANGELOG.md
git commit -m "chore: update changelog for v$(node -p "require('./package.json').version")"

# 6. Push changes and tag
git push origin main
git push origin v$(node -p "require('./package.json').version")

# 7. Publish to NPM
npm publish

# 8. Create GitHub release
# Go to GitHub releases page and create release from the new tag
```

## Version Guidelines

### Patch Release (x.x.X)
- Bug fixes
- Performance improvements
- Documentation updates
- Dependency updates (non-breaking)

### Minor Release (x.X.0)
- New features (backward compatible)
- New commands or options
- Significant improvements
- Dependency updates (potentially breaking)

### Major Release (X.0.0)
- Breaking changes
- Major refactoring
- API changes
- Removal of features

## Pre-release Checklist

- [ ] All tests pass locally
- [ ] Build succeeds without warnings
- [ ] CLI works correctly (`npx . --help`)
- [ ] No uncommitted changes
- [ ] CHANGELOG.md is updated
- [ ] Version number makes sense

## Post-release Checklist

- [ ] Package is live on NPM
- [ ] GitHub release is created
- [ ] Installation works: `npm install -g agent-team-composer@latest`
- [ ] CLI works: `agent-team-composer --version`
- [ ] Announce release (if major/minor)

## Troubleshooting

### NPM Publish Fails

1. Check NPM authentication:
   ```bash
   npm whoami
   ```

2. Ensure you have publish permissions:
   ```bash
   npm owner ls agent-team-composer
   ```

3. Try manual publish with debug:
   ```bash
   npm publish --verbose
   ```

### GitHub Actions Fails

1. Check NPM_TOKEN secret is set in repository settings
2. Ensure GITHUB_TOKEN has appropriate permissions
3. Check workflow logs for specific errors

### Version Already Exists

If you get "version already exists" error:
1. Check NPM: `npm view agent-team-composer versions`
2. Bump to next version: `npm version patch`
3. Try publishing again

## Security Notes

- Never commit NPM tokens to repository
- Use GitHub secrets for sensitive data
- Review dependencies before releasing
- Run `npm audit` before each release