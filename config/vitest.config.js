import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Test environment
    environment: 'jsdom',
    
    // Global setup
    globals: true,
    
    // Test paths
    include: ['tests/frontend/**/*.test.js'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/cypress/**',
      '**/.{idea,git,cache,output,temp}/**',
      '**/tests/frontend/e2e/**' // E2E tests run with Playwright
    ],
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/frontend/**/*.js'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.test.js',
        '**/*.spec.js',
        'coverage/**',
        'dist/**',
        '*.config.js',
        '**/*.d.ts',
        'src/frontend/js/modules/index.js',
        'src/frontend/archived_maps/**',
        'src/frontend/pwa/**'
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 60,
        statements: 70
      }
    },
    
    // Setup files
    setupFiles: ['./tests/setup.js'],
    
    // Reporters
    reporters: ['verbose'],
    
    // Test timeout
    testTimeout: 10000,
    
    // Mock configuration
    mockReset: true,
    clearMocks: true,
    restoreMocks: true
  }
});