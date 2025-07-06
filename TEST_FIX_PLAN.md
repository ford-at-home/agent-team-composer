# Test Fix Plan

## Issues to Fix

### 1. ProjectSummary.test.tsx

- Tests using `getByRole('option')` which doesn't work with Radix UI Select
- Need to update tests to interact with Radix UI components properly

### 2. ReviewSubmit.test.tsx

- Tests looking for 'owner/repo' text that's now in a dropdown
- Need to update tests to match new UI structure

### 3. LifecyclePhases.test.tsx

- Multiple elements with same text causing ambiguity
- Need to use more specific queries

### 4. E2E Tests

- Playwright configuration issue

## Solutions

### For Radix UI Select Testing

```typescript
// Instead of:
await user.click(screen.getByRole('option', { name: 'Mobile App' }));

// Use:
const trigger = screen.getByRole('combobox');
await user.click(trigger);
// Then find the option in the portal
const option = await screen.findByText('Mobile App');
await user.click(option);
```

### For ReviewSubmit Tests

- Update to not look for repository text directly
- Test the component behavior instead of specific text

### For LifecyclePhases Tests

- Use `getAllByText` when multiple elements expected
- Add more specific queries using parent elements
