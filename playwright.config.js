import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests
 */
export default defineConfig({
  // Test directory
  testDir: './tests/frontend/e2e',
  
  // Test match pattern
  testMatch: '**/*.test.js',
  
  // Timeout per test
  timeout: 30 * 1000,
  
  // Test execution
  fullyParallel: true,
  workers: process.env.CI ? 1 : undefined,
  
  // Retry failed tests
  retries: process.env.CI ? 2 : 0,
  
  // Reporter
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],
  
  // Global test settings
  use: {
    // Base URL
    baseURL: 'http://localhost:8081',
    
    // Trace on failure
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Action timeout
    actionTimeout: 10 * 1000,
    
    // Navigation timeout
    navigationTimeout: 30 * 1000,
  },
  
  // Configure projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile viewports
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  
  // Run local servers before tests
  webServer: [
    {
      command: 'node server.js',
      port: 8081,
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'python -m src.backend.main',
      port: 8000,
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    }
  ],
});