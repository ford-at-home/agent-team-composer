# Development Workflow

## Quick Commands

After making any changes to the code, run:

```bash
npm run build:npm && npm link --force
```

This will:
1. Build the project with proper ES module extensions
2. Re-link the package globally
3. Make changes immediately available for testing

## Verify Changes

To verify your changes are in the build:

```bash
./scripts/verify-changes.sh
```

## Test in Another Workspace

In your test project directory:

```bash
agent-team-composer --version  # Should show 1.0.10
agent-team-composer init       # Test the UI
```

## What We Changed in v1.0.10

1. **Removed README preview panel** - The right column showing README content is gone
2. **Added loading state** - Shows "Generating Project Plan" overlay when processing
3. **Display all form fields** - ProjectSummary now shows:
   - Target Users
   - Tech Stack  
   - Key Features
   - Complexity indicator
4. **Dynamic version** - CLI now reads version from package.json

## Troubleshooting

If changes aren't showing:

1. Make sure you ran `npm run build:npm` (not just `npm run build`)
2. Force re-link: `npm unlink -g agent-team-composer && npm link --force`
3. Check the build: `./scripts/verify-changes.sh`
4. In your test workspace, check version: `agent-team-composer --version`