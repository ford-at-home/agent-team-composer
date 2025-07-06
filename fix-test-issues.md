# Test Issues Fix Plan

## Issues Identified

1. **ProjectSummary.test.tsx** - Select component issues:
   - Tests are looking for HTML `role="option"` elements, but the Radix UI Select component doesn't render standard HTML select/option elements
   - Need to update tests to work with Radix UI's Select component

2. **ReviewSubmit.test.tsx** - branches.map error:
   - The `branches` state might not be an array in some cases
   - Need to add defensive coding to ensure branches is always an array

3. **LifecyclePhases.test.tsx** - Multiple element issues:
   - Tests finding multiple elements with same text
   - Need to use more specific queries

4. **e2e/project-flow.spec.ts** - Playwright configuration issue:
   - test.describe() being called in wrong context

## Solutions

### 1. Fix ReviewSubmit Component - Add defensive coding for branches

```typescript
// In ReviewSubmit.tsx, update line 105:
setBranches(Array.isArray(data) ? data : []);

// Also update the branches.map on line 287:
{Array.isArray(branches) && branches.map(branch => (
```

### 2. Update ProjectSummary Tests to work with Radix UI

```typescript
// Instead of looking for role="option", we need to:
// 1. Click the select trigger to open it
// 2. Look for elements by text content within the dropdown
```

### 3. Fix LifecyclePhases Tests

```typescript
// Use more specific queries like:
// - getAllByText when expecting multiple elements
// - Add data-testid attributes for better targeting
```

### 4. Fix Playwright E2E Test

```typescript
// Ensure test.describe is not being called in a configuration context
```
