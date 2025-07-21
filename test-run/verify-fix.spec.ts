import { chromium } from 'playwright';

(async () => {
  console.log('🔍 Testing for initialization errors...\n');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const errors: string[] = [];
  
  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      errors.push(text);
      
      // Check for the specific error
      if (text.includes('Cannot access') && text.includes('before initialization')) {
        console.error('❌ INITIALIZATION ERROR DETECTED:', text);
      }
    }
  });
  
  page.on('pageerror', error => {
    errors.push(error.message);
  });

  try {
    // Test 1: Load the main page
    console.log('1️⃣ Loading main page...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(3000);
    
    const mainPageInitErrors = errors.filter(e => 
      e.includes('Cannot access') && e.includes('before initialization')
    );
    
    if (mainPageInitErrors.length === 0) {
      console.log('   ✅ No initialization errors on main page\n');
    }
    
    // Test 2: Try to navigate to repository selection
    console.log('2️⃣ Testing repository selection page...');
    
    // Check if we see any repository cards or error messages
    const pageContent = await page.content();
    
    if (pageContent.includes('Failed to fetch') || pageContent.includes('CLI tool')) {
      console.log('   ⚠️  Cannot test repository selection (CLI not configured)\n');
    } else {
      // Try to find and click a repository if available
      try {
        await page.waitForSelector('.card, [class*="card"]', { timeout: 5000 });
        const cards = await page.$$('.card, [class*="card"]');
        
        if (cards.length > 0) {
          console.log(`   📦 Found ${cards.length} repository cards`);
          await cards[0].click();
          await page.waitForTimeout(2000);
          
          // Try to click continue
          const buttons = await page.$$('button');
          for (const button of buttons) {
            const text = await button.textContent();
            if (text?.includes('Continue') || text?.includes('Select')) {
              await button.click();
              console.log('   🔄 Navigated to next page');
              break;
            }
          }
          
          await page.waitForTimeout(3000);
        }
      } catch (e) {
        console.log('   ℹ️  No repositories found to test navigation\n');
      }
    }
    
    // Final check
    const allInitErrors = errors.filter(e => 
      e.includes('Cannot access') && e.includes('before initialization')
    );
    
    console.log('📊 Final Results:');
    console.log('================');
    
    if (allInitErrors.length === 0) {
      console.log('✅ SUCCESS: No initialization errors found!');
      console.log('The fix appears to be working correctly.\n');
    } else {
      console.log(`❌ FAILURE: Found ${allInitErrors.length} initialization errors:`);
      allInitErrors.forEach(e => console.log(`   - ${e}`));
      console.log('');
    }
    
    if (errors.length > 0) {
      console.log('ℹ️  Other console errors (non-critical):');
      const otherErrors = errors.filter(e => 
        !e.includes('Cannot access') || !e.includes('before initialization')
      );
      otherErrors.slice(0, 5).forEach(e => console.log(`   - ${e.substring(0, 100)}...`));
      if (otherErrors.length > 5) {
        console.log(`   ... and ${otherErrors.length - 5} more`);
      }
    }
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
})();