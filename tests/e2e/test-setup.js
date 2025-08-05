/**
 * Test setup and utilities for E2E tests
 */

import { beforeAll } from 'vitest';

// Increase test timeout for CI environments
beforeAll(() => {
    // Check if running in CI or limited environment
    const isCI = process.env.CI || process.env.GITHUB_ACTIONS || process.env.GITLAB_CI;
    
    if (isCI) {
        console.log('Running in CI environment - using extended timeouts');
        // Set longer timeout for CI environments
        vitest.setConfig({ testTimeout: 120000 });
    }
});

// Helper to wait for element with retries
export async function waitForElement(page, selector, options = {}) {
    const { timeout = 30000, visible = true } = options;
    
    try {
        await page.waitForSelector(selector, { timeout, visible });
        return true;
    } catch (error) {
        console.error(`Failed to find element: ${selector}`);
        return false;
    }
}

// Helper to safely close browser
export async function closeBrowser(browser) {
    if (browser && browser.isConnected()) {
        try {
            await browser.close();
        } catch (error) {
            console.error('Error closing browser:', error);
            // Force kill if normal close fails
            if (browser.process()) {
                browser.process().kill('SIGKILL');
            }
        }
    }
}