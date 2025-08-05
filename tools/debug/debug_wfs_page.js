const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();
    
    // Log console messages
    page.on('console', msg => {
        console.log('PAGE LOG:', msg.text());
    });
    
    // Log page errors
    page.on('pageerror', error => {
        console.log('PAGE ERROR:', error.message);
    });
    
    // Log response errors
    page.on('response', response => {
        if (!response.ok() && !response.url().includes('favicon')) {
            console.log(`RESPONSE ERROR: ${response.status()} - ${response.url()}`);
        }
    });
    
    try {
        console.log('Loading page...');
        await page.goto('http://localhost:8085/test_wfs_resilience.html', {
            waitUntil: 'networkidle2'
        });
        
        // Wait for WFS client to initialize
        await page.waitForTimeout(2000);
        
        // Get service status
        const status = await page.evaluate(() => {
            if (window.wfsClient) {
                return window.wfsClient.getServiceStatus();
            }
            return null;
        });
        
        console.log('WFS Service Status:', JSON.stringify(status, null, 2));
        
        // Try to click test button
        console.log('Testing normal operation...');
        await page.click('button[onclick="testNormalOperation()"]');
        await page.waitForTimeout(3000);
        
        // Get test results
        const testLog = await page.evaluate(() => {
            const logDiv = document.getElementById('test-log');
            return logDiv ? logDiv.innerText : 'No test log found';
        });
        
        console.log('Test Results:\n', testLog);
        
    } catch (error) {
        console.error('Error:', error);
    }
    
    await browser.close();
})();