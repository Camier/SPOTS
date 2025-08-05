/**
 * Fixed Puppeteer configuration for E2E tests
 * Based on official Puppeteer troubleshooting guide
 */

import { execSync } from 'child_process';

// Try to find system Chrome/Chromium
function findChrome() {
    const possiblePaths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/usr/bin/google-chrome-beta',
        '/usr/bin/google-chrome-unstable',
    ];
    
    for (const path of possiblePaths) {
        try {
            execSync(`which ${path}`);
            console.log(`Found Chrome at: ${path}`);
            return path;
        } catch (e) {
            // Continue searching
        }
    }
    
    return undefined; // Use Puppeteer's bundled Chrome
}

export const puppeteerConfig = {
    headless: 'new', // Use new headless mode explicitly
    executablePath: findChrome(), // Use system Chrome if available
    args: [
        '--no-sandbox', // Required for CI/Docker environments
        '--disable-setuid-sandbox', // Disable setuid sandbox
        '--disable-dev-shm-usage', // Overcome limited resource problems
        '--disable-gpu', // Disable GPU hardware acceleration
        '--disable-web-security', // For testing cross-origin scenarios
        '--disable-features=IsolateOrigins,site-per-process', // Helps with iframe interactions
        '--disable-blink-features=AutomationControlled', // Avoid detection
        '--window-size=1280,800',
        `--user-data-dir=/tmp/puppeteer-user-data-${Date.now()}-${Math.random().toString(36).substring(7)}`, // Use unique temp directory
    ],
    // Increase timeout for slower CI environments
    timeout: 60000,
    // Additional options for stability
    dumpio: false, // Set to true for debugging
    ignoreDefaultArgs: ['--disable-extensions'], // Keep extensions enabled
    pipe: false, // Use WebSocket instead of pipe
};

// Set environment variable for Chrome sandbox (if needed)
if (process.platform === 'linux') {
    process.env.CHROME_DEVEL_SANDBOX = '/usr/local/sbin/chrome-devel-sandbox';
}

export default puppeteerConfig;