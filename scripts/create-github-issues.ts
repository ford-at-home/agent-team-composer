#!/usr/bin/env node
import { GitHubService } from '../src/services/github-service';
import dotenv from 'dotenv';

dotenv.config();

const REPOSITORY = 'ford-at-home/project-delivery-navigator';

const issues = [
  // Epic 1: Complete 5-Step UI Flow
  {
    title: '[Epic 1] Complete 5-Step UI Flow',
    body: `## Epic Overview
This epic completes the 5-step UI flow as specified in the original requirements.

### Issues in this Epic:
- [ ] #2 Parse Product with editable metadata
- [ ] #3 Per-Epic Issue View with editing  
- [ ] #4 GitHub repo/branch selector
- [ ] #5 Enable editing for all UI components

### Goal
Provide a complete, editable UI experience for transforming README files into GitHub issues.`,
    labels: ['epic', 'ui', 'priority:high']
  },
  {
    title: 'Implement Step 1: Parse Product with editable metadata',
    body: `## Overview
Implement the missing Step 1 that displays parsed README content and allows users to edit project metadata before proceeding.

## Deliverables
- [ ] New component: src/components/ParseProduct.tsx
- [ ] Display parsed README with syntax highlighting
- [ ] Editable fields for: title, description, domain, target users, tech stack
- [ ] Auto-detection with manual override capability
- [ ] Integration with existing stepper flow

## Technical Approach
1. Create ParseProduct component with form controls
2. Use react-hook-form for form management
3. Add markdown preview with react-markdown
4. Update stepper to include new step
5. Pass edited metadata through to LLM calls

## SPARC Agent Instructions
**Sequential Execution Required**
- Frontend Developer: Build UI component first
- Full-Stack Engineer: Integrate with existing flow
- Integration Engineer: Update LLM calls to use edited metadata

**Parallel Opportunities**
- UI styling and form validation can happen in parallel
- README parsing improvements can be worked separately

## Dependencies
None - this is the entry point

## Estimated Effort
6 hours (4h development, 2h integration/testing)`,
    labels: ['enhancement', 'ui', 'phase:development', 'role:frontend', 'sparc-enabled:true', 'sprint:1']
  },
  {
    title: 'Implement Step 4: Per-Epic Issue View with editing',
    body: `## Overview
Create Step 4 that shows all issues grouped by epic with full editing capabilities before GitHub submission.

## Deliverables
- [ ] New component: src/components/EpicIssueView.tsx
- [ ] Drag-and-drop issue reordering within epics
- [ ] Edit issue title, description, assigned role
- [ ] Add/delete issues
- [ ] Bulk operations (select multiple issues)
- [ ] Preview of final GitHub issue format

## Technical Approach
1. Use react-beautiful-dnd for drag-and-drop
2. Implement CollapsibleEpic component for grouping
3. Create IssueEditor with markdown preview
4. Add state management for issue modifications
5. Implement undo/redo functionality

## SPARC Agent Instructions
**Sequential Execution Required**
- UI Designer: Create mockups first
- Frontend Developer: Implement components
- Full-Stack Engineer: Wire up state management

**Parallel Opportunities**
- Drag-and-drop can be developed separately from editing
- Markdown preview can be built independently
- Bulk operations can be added after base functionality

## Dependencies
- Requires Issue #1 (Parse Product) to be complete

## Estimated Effort
8 hours (5h development, 2h drag-drop, 1h testing)`,
    labels: ['enhancement', 'ui', 'phase:development', 'role:frontend', 'sparc-enabled:true', 'sprint:1']
  },
  {
    title: 'Add GitHub repo/branch selector to Step 5',
    body: `## Overview
Add repository and branch selection to the final review step before pushing to GitHub.

## Deliverables
- [ ] Repository dropdown with user's accessible repos
- [ ] Branch selector with create new branch option
- [ ] Validation of write permissions
- [ ] Preview of target location
- [ ] Error handling for permission issues

## Technical Approach
1. Add GitHub API call to list user repositories
2. Create RepoSelector component with search
3. Implement branch listing and creation
4. Add permission checking before enable submit
5. Show clear error messages for access issues

## SPARC Agent Instructions
**Sequential Execution Required**
- Integration Engineer: Implement GitHub API calls first
- Frontend Developer: Build UI components
- Full-Stack Engineer: Wire up to submission flow

**Parallel Opportunities**
- Repository listing and branch listing can be built in parallel
- UI components can be styled while API is being built

## Dependencies
- Requires GitHub authentication to be working

## Estimated Effort
4 hours (2h API integration, 2h UI)`,
    labels: ['enhancement', 'ui', 'github', 'phase:development', 'role:fullstack', 'sparc-enabled:true', 'sprint:1']
  },
  {
    title: 'Enable editing for all UI components',
    body: `## Overview
Make all UI components editable instead of read-only, allowing users to modify generated content before submission.

## Deliverables
- [ ] Editable ProjectSummary component
- [ ] Editable LifecyclePhases with add/remove phases
- [ ] Editable phase descriptions and roles
- [ ] Consistent edit/view mode toggle
- [ ] Form validation across all components
- [ ] Auto-save to localStorage

## Technical Approach
1. Add edit mode state to each component
2. Create inline editing components
3. Implement form validation with Zod
4. Add localStorage persistence
5. Create consistent edit UI patterns

## SPARC Agent Instructions
**Parallel Execution Possible**
- Frontend Dev 1: Update ProjectSummary component
- Frontend Dev 2: Update LifecyclePhases component
- Frontend Dev 3: Update ReviewSubmit component
- Full-Stack Engineer: Implement auto-save system

**Sequential Requirements**
- Design consistent edit patterns first
- Test all components together at the end

## Dependencies
- Can start immediately, works with existing components

## Estimated Effort
6 hours (2h per major component)`,
    labels: ['enhancement', 'ui', 'phase:development', 'role:frontend', 'sparc-enabled:true', 'sprint:1']
  },
  // Epic 2: GitHub Integration & SPARC Optimization
  {
    title: '[Epic 2] GitHub Integration & SPARC Optimization',
    body: `## Epic Overview
Complete GitHub integration with proper milestone/epic hierarchy and SPARC agent optimization.

### Issues in this Epic:
- [ ] #7 Create GitHub Milestones for Sprints
- [ ] #8 Implement Epic → Issue hierarchy
- [ ] #9 Add SPARC-specific labels
- [ ] #10 Add Execution Planner LLM call

### Goal
Full GitHub integration with SPARC-optimized issue formatting.`,
    labels: ['epic', 'github', 'integration', 'priority:high']
  },
  {
    title: 'Create GitHub Milestones for Sprints',
    body: `## Overview
Automatically create GitHub Milestones for each Sprint/Phase in the project plan.

## Deliverables
- [ ] Milestone creation in GitHubService
- [ ] Sprint number and dates in milestone
- [ ] Progress tracking setup
- [ ] Link issues to appropriate milestones
- [ ] Handle existing milestone conflicts

## Technical Approach
1. Extend GitHubService with milestone methods
2. Create milestones before creating issues
3. Auto-generate due dates based on estimates
4. Add milestone parameter to issue creation
5. Handle duplicate milestone names

## SPARC Agent Instructions
**Sequential Execution Required**
- Integration Engineer: Implement GitHub API calls
- Backend Developer: Update issue creation flow
- QA Engineer: Test milestone edge cases

**Parallel Opportunities**
- Milestone UI preview can be built separately
- Date calculation logic can be developed independently

## Dependencies
- Requires GitHub authentication

## Estimated Effort
4 hours (3h implementation, 1h testing)`,
    labels: ['enhancement', 'github', 'phase:development', 'role:backend', 'sparc-enabled:true', 'sprint:2']
  },
  {
    title: 'Implement Epic → Issue hierarchy with Projects v2',
    body: `## Overview
Create proper epic-to-issue relationships using GitHub Projects v2 or issue references.

## Deliverables
- [ ] Epic issues with task lists referencing sub-issues
- [ ] Automatic linking of issues to epics
- [ ] Progress tracking on epics
- [ ] Optional: GitHub Projects v2 integration
- [ ] Fallback: Use labels and references if Projects unavailable

## Technical Approach
1. Create epics as issues with 'epic' label
2. Add task lists in epic body with issue references
3. Implement parent-child linking via mentions
4. Optional: Use Projects v2 GraphQL API
5. Update UI to show hierarchy

## SPARC Agent Instructions
**Sequential Execution Required**
- Research Engineer: Investigate Projects v2 API
- Integration Engineer: Implement chosen approach
- Frontend Developer: Update UI to show relationships

**Parallel Opportunities**
- Epic creation and issue creation can be parallelized
- UI updates can happen while API work continues

## Dependencies
- Requires Issue #5 (Milestones) to be complete

## Estimated Effort
6 hours (4h implementation, 2h Projects v2 research)`,
    labels: ['enhancement', 'github', 'phase:development', 'role:backend', 'sparc-enabled:true', 'sprint:2']
  },
  {
    title: 'Add SPARC-specific labels and metadata',
    body: `## Overview
Add all required SPARC agent labels and metadata to enable autonomous execution.

## Deliverables
- [ ] Add sparc-enabled:true label to all issues
- [ ] Add sprint:<n> labels
- [ ] Add role:<persona> labels with normalized names
- [ ] Add execution metadata in issue body
- [ ] Create SPARC manifest reference

## Technical Approach
1. Define SPARC label schema
2. Normalize role names for consistency
3. Add metadata section to issue template
4. Include execution hints in markdown
5. Validate all required labels present

## SPARC Agent Instructions
**Parallel Execution Possible**
- Backend Dev 1: Implement label creation
- Backend Dev 2: Update issue templates
- Integration Engineer: Add manifest generation

**Sequential Requirements**
- Define label schema first
- Test with SPARC agents at end

## Dependencies
- Can start immediately

## Estimated Effort
3 hours (2h implementation, 1h testing)`,
    labels: ['enhancement', 'github', 'sparc', 'phase:development', 'role:backend', 'sparc-enabled:true', 'sprint:2']
  },
  {
    title: 'Add Execution Planner LLM call for issue formatting',
    body: `## Overview
Implement the 4th LLM call that optimizes each issue for SPARC agent execution.

## Deliverables
- [ ] New LLM prompt for execution planning
- [ ] Structured issue body with sections:
  - Context: What this contributes
  - Steps: Detailed breakdown by role
  - Output: Clear definition of done
  - Agent Instructions: SPARC-specific guidance
- [ ] Dependency mapping between issues
- [ ] Time estimates per issue

## Technical Approach
1. Create execution-planner.ts prompt
2. Add to LLM orchestrator pipeline
3. Format issues with clear sections
4. Include dependency DAG in metadata
5. Add to issue body template

## SPARC Agent Instructions
**Sequential Execution Required**
- AI Engineer: Design and test prompt
- Integration Engineer: Add to LLM pipeline
- Backend Developer: Update issue formatting

**Parallel Opportunities**
- Prompt engineering can happen while other LLM calls work
- Template formatting can be developed separately

## Dependencies
- Requires base LLM orchestrator to be working

## Estimated Effort
5 hours (3h prompt engineering, 2h integration)`,
    labels: ['enhancement', 'ai', 'sparc', 'phase:development', 'role:ai-engineer', 'sparc-enabled:true', 'sprint:2']
  },
  // Epic 3: Production Readiness
  {
    title: '[Epic 3] Production Readiness & Publishing',
    body: `## Epic Overview
Prepare the tool for NPM publishing and production use.

### Issues in this Epic:
- [ ] #11 Prepare and publish NPM package
- [ ] #12 Implement GitHub CLI verification

### Goal
Make the tool installable via NPM and production-ready.`,
    labels: ['epic', 'devops', 'priority:medium']
  },
  {
    title: 'Prepare and publish NPM package',
    body: `## Overview
Convert the project into a publishable NPM package that can be installed globally.

## Deliverables
- [ ] Proper package.json configuration
- [ ] CLI entry point with shebang
- [ ] Bundled distribution files
- [ ] README with installation instructions
- [ ] Published to NPM registry
- [ ] npx support working

## Technical Approach
1. Configure package.json for CLI tool
2. Set up proper entry points
3. Bundle with esbuild or similar
4. Test global installation
5. Publish to NPM with proper scope

## SPARC Agent Instructions
**Sequential Execution Required**
- DevOps Engineer: Set up build pipeline
- Full-Stack Engineer: Fix any bundling issues
- Tech Lead: Handle NPM publication

**Parallel Opportunities**
- Documentation can be written while bundling
- Testing can happen on different platforms

## Dependencies
- All core features should be complete

## Estimated Effort
4 hours (2h setup, 1h testing, 1h publishing)`,
    labels: ['enhancement', 'devops', 'phase:deployment', 'role:devops', 'sparc-enabled:true', 'sprint:3']
  },
  {
    title: 'Implement GitHub CLI verification and setup',
    body: `## Overview
Add proper GitHub CLI detection and setup flow instead of using execSync.

## Deliverables
- [ ] Detect if gh is installed
- [ ] Prompt to install if missing
- [ ] Guide through gh auth login
- [ ] Verify authentication status
- [ ] Fall back to GITHUB_TOKEN if available
- [ ] Clear error messages

## Technical Approach
1. Use which or command -v to detect gh
2. Provide platform-specific install instructions
3. Check gh auth status safely
4. Implement token fallback
5. Add to environment validation

## SPARC Agent Instructions
**Sequential Execution Required**
- Backend Developer: Implement detection logic
- Full-Stack Engineer: Add setup UI flow
- QA Engineer: Test on all platforms

**Parallel Opportunities**
- Platform-specific instructions can be written in parallel
- UI and CLI detection can be built separately

## Dependencies
- None, but fixes security issue

## Estimated Effort
3 hours (2h implementation, 1h platform testing)`,
    labels: ['enhancement', 'security', 'phase:development', 'role:backend', 'sparc-enabled:true', 'sprint:3']
  }
];

async function createIssues() {
  console.log('Creating GitHub issues for Agent Team Composer...\n');
  
  const githubService = new GitHubService(process.env.GITHUB_TOKEN);
  
  // Check authentication
  const auth = await githubService.checkAuthentication();
  if (!auth.authenticated) {
    console.error('❌ Not authenticated with GitHub. Set GITHUB_TOKEN environment variable.');
    process.exit(1);
  }
  
  console.log(`✅ Authenticated as ${auth.user}\n`);
  
  // Create issues sequentially to avoid rate limits
  for (const issue of issues) {
    try {
      console.log(`Creating: ${issue.title}`);
      
      const result = await githubService['octokit'].issues.create({
        owner: 'ford-at-home',
        repo: 'project-delivery-navigator',
        title: issue.title,
        body: issue.body,
        labels: issue.labels
      });
      
      console.log(`✅ Created issue #${result.data.number}\n`);
      
      // Small delay to avoid rate limits
      await new Promise(resolve => setTimeout(resolve, 1000));
      
    } catch (error) {
      console.error(`❌ Failed to create issue: ${issue.title}`);
      console.error(error.message);
    }
  }
  
  console.log('✨ Done creating issues!');
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  createIssues().catch(console.error);
}