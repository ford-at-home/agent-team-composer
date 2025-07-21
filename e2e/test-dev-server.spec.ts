import { test, expect } from '@playwright/test';

test.describe('Dev Server Test', () => {
  test('Check dev server for console errors', async ({ page }) => {
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

    // Navigate to the dev server
    await page.goto('http://localhost:8080', { waitUntil: 'domcontentloaded' });
    
    // Wait a bit for any async errors
    await page.waitForTimeout(3000);
    
    // Log all console messages
    console.log('\n=== ALL CONSOLE MESSAGES ===');
    consoleMessages.forEach(msg => console.log(msg));
    
    // Log errors specifically
    if (consoleErrors.length > 0) {
      console.log('\n=== CONSOLE ERRORS ===');
      consoleErrors.forEach(err => console.log(err));
    } else {
      console.log('\n=== NO CONSOLE ERRORS! ===');
    }
    
    // Check for app content
    const appElement = await page.$('#root');
    const hasApp = appElement !== null;
    console.log('\n=== APP LOADED ===');
    console.log(`App root element found: ${hasApp}`);
    
    // Check for specific UI elements
    const title = await page.$('h1, h2, h3');
    if (title) {
      const titleText = await title.textContent();
      console.log(`Found title: ${titleText}`);
    }
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/dev-server-test.png' });
    
    // Expect no console errors
    expect(consoleErrors).toHaveLength(0);
  });
});