import { test, expect } from '@playwright/test';

test.describe('Initialization Error Test', () => {
  test.beforeEach(async ({ page }) => {
    // Listen for console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Store errors on the page object
    (page as any).consoleErrors = errors;
  });

  test('should not have initialization errors on repository selection page', async ({ page }) => {
    await page.goto('http://localhost:8080');
    await page.waitForTimeout(2000);
    
    const errors = (page as any).consoleErrors;
    const initErrors = errors.filter(e => e.includes('Cannot access') && e.includes('before initialization'));
    
    expect(initErrors).toHaveLength(0);
  });

  test('should not have initialization errors when navigating to second page', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Wait for repository list to load
    await page.waitForSelector('[data-testid="repository-card"], .repository-card', { 
      timeout: 10000 
    }).catch(() => {
      // Fallback selectors
      return page.waitForSelector('text=/ford-at-home|agent-team-composer/', { timeout: 10000 });
    });
    
    // Click on first repository
    const repoCard = await page.locator('[data-testid="repository-card"], .repository-card, div:has-text("ford-at-home")').first();
    await repoCard.click();
    
    // Click continue button
    await page.click('button:has-text("Continue")');
    
    // Wait for navigation to complete
    await page.waitForTimeout(3000);
    
    // Check for initialization errors
    const errors = (page as any).consoleErrors;
    const initErrors = errors.filter(e => e.includes('Cannot access') && e.includes('before initialization'));
    
    expect(initErrors).toHaveLength(0);
  });

  test('should not have initialization errors on any workflow step', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Repository selection
    await page.waitForSelector('[data-testid="repository-card"], .repository-card', { 
      timeout: 10000 
    }).catch(() => {
      return page.waitForSelector('text=/ford-at-home|agent-team-composer/', { timeout: 10000 });
    });
    
    const repoCard = await page.locator('[data-testid="repository-card"], .repository-card, div:has-text("ford-at-home")').first();
    await repoCard.click();
    await page.click('button:has-text("Continue")');
    
    // Wait for parse product page
    await page.waitForTimeout(2000);
    
    // Fill in required fields if present
    try {
      await page.fill('input[name="title"]', 'Test Project', { timeout: 5000 });
      await page.fill('textarea[name="description"]', 'Test project description for initialization testing', { timeout: 5000 });
      await page.click('button:has-text("Next"), button:has-text("Continue")', { timeout: 5000 });
    } catch {
      // Fields might be pre-filled or page might auto-advance
    }
    
    // Check for errors after each navigation
    await page.waitForTimeout(2000);
    
    const errors = (page as any).consoleErrors;
    const initErrors = errors.filter(e => e.includes('Cannot access') && e.includes('before initialization'));
    
    // Log all errors for debugging
    if (errors.length > 0) {
      console.log('Console errors found:', errors);
    }
    
    expect(initErrors).toHaveLength(0);
  });
});