# CLAUDE.md

## CRITICAL: Development & Testing Workflow

**I (Claude) MUST ALWAYS RUN THESE COMMANDS AFTER MAKING ANY CODE CHANGES:**

### After Making ANY Code Changes

1. **I MUST Build and Deploy Changes:**
   ```bash
   ./scripts/deploy-global.sh
   ```
   
   OR manually:
   ```bash
   npm run build:npm && npm link --force
   ```
   
   **IMPORTANT:** I MUST use `npm run build:npm` (not `npm run build`) because it:
   - Adds `.js` extensions to ES module imports
   - Fixes module resolution issues
   - Creates a properly packaged version

2. **I MUST Verify Changes Are in Build:**
   ```bash
   ./scripts/verify-changes.sh
   ```
   
   This script checks:
   - Package version is correct
   - Specific changes are present in the built files
   - Global link is properly configured

3. **THEN the User Can Test in Their Separate Workspace:**
   ```bash
   agent-team-composer --version  # Should show current version
   agent-team-composer init       # Test the actual UI
   ```

### Common Issues & Solutions

- **"Module not found" errors**: Run `npm run build:npm` (not just `npm run build`)
- **Changes not showing**: Force re-link with `npm unlink -g agent-team-composer && npm link --force`
- **Version showing wrong**: The version is now read from package.json dynamically

### Build Commands Reference

- `npm run build` - Standard build (DO NOT USE for testing)
- `npm run build:npm` - Proper build with ES module fixes (USE THIS)
- `npm run build:cli` - Only builds CLI
- `npm run dev:auto` - Auto-rebuild on file changes (experimental)

### Testing Checklist - I (Claude) MUST DO THIS

Before telling the user any change is complete, I MUST:
- [ ] Update any affected E2E tests to match the changes
- [ ] Run `./scripts/deploy-global.sh` (builds and links automatically)
- [ ] Run `./scripts/verify-changes.sh` and confirm all checks pass
- [ ] Run `./scripts/test-ui.sh` to run automated browser tests
- [ ] Verify tests pass or fix any failures
- [ ] Tell the user what version to expect
- [ ] NEVER end with "Now test with..." or "Here's what to run..."
- [ ] ALWAYS end with "I've run [commands] and you can now test"

**I MUST RUN THESE COMMANDS MYSELF. The user should NOT have to build or link anything.**
**I MUST UPDATE AND RUN TESTS for every UI change.**

### Proper Ending Format

❌ WRONG: "Now test with: `agent-team-composer init`"
✅ RIGHT: "I've run `./scripts/deploy-global.sh` and verified the changes. You can now test in your workspace."

---

## Prime Directive for Claude Flow SPARC

You are operating within a Claude Flow SPARC project environment. Your role is to autonomously plan, execute, and report on tasks derived from a human-provided product spec, typically found in the README.md file of this repository.

### Workflow Instructions

1. Parse the README.md to understand the intended product or feature.
2. Generate a full product plan by breaking the work down into:
   - Sprints (phases of delivery, created as GitHub Milestones)
   - Epics (major workstreams, created as labeled GitHub Issues)
   - Issues (atomic tasks, assigned to roles and nested under epics)
3. For each task:
   - Identify the team roles or personas involved
   - Define clear steps, deliverables, and role sequencing
   - Use team-based swarming to collaborate across personas
4. Push all Sprints, Epics, and Issues to the GitHub repository using structured metadata:
   - Assign each issue to a milestone (sprint)
   - Label with role, phase, and sprint
   - Mark with sparc-enabled:true if Claude agents should swarm it
5. Execute the assigned issues:
   - Follow the defined steps in the issue body
   - Collaborate with other agents where necessary
   - Update issue status through comments or edits
   - Close each issue when the deliverable is complete

### Version Control Requirements

**CRITICAL: All work must follow strict version control practices:**

1. **Before starting any issue:**
   - Pull fresh main branch: `git pull origin main`
   - Create a new feature branch: `git checkout -b issue-<issue-number>-<brief-description>`
   - Example: `git checkout -b issue-42-add-user-authentication`

2. **During development:**
   - Make atomic commits with clear messages
   - Commit frequently to track progress
   - Use conventional commit format: `type(scope): description`
   - Examples: `feat(auth): add JWT token validation`, `fix(api): resolve null pointer exception`

3. **After completing the issue:**
   - Push the feature branch: `git push origin issue-<issue-number>-<brief-description>`
   - Create a Pull Request with:
     - Clear title referencing the issue number
     - Description of changes made
     - Link to the related issue
     - Any testing performed
   - Mark the PR as ready for review

4. **Branch naming conventions:**
   - Feature branches: `issue-<number>-<description>`
   - Bug fixes: `fix-<number>-<description>`
   - Hotfixes: `hotfix-<number>-<description>`

5. **PR Description Template:**
   ```
   ## Related Issue
   Closes #<issue-number>
   
   ## Changes Made
   - Brief description of changes
   - Key implementation decisions
   
   ## Testing
   - How the changes were tested
   - Any edge cases considered
   
   ## Notes
   - Any additional context for reviewers
   ```

**IMPORTANT:** Never commit directly to main. All changes must go through PR review process. A human will review and approve PRs before merging.

### Output Requirements

- All planning should be materialized as GitHub artifacts
- GitHub is the source of truth for the backlog
- All issues must be well-structured and understandable by both humans and Claude agents
- Prioritize clarity, modularity, and reusability

### Notes

- Do not overwrite or delete human-authored content unless explicitly allowed
- Use swarming only when appropriate and role boundaries are clear
- Always complete the loop: generate, execute, close
