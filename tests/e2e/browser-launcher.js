/**
 * Browser launcher with proper error handling
 */
import puppeteer from 'puppeteer';
import { executablePath } from 'puppeteer';

export async function launchBrowser(options = {}) {
    const defaultOptions = {
        headless: 'new', // Use new headless mode
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--window-size=1280,800'
        ],
        timeout: 60000,
        // Use system Chrome if available
        executablePath: process.env.PUPPETEER_EXEC_PATH || executablePath(),
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    let browser;
    let retries = 3;
    
    while (retries > 0) {
        try {
            browser = await puppeteer.launch(finalOptions);
            console.log('Browser launched successfully');
            return browser;
        } catch (error) {
            retries--;
            console.error(`Failed to launch browser (${3 - retries}/3):`, error.message);
            
            if (retries === 0) {
                // Last resort: try with dumpio for debugging
                console.log('Attempting final launch with debug output...');
                try {
                    browser = await puppeteer.launch({
                        ...finalOptions,
                        dumpio: true
                    });
                    return browser;
                } catch (finalError) {
                    throw new Error(`Failed to launch browser after all attempts: ${finalError.message}`);
                }
            }
            
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    
    throw new Error('Failed to launch browser');
}

export async function closeBrowser(browser) {
    if (!browser) return;
    
    try {
        const pages = await browser.pages();
        await Promise.all(pages.map(page => page.close().catch(() => {})));
        await browser.close();
    } catch (error) {
        console.error('Error closing browser gracefully:', error.message);
        // Force kill if graceful close fails
        try {
            if (browser.process()) {
                browser.process().kill('SIGKILL');
            }
        } catch (killError) {
            console.error('Failed to force kill browser:', killError.message);
        }
    }
}