import { test, expect } from '@playwright/test';
import { exec } from 'child_process';

let serverProcess: ReturnType<typeof exec> | null = null;
const TEST_PORT = 8765;

test.describe('Debug Console Errors', () => {
  test.beforeAll(async () => {
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

  test('Check for console errors', async ({ page }) => {
    // Capture console messages
    const consoleMessages: string[] = [];
    const consoleErrors: string[] = [];
    
    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push(`${msg.type()}: ${text}`);
      if (msg.type() === 'error') {
        consoleErrors.push(text);
      }
    });

    page.on('pageerror', error => {
      consoleErrors.push(`Page error: ${error.message}`);
    });

    // Navigate to the page
    await page.goto(`http://localhost:${TEST_PORT}`, { waitUntil: 'domcontentloaded' });
    
    // Wait a bit for any async errors
    await page.waitForTimeout(3000);
    
    // Log all console messages
    console.log('\n=== ALL CONSOLE MESSAGES ===');
    consoleMessages.forEach(msg => console.log(msg));
    
    // Log errors specifically
    if (consoleErrors.length > 0) {
      console.log('\n=== CONSOLE ERRORS ===');
      consoleErrors.forEach(err => console.log(err));
    }
    
    // Check page content
    const pageContent = await page.content();
    console.log('\n=== PAGE CONTENT (first 500 chars) ===');
    console.log(pageContent.substring(0, 500));
    
    // Check for specific elements
    const body = await page.$('body');
    const bodyText = await body?.textContent();
    console.log('\n=== BODY TEXT ===');
    console.log(bodyText);
    
    // Check network errors
    const failedRequests: string[] = [];
    page.on('requestfailed', request => {
      failedRequests.push(`${request.url()} - ${request.failure()?.errorText}`);
    });
    
    if (failedRequests.length > 0) {
      console.log('\n=== FAILED REQUESTS ===');
      failedRequests.forEach(req => console.log(req));
    }
    
    // Expect no console errors
    expect(consoleErrors).toHaveLength(0);
  });
});