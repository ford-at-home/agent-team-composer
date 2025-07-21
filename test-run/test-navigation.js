const puppeteer = require('puppeteer');

(async () => {
  console.log('Starting navigation test...');
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  // Collect console errors
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  
  page.on('pageerror', error => {
    errors.push(error.message);
  });
  
  try {
    // Navigate to the application
    console.log('1. Loading application...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
    await page.waitForTimeout(2000);
    
    // Check for initial errors
    const initErrors = errors.filter(e => 
      e.includes('Cannot access') && e.includes('before initialization')
    );
    
    if (initErrors.length > 0) {
      console.error('❌ INITIALIZATION ERROR ON FIRST PAGE:', initErrors);
    } else {
      console.log('✅ No initialization errors on first page');
    }
    
    // Try to find and click a repository
    console.log('2. Looking for repository to select...');
    try {
      // Wait for repositories to load
      await page.waitForSelector('div[class*="card"], [data-testid="repository-card"]', { timeout: 5000 });
      
      // Click the first repository
      const repo = await page.$('div[class*="card"], [data-testid="repository-card"]');
      if (repo) {
        await repo.click();
        console.log('   - Clicked repository');
        await page.waitForTimeout(1000);
        
        // Look for continue button
        const continueBtn = await page.$('button:has-text("Continue"), button:has-text("Select")');
        if (continueBtn) {
          await continueBtn.click();
          console.log('   - Clicked continue button');
        }
      }
    } catch (e) {
      console.log('   - Could not find repository (might need auth)');
    }
    
    // Wait for navigation
    await page.waitForTimeout(3000);
    
    // Check for errors after navigation
    const navErrors = errors.filter(e => 
      e.includes('Cannot access') && e.includes('before initialization')
    );
    
    if (navErrors.length > 0) {
      console.error('❌ INITIALIZATION ERROR AFTER NAVIGATION:', navErrors);
    } else {
      console.log('✅ No initialization errors after navigation');
    }
    
    // Print all errors for debugging
    if (errors.length > 0) {
      console.log('\nAll console errors found:');
      errors.forEach(e => console.log('  -', e));
    }
    
  } catch (error) {
    console.error('Test error:', error.message);
  } finally {
    await browser.close();
  }
  
  // Final result
  const hasInitError = errors.some(e => 
    e.includes('Cannot access') && e.includes('before initialization')
  );
  
  if (hasInitError) {
    console.log('\n❌ FAILED: Initialization error still present!');
    process.exit(1);
  } else {
    console.log('\n✅ SUCCESS: No initialization errors found!');
    process.exit(0);
  }
})();