/**
 * Quick test to verify Puppeteer can launch
 */
import puppeteer from 'puppeteer';

async function testPuppeteer() {
    console.log('Testing Puppeteer launch...');
    
    try {
        const browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ],
            timeout: 30000
        });
        
        console.log('✅ Browser launched successfully');
        
        const page = await browser.newPage();
        console.log('✅ Page created successfully');
        
        await browser.close();
        console.log('✅ Browser closed successfully');
        
        process.exit(0);
    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    }
}

testPuppeteer();