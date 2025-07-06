# Agent Team Composer - GitHub Issues Specification

## Overview
The Agent Team Composer is a CLI tool that transforms product vision documents into GitHub issues optimized for SPARC agent execution. This specification details 10 issues grouped into 3 epics for completing the missing features.

---

## Epic 1: Complete 5-Step UI Flow

### Issue 1: Implement Step 1: Parse Product with Editable Metadata

**Title:** Implement Parse Product Step with LLM Integration and Editable UI

**Description:**
Add the first step of the 5-step flow that parses a product vision document using an LLM and presents editable metadata.

**Deliverables:**
- New component `ParseProduct.tsx` that accepts markdown/text input
- LLM API integration to extract project metadata
- Editable fields for title, description, tech stack, complexity
- Auto-save functionality on field changes
- Validation for required fields

**Technical Approach:**
1. Create `/src/components/ParseProduct.tsx` component
2. Add LLM service in `/src/services/llm.ts` for document parsing
3. Update types to include parsed metadata structure
4. Integrate with existing `useProjectData` hook
5. Use existing UI components (Card, Input, Textarea, Select)

**SPARC Agent Instructions:**
```
@researcher: Research best practices for LLM prompt engineering for document parsing
@coder: Implement ParseProduct component and LLM service in parallel
@integration-engineer: Connect LLM responses to UI state management
```

**Dependencies:** None
**Estimated Effort:** 4-6 hours

---

### Issue 2: Implement Step 4: Per-Epic Issue View with Editing

**Title:** Add Epic-Level Issue Management UI with Inline Editing

**Description:**
Create Step 4 that displays generated issues grouped by epic with full editing capabilities.

**Deliverables:**
- `EpicIssueView.tsx` component with collapsible epic sections
- Inline editing for issue titles and descriptions
- Drag-and-drop to reorder issues within epics
- Add/remove issues functionality
- Role assignment dropdown for each issue
- Issue count and status indicators per epic

**Technical Approach:**
1. Create `/src/components/EpicIssueView.tsx`
2. Use `@dnd-kit/sortable` for drag-and-drop
3. Implement controlled inputs with debounced updates
4. Add issue CRUD operations to `useProjectData`
5. Use Accordion component for epic collapsing

**SPARC Agent Instructions:**
```
@full-stack-engineer: Build the EpicIssueView component with drag-and-drop
@coder: Implement issue CRUD operations and state management
-- Sequential after UI complete --
@tech-lead: Review component architecture and state flow
```

**Dependencies:** Issue 1 (for data structure)
**Estimated Effort:** 6-8 hours

---

### Issue 3: Add GitHub Repo/Branch Selector to Step 5

**Title:** Implement GitHub Repository and Branch Selection UI

**Description:**
Enhance Step 5 (Review & Submit) with GitHub repository and branch selection before issue creation.

**Deliverables:**
- Repository search/selection with autocomplete
- Branch dropdown populated from selected repo
- Validation that repo exists and user has write access
- Option to create new branch
- Persist selections in project data

**Technical Approach:**
1. Add GitHub API integration to fetch user repos and branches
2. Create `RepoSelector.tsx` and `BranchSelector.tsx` components
3. Use Combobox pattern for searchable repo selection
4. Add GitHub validation to submission flow
5. Update `ReviewSubmit.tsx` to include selectors

**SPARC Agent Instructions:**
```
@integration-engineer: Implement GitHub API client for repos/branches
@full-stack-engineer: Build selector components with search
-- Parallel execution, then merge --
@coder: Integrate selectors into ReviewSubmit flow
```

**Dependencies:** None
**Estimated Effort:** 4-5 hours

---

### Issue 4: Enable Editing for All UI Components

**Title:** Add Comprehensive Edit Mode Across All Steps

**Description:**
Ensure all data fields across all steps are editable with consistent UX patterns.

**Deliverables:**
- Edit/Preview toggle for all text fields
- Inline editing for lists and arrays
- Undo/redo functionality
- Dirty state indicators
- Confirmation before navigation with unsaved changes

**Technical Approach:**
1. Create `useEditMode` hook for consistent edit state
2. Add `EditableField` wrapper component
3. Implement undo/redo with state history
4. Add navigation guards to router
5. Update all step components to use editable patterns

**SPARC Agent Instructions:**
```
@coder: Create useEditMode hook and EditableField component
@full-stack-engineer: Update all step components with edit capability
-- Work in parallel on different components --
@tech-lead: Ensure consistent UX patterns across components
```

**Dependencies:** Issues 1, 2, 3
**Estimated Effort:** 3-4 hours

---

## Epic 2: GitHub Integration & SPARC Optimization

### Issue 5: Create GitHub Milestones for Sprints

**Title:** Implement Automated Sprint Milestone Creation

**Description:**
Automatically create GitHub milestones for each sprint/phase with proper dates and descriptions.

**Deliverables:**
- Milestone creation API integration
- Sprint date calculation based on complexity
- Milestone description templates
- Issue assignment to milestones
- Progress tracking setup

**Technical Approach:**
1. Extend GitHub service with milestone endpoints
2. Add sprint planning logic to calculate dates
3. Create milestone templates with phase metadata
4. Update issue creation to include milestone assignment
5. Add milestone ID tracking to project data

**SPARC Agent Instructions:**
```
@integration-engineer: Implement GitHub milestone API client
@coder: Build sprint planning and date calculation logic
-- Sequential execution required --
@full-stack-engineer: Update UI to show milestone associations
```

**Dependencies:** Issue 3 (repo selection)
**Estimated Effort:** 4-5 hours

---

### Issue 6: Implement Epic → Issue Hierarchy with Projects v2

**Title:** Setup GitHub Projects v2 Board with Epic Tracking

**Description:**
Create GitHub Project board with proper epic-to-issue relationships and custom fields.

**Deliverables:**
- Projects v2 board creation
- Custom fields for epic tracking
- Epic parent-child relationships
- Automated board population
- Status field configuration

**Technical Approach:**
1. Use GitHub GraphQL API for Projects v2
2. Create project board with epic swim lanes
3. Add custom fields: Epic, Sprint, Agent Role
4. Link issues to epics via custom field
5. Configure automation rules

**SPARC Agent Instructions:**
```
@integration-engineer: Implement Projects v2 GraphQL mutations
@coder: Build epic relationship management
-- Work can happen in parallel --
@tech-lead: Design optimal board structure for SPARC workflow
```

**Dependencies:** Issue 5
**Estimated Effort:** 6-8 hours

---

### Issue 7: Add SPARC-Specific Labels and Metadata

**Title:** Create SPARC Agent Labels and Execution Metadata

**Description:**
Add GitHub labels and issue metadata optimized for SPARC agent execution.

**Deliverables:**
- SPARC role labels (researcher, coder, tester, etc.)
- Execution order labels (parallel, sequential, blocking)
- Complexity labels (simple, medium, complex)
- Agent instruction blocks in issue descriptions
- Dependency metadata fields

**Technical Approach:**
1. Define SPARC label taxonomy
2. Create labels via GitHub API
3. Add SPARC instruction formatter
4. Update issue templates with metadata sections
5. Include execution hints in issue body

**SPARC Agent Instructions:**
```
@researcher: Define optimal SPARC label taxonomy
@coder: Implement label creation and assignment
@integration-engineer: Format issues with SPARC metadata
-- All agents work in parallel --
```

**Dependencies:** None
**Estimated Effort:** 3-4 hours

---

### Issue 8: Add Execution Planner LLM Call for Issue Formatting

**Title:** Implement AI-Powered SPARC Execution Planning

**Description:**
Add LLM step that optimizes issue descriptions and dependencies for SPARC agent execution.

**Deliverables:**
- Execution Planner LLM prompt engineering
- Dependency graph analysis
- Parallel execution opportunity detection
- SPARC instruction generation
- Batch optimization for related tasks

**Technical Approach:**
1. Create `ExecutionPlanner` service
2. Design prompts for SPARC optimization
3. Analyze issue dependencies for parallelization
4. Generate SPARC-specific instructions
5. Add planning step to workflow

**SPARC Agent Instructions:**
```
@researcher: Research SPARC execution patterns and best practices
@coder: Implement ExecutionPlanner service and prompts
@integration-engineer: Integrate planner into issue creation flow
-- Researcher first, then parallel execution --
```

**Dependencies:** Issue 7
**Estimated Effort:** 5-6 hours

---

## Epic 3: Production Readiness & Publishing

### Issue 9: Prepare and Publish NPM Package

**Title:** Package Agent Team Composer as NPM CLI Tool

**Description:**
Convert the web application into a published NPM package with CLI interface.

**Deliverables:**
- CLI entry point with command parsing
- NPM package configuration
- Build and bundle optimization
- README with installation/usage
- Publish to NPM registry

**Technical Approach:**
1. Create `cli.js` entry point using Commander.js
2. Configure package.json for CLI distribution
3. Setup Rollup/esbuild for optimal bundling
4. Write comprehensive README
5. Implement `npx` support

**SPARC Agent Instructions:**
```
@coder: Create CLI wrapper and command structure
@full-stack-engineer: Optimize build and bundle configuration
@tech-lead: Review package structure and dependencies
-- Sequential execution for testing --
```

**Dependencies:** All previous issues
**Estimated Effort:** 4-5 hours

---

### Issue 10: Implement GitHub CLI Verification and Setup

**Title:** Add GitHub CLI Authentication and Setup Flow

**Description:**
Ensure proper GitHub CLI (`gh`) setup and authentication before allowing issue creation.

**Deliverables:**
- GitHub CLI detection
- Authentication status check
- Setup wizard for missing auth
- Permission verification
- Helpful error messages with fix instructions

**Technical Approach:**
1. Check for `gh` CLI installation
2. Verify `gh auth status`
3. Guide user through `gh auth login` if needed
4. Test API access with user permissions
5. Cache auth status for session

**SPARC Agent Instructions:**
```
@integration-engineer: Implement gh CLI detection and auth check
@full-stack-engineer: Build setup wizard UI
@coder: Add permission verification logic
-- All work in parallel, integrate at end --
```

**Dependencies:** Issue 3
**Estimated Effort:** 3-4 hours

---

## Execution Summary

### Phase 1 (Sprint 1): Core UI Completion
- Issues 1, 2, 3, 4
- Total effort: 17-23 hours
- Parallel execution possible for Issues 1 & 3

### Phase 2 (Sprint 2): GitHub & SPARC Integration  
- Issues 5, 6, 7, 8
- Total effort: 18-23 hours
- Issues 5 & 7 can run in parallel

### Phase 3 (Sprint 3): Production Release
- Issues 9, 10
- Total effort: 7-9 hours
- Sequential execution required

### Total Project Effort: 42-55 hours

### Critical Path:
1 → 2 → 4 → 5 → 6 → 8 → 9

### Parallel Opportunities:
- Issues 1 & 3 (no dependencies)
- Issues 5 & 7 (different GitHub APIs)
- Issue 10 (can start early)

### SPARC Optimization Notes:
- Use `@researcher` for all exploratory work
- `@coder` and `@full-stack-engineer` can work in parallel on independent components
- `@integration-engineer` handles all external API work
- `@tech-lead` reviews critical architectural decisions
- Batch related file operations for efficiency
- Use TodoWrite for complex multi-step workflows