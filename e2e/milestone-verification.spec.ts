import { test, expect } from '@playwright/test';
import { ChildProcess, exec } from 'child_process';
import * as fs from 'fs/promises';
import * as path from 'path';

let serverProcess: ChildProcess | null = null;
const TEST_PORT = 8765;

test.describe('Milestone Feature Verification', () => {
  test.beforeAll(async () => {
    const testDataPath = path.join(process.cwd(), '.agent-team-composer-data.json');
    try {
      await fs.unlink(testDataPath);
    } catch {
      // Ignore if file doesn't exist
    }

    // Kill any existing processes
    try {
      const { execSync } = await import('child_process');
      execSync(`lsof -ti:${TEST_PORT} | xargs kill -9`, { stdio: 'ignore' });
    } catch {
      // Ignore errors
    }

    // Start server
    serverProcess = exec(`agent-team-composer init --fresh --port ${TEST_PORT}`);
    
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Server startup timeout')), 15000);
      
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

  test('Single browser flow: Parse Product → Phase Generation → Verify Milestones', async ({ page }) => {
    // 1. Navigate to the application
    await page.goto(`http://localhost:${TEST_PORT}`);
    await page.waitForLoadState('networkidle');
    
    // 2. Fill the Parse Product form
    await page.fill('input#title', 'Milestone Test Project');
    await page.fill('textarea#description', 'Testing milestone creation in Phase Generation');
    await page.click('[id="domain"]');
    await page.click('[role="option"]:has-text("Developer Tools")');
    
    // 3. Click Continue to Phase Generation
    await page.click('button:has-text("Continue to Phase Generation")');
    
    // 4. Wait for phase generation to complete
    await page.waitForSelector('text="Project Summary"', { timeout: 60000 });
    
    // 5. Continue to Phase Generation step
    await page.click('button:has-text("Continue to Phases")');
    await page.waitForSelector('text="Configure Lifecycle Phases"');
    
    // 6. Approve some phases
    const approveButtons = page.locator('button:has-text("Approve")');
    await approveButtons.first().click();
    
    // 7. Verify milestone info appears
    await expect(page.locator('text="GitHub milestones will be created"')).toBeVisible();
    await expect(page.locator('text="Each approved phase will become a milestone"')).toBeVisible();
    
    // 8. Continue to Review & Submit
    await page.click('button:has-text("Review & Submit")');
    await page.waitForSelector('text="Epic & Issue Organization"');
    
    await page.click('button:has-text("Review & Submit")');
    await page.waitForSelector('text="Review & Submit"');
    
    // 9. Verify milestone mention in final review
    await expect(page.locator('text="These phases will be created as milestones and epics"')).toBeVisible();
    
    console.log('✅ Milestone functionality verified in single browser session');
  });
});