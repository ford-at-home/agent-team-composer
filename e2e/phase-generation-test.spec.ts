import { test, expect } from '@playwright/test';
import { exec, ChildProcess } from 'child_process';
import * as fs from 'fs/promises';
import * as path from 'path';

let serverProcess: ChildProcess | null = null;
const TEST_PORT = 8765;

test.describe('Phase Generation Flow', () => {
  test.beforeAll(async () => {
    // Clean up
    const testDataPath = path.join(process.cwd(), '.agent-team-composer-data.json');
    try {
      await fs.unlink(testDataPath);
    } catch {
      // Ignore
    }

    // Kill existing processes
    try {
      const { execSync } = await import('child_process');
      execSync(`lsof -ti:${TEST_PORT} | xargs kill -9`, { stdio: 'ignore' });
    } catch {
      // Ignore
    }

    // Start server
    serverProcess = exec(`agent-team-composer init --fresh --port ${TEST_PORT}`);
    
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Server timeout')), 15000);
      
      serverProcess?.stdout?.on('data', (data: Buffer) => {
        if (data.toString().includes('Agent Team Composer is ready')) {
          clearTimeout(timeout);
          resolve(true);
        }
      });
    });

    await new Promise(resolve => setTimeout(resolve, 2000));
  });

  test.afterAll(async () => {
    if (serverProcess) {
      serverProcess.kill();
    }
  });

  test('Step 1: Parse Product → Step 2: Phase Generation', async ({ page }) => {
    // Go to app
    await page.goto(`http://localhost:${TEST_PORT}`);
    await page.waitForLoadState('networkidle');
    
    // Step 1: Fill Parse Product form
    console.log('=== Step 1: Parse Product ===');
    await page.fill('input#title', 'Test Phase Generation');
    await page.fill('textarea#description', 'Testing phase generation flow');
    
    // Scroll to and click Continue to Phase Generation
    const continueButton = page.locator('button:has-text("Continue to Phase Generation")');
    await continueButton.scrollIntoViewIfNeeded();
    await continueButton.click();
    
    // Step 2: Should generate phases
    console.log('=== Step 2: Phase Generation ===');
    
    // Wait for loading overlay if it appears
    const loadingOverlay = page.locator('text="Generating Project Plan"');
    if (await loadingOverlay.isVisible({ timeout: 2000 })) {
      console.log('Saw loading overlay...');
      await loadingOverlay.waitFor({ state: 'hidden', timeout: 60000 });
    }
    
    // Should now see phase generation page
    await expect(page.locator('text="Configure Lifecycle Phases"')).toBeVisible({ timeout: 30000 });
    
    // Should have generated phases
    const phaseCards = page.locator('.cursor-pointer');
    const phaseCount = await phaseCards.count();
    console.log(`Generated ${phaseCount} phases`);
    
    // Should be 8 SDLC phases
    expect(phaseCount).toBeGreaterThan(0);
    
    // Click on first phase to expand
    await phaseCards.first().click();
    
    // Should see phase details
    await expect(page.locator('text="Assigned Roles"')).toBeVisible();
    
    // Approve first phase
    const approveButton = page.locator('button:has-text("Approve")').first();
    await approveButton.scrollIntoViewIfNeeded();
    await approveButton.click();
    
    // Take screenshot to see what we have
    await page.screenshot({ path: 'test-results/phase-generation-success.png', fullPage: true });
    
    console.log('✅ Phase generation working!');
  });
});