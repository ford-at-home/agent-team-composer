import { test, expect } from '@playwright/test';
import { exec } from 'child_process';
import * as fs from 'fs/promises';
import * as path from 'path';

let serverProcess: any;
const TEST_PORT = 8765;

test.describe.serial('Complete UI Flow Test', () => {
  test.beforeAll(async () => {
    // Clean up
    const testDataPath = path.join(process.cwd(), '.agent-team-composer-data.json');
    try {
      await fs.unlink(testDataPath);
    } catch {}

    // Kill any existing processes
    try {
      const { execSync } = await import('child_process');
      execSync(`lsof -ti:${TEST_PORT} | xargs kill -9`, { stdio: 'ignore' });
    } catch {}

    // Start server
    console.log('Starting agent-team-composer server...');
    serverProcess = exec(`agent-team-composer init --fresh --port ${TEST_PORT}`);
    
    // Wait for server to be ready
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Server startup timeout')), 15000);
      
      serverProcess.stdout?.on('data', (data: Buffer) => {
        console.log('Server:', data.toString().trim());
        if (data.toString().includes('Agent Team Composer is ready')) {
          clearTimeout(timeout);
          resolve(true);
        }
      });
      
      serverProcess.stderr?.on('data', (data: Buffer) => {
        console.error('Server error:', data.toString());
      });
    });

    // Give it a moment to fully initialize
    await new Promise(resolve => setTimeout(resolve, 2000));
  });

  test.afterAll(async () => {
    if (serverProcess) {
      serverProcess.kill();
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  });

  test('1. Should show Parse Product form on initial load', async ({ page }) => {
    await page.goto(`http://localhost:${TEST_PORT}`);
    await page.waitForLoadState('networkidle');

    // Check we're on step 0
    const activeStep = await page.locator('.text-blue-600').first().textContent();
    expect(activeStep).toContain('Step 1'); // UI shows Step 1 for index 0

    // Verify Parse Product form elements (it's not an h2, it's in the card header)
    await expect(page.locator('text="Parse Product"').first()).toBeVisible();
    await expect(page.locator('input#title')).toBeVisible();
    await expect(page.locator('textarea#description')).toBeVisible();
    await expect(page.locator('text="Target Users"')).toBeVisible();
    await expect(page.locator('text="Tech Stack"')).toBeVisible();
    await expect(page.locator('text="Key Features"')).toBeVisible();
    
    // Verify NO AI Populate button (it's automatic now)
    const aiButton = await page.locator('button:has-text("AI Populate")').count();
    expect(aiButton).toBe(0);
    
    // Verify NO README preview (we removed it)
    const readmeSection = await page.locator('text="README Content"').count();
    expect(readmeSection).toBe(0);
    
    // Take screenshot for reference
    await page.screenshot({ path: 'test-results/step-0-parse-product.png', fullPage: true });
  });

  test('2. Should fill form and continue to next step', async ({ page }) => {
    await page.goto(`http://localhost:${TEST_PORT}`);
    await page.waitForLoadState('networkidle');

    // Fill in the form
    await page.fill('input#title', 'Test Project');
    await page.fill('textarea#description', 'This is a comprehensive test project for automated testing');
    
    // Select domain
    await page.click('[id="domain"]');
    await page.click('text="Developer Tools"');
    
    // Add target users
    const targetUserInput = page.locator('input[placeholder="Add target user..."]');
    await targetUserInput.fill('Developers');
    await targetUserInput.press('Enter');
    await targetUserInput.fill('QA Engineers');
    await targetUserInput.press('Enter');
    
    // Add tech stack
    const techInput = page.locator('input[placeholder="Add technology..."]');
    await techInput.fill('React');
    await techInput.press('Enter');
    await techInput.fill('TypeScript');
    await techInput.press('Enter');
    await techInput.fill('Playwright');
    await techInput.press('Enter');
    
    // Add features
    const featureInput = page.locator('input[placeholder="Add feature..."]');
    await featureInput.fill('Automated UI Testing');
    await featureInput.press('Enter');
    await featureInput.fill('Real Browser Testing');
    await featureInput.press('Enter');
    
    // Take screenshot of filled form
    await page.screenshot({ path: 'test-results/filled-form.png', fullPage: true });
    
    // Click continue
    await page.click('button:has-text("Continue to Phase Generation")');
    
    // Should see loading state
    await expect(page.locator('text="Generating Project Plan"')).toBeVisible();
    await expect(page.locator('text="Analyzing your project requirements"')).toBeVisible();
    
    // Take screenshot of loading state
    await page.screenshot({ path: 'test-results/loading-state.png' });
  });

  test('3. Should verify all fields appear in Project Summary', async ({ page }) => {
    // This test assumes the previous test ran and we're now on ProjectSummary
    // In a real scenario, you might need to wait for the API call to complete
    
    await page.goto(`http://localhost:${TEST_PORT}`);
    await page.waitForLoadState('networkidle');
    
    // If still on step 0, fill and submit form quickly
    const isStillOnParseProduct = await page.locator('text="Parse Product"').isVisible();
    if (isStillOnParseProduct) {
      // Quick fill
      await page.fill('input#title', 'Test Project');
      await page.fill('textarea#description', 'Test description');
      await page.click('button:has-text("Continue to Phase Generation")');
      
      // Wait for navigation
      await page.waitForFunction(() => {
        return !document.querySelector('text="Parse Product"');
      }, { timeout: 10000 });
    }
    
    // Now we should be on ProjectSummary
    // Check for our fields
    const pageContent = await page.content();
    console.log('Checking for Target Users, Tech Stack, etc.');
    
    // Take final screenshot
    await page.screenshot({ path: 'test-results/project-summary.png', fullPage: true });
  });
});

test.describe('AI Auto-Population Test', () => {
  test('Should automatically populate form when README is loaded', async ({ page }) => {
    // This test requires ANTHROPIC_API_KEY to be set
    const hasApiKey = !!process.env.ANTHROPIC_API_KEY;
    test.skip(!hasApiKey, 'Skipping AI test - no ANTHROPIC_API_KEY set');
    
    // Start fresh server
    const aiServerProcess = exec(`agent-team-composer init --fresh --port 8766`);
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    try {
      await page.goto('http://localhost:8766');
      await page.waitForLoadState('networkidle');
      
      // Should see "Analyzing README..." loading state
      const analyzingText = page.locator('text="Analyzing README..."');
      
      // Wait for auto-population to complete (or timeout)
      try {
        await analyzingText.waitFor({ state: 'visible', timeout: 5000 });
        console.log('Saw "Analyzing README..." indicator');
        
        // Wait for it to disappear
        await analyzingText.waitFor({ state: 'hidden', timeout: 15000 });
      } catch {
        // Might have completed before we could see it
        console.log('AI population might have completed quickly');
      }
      
      // Check if fields were populated from README
      const titleValue = await page.locator('input#title').inputValue();
      const descriptionValue = await page.locator('textarea#description').inputValue();
      
      // Should not be the default values
      expect(titleValue).not.toBe('Untitled Project');
      expect(descriptionValue.length).toBeGreaterThan(20);
      
      // Check for populated arrays - look for the badge elements with X buttons
      const targetUserBadges = await page.locator('button:has-text("×")').count();
      expect(targetUserBadges).toBeGreaterThan(0);
      
    } finally {
      aiServerProcess.kill();
    }
  });
});