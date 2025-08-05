/**
 * Shared Puppeteer configuration for E2E tests
 */

export const puppeteerConfig = {
    headless: true, // Use new headless mode (v22+)
    args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage', // Overcome limited resource problems
        '--disable-gpu', // Disable GPU hardware acceleration
        '--disable-web-security', // For testing cross-origin scenarios
        '--disable-features=IsolateOrigins,site-per-process', // Helps with iframe interactions
    ],
    // Increase timeout for slower CI environments
    timeout: 60000,
};

export default puppeteerConfig;