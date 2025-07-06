import { test, expect } from '@playwright/test';
import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';

test.describe('Project Delivery Navigator E2E', () => {
  let tempDataPath: string;

  test.beforeAll(async () => {
    // Create a temporary project data file
    const tempDir = os.tmpdir();
    tempDataPath = path.join(tempDir, 'test-project-data.json');
    
    const mockProjectData = {
      summary: {
        title: 'E2E Test Project',
        description: 'A test project for E2E testing',
        domain: 'Web Application',
        repository: 'test/repo',
        branch: 'main'
      },
      phases: [
        {
          id: 'discovery',
          title: 'Discovery & Research',
          description: 'Initial research phase',
          roles: ['Product Owner', 'UX Researcher'],
          issues: [
            {
              title: 'Market Research',
              description: 'Analyze market opportunities',
              role: 'Product Owner'
            },
            {
              title: 'User Interviews',
              description: 'Conduct user research',
              role: 'UX Researcher'
            }
          ],
          approved: false
        },
        {
          id: 'design',
          title: 'Design Phase',
          description: 'Create UI/UX designs',
          roles: ['Designer'],
          issues: [
            {
              title: 'Create Wireframes',
              description: 'Design initial wireframes',
              role: 'Designer'
            }
          ],
          approved: false
        }
      ]
    };

    await fs.writeFile(tempDataPath, JSON.stringify(mockProjectData));
  });

  test.afterAll(async () => {
    // Clean up
    await fs.unlink(tempDataPath).catch(() => {});
  });

  test('should display project summary', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the project data to load
    await page.waitForSelector('text=E2E Test Project', { timeout: 10000 });
    
    // Check summary information
    await expect(page.locator('h2').filter({ hasText: 'E2E Test Project' })).toBeVisible();
    await expect(page.locator('text=A test project for E2E testing')).toBeVisible();
    await expect(page.locator('text=test/repo')).toBeVisible();
    await expect(page.locator('text=main')).toBeVisible();
    
    // Check stats
    await expect(page.locator('text=8')).toBeVisible(); // Lifecycle phases
    await expect(page.locator('text=9')).toBeVisible(); // Agent roles
    await expect(page.locator('text=~32')).toBeVisible(); // Expected issues
  });

  test('should allow editing project description', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Click edit button
    await page.click('button:has-text("Edit")');
    
    // Edit description
    const textarea = page.locator('textarea');
    await textarea.clear();
    await textarea.fill('Updated E2E test description');
    
    // Click preview
    await page.click('button:has-text("Preview")');
    
    // Verify update
    await expect(page.locator('text=Updated E2E test description')).toBeVisible();
  });

  test('should navigate through workflow steps', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Step 1: Project Summary
    await expect(page.locator('text=Configure Phases')).toBeVisible();
    await page.click('button:has-text("Configure Phases")');
    
    // Step 2: Lifecycle Phases
    await expect(page.locator('text=Configure Lifecycle Phases')).toBeVisible();
    await expect(page.locator('text=0/2')).toBeVisible(); // 0 of 2 phases approved
    
    // Expand first phase
    await page.click('text=Discovery & Research');
    await expect(page.locator('text=Market Research')).toBeVisible();
    await expect(page.locator('text=User Interviews')).toBeVisible();
    
    // Approve first phase
    await page.click('button:has-text("Approve")').first();
    await expect(page.locator('text=1/2')).toBeVisible();
    
    // Navigate to review
    await page.click('button:has-text("Review & Submit")');
    
    // Step 3: Review & Submit
    await expect(page.locator('text=Review & Submit')).toBeVisible();
    await expect(page.locator('text=Approved Phases')).toBeVisible();
    await expect(page.locator('text=1 phase(s) not approved')).toBeVisible();
  });

  test('should manage phase roles', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Navigate to phases
    await page.click('button:has-text("Configure Phases")');
    
    // Expand first phase
    await page.click('text=Discovery & Research');
    
    // Check existing roles
    const productOwnerCheckbox = page.locator('input[type="checkbox"]').filter({ hasText: 'Product Owner' }).first();
    await expect(productOwnerCheckbox).toBeChecked();
    
    // Add a new role
    const engineerCheckbox = page.locator('label:has-text("Software Engineer")').first().locator('input[type="checkbox"]');
    await engineerCheckbox.click();
    await expect(engineerCheckbox).toBeChecked();
    
    // Verify role count updated
    await expect(page.locator('text=3 roles').first()).toBeVisible();
  });

  test('should handle phase approval workflow', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Navigate to phases
    await page.click('button:has-text("Configure Phases")');
    
    // Approve both phases
    const approveButtons = page.locator('button:has-text("Approve")');
    const count = await approveButtons.count();
    
    for (let i = 0; i < count; i++) {
      await approveButtons.nth(i).click();
    }
    
    // Verify all approved
    await expect(page.locator('text=2/2')).toBeVisible();
    
    // Continue button should be enabled
    const continueButton = page.locator('button:has-text("Review & Submit")');
    await expect(continueButton).toBeEnabled();
    
    // Navigate to review
    await continueButton.click();
    
    // No warning about unapproved phases
    await expect(page.locator('text=phase(s) not approved')).not.toBeVisible();
  });

  test('should display correct statistics in review', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Navigate through to review with approved phases
    await page.click('button:has-text("Configure Phases")');
    
    // Approve first phase
    await page.click('button:has-text("Approve")').first();
    
    await page.click('button:has-text("Review & Submit")');
    
    // Check statistics
    await expect(page.locator('text=Approved Phases').locator('..').locator('text=1')).toBeVisible();
    await expect(page.locator('text=Total Issues').locator('..').locator('text=2')).toBeVisible();
    await expect(page.locator('text=Active Roles').locator('..').locator('text=2')).toBeVisible();
  });

  test('should handle domain selection', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Open domain dropdown
    await page.click('[role="combobox"]');
    
    // Select a different domain
    await page.click('text=Mobile App');
    
    // Verify selection
    await expect(page.locator('[role="combobox"]')).toContainText('Mobile App');
  });

  test('should show loading state', async ({ page }) => {
    // Slow down the network to see loading states
    await page.route('**/api/project', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });
    
    await page.goto('/');
    
    // Should show loading indicator
    await expect(page.locator('text=Loading project data...')).toBeVisible();
    
    // Eventually loads
    await expect(page.locator('text=E2E Test Project')).toBeVisible({ timeout: 15000 });
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/project', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Server error' })
      });
    });
    
    await page.goto('/');
    
    // Should show error message
    await expect(page.locator('text=Failed to load project data')).toBeVisible();
  });

  test('should be responsive', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Elements should still be visible and functional
    await expect(page.locator('text=E2E Test Project')).toBeVisible();
    await page.click('button:has-text("Configure Phases")');
    await expect(page.locator('text=Configure Lifecycle Phases')).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('text=Configure Lifecycle Phases')).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('text=Configure Lifecycle Phases')).toBeVisible();
  });

  test('should persist changes across navigation', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Edit description
    await page.click('button:has-text("Edit")');
    const textarea = page.locator('textarea');
    await textarea.clear();
    await textarea.fill('Persisted description');
    await page.click('button:has-text("Preview")');
    
    // Navigate forward
    await page.click('button:has-text("Configure Phases")');
    
    // Navigate back
    await page.click('button:has-text("Back to Summary")');
    
    // Description should be persisted
    await expect(page.locator('text=Persisted description')).toBeVisible();
  });

  test('should show GitHub push button only when phases approved', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Navigate to review without approving
    await page.click('button:has-text("Configure Phases")');
    
    // Try to continue without approving (should be disabled)
    const continueButton = page.locator('button:has-text("Review & Submit")');
    await expect(continueButton).toBeDisabled();
    
    // Approve one phase
    await page.click('button:has-text("Approve")').first();
    await expect(continueButton).toBeEnabled();
    
    await continueButton.click();
    
    // Push button should be enabled with at least one approved phase
    const pushButton = page.locator('button:has-text("Push to GitHub")');
    await expect(pushButton).toBeEnabled();
  });
});

test.describe('Accessibility', () => {
  test('should have no accessibility violations on summary page', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Basic accessibility checks
    // Check for proper heading hierarchy
    const h1 = await page.locator('h1').count();
    const h2 = await page.locator('h2').count();
    expect(h1).toBeGreaterThanOrEqual(0);
    expect(h2).toBeGreaterThan(0);
    
    // Check for alt text on images/icons
    const images = page.locator('img');
    const imageCount = await images.count();
    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
    }
    
    // Check for button labels
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      expect(text || ariaLabel).toBeTruthy();
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=E2E Test Project');
    
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
    
    // Continue tabbing and check focus is visible
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      await expect(page.locator(':focus')).toBeVisible();
    }
    
    // Test Enter key on button
    await page.focus('button:has-text("Configure Phases")');
    await page.keyboard.press('Enter');
    await expect(page.locator('text=Configure Lifecycle Phases')).toBeVisible();
  });
});