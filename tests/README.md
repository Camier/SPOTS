# SPOTS Project E2E Tests

Comprehensive end-to-end tests for the SPOTS (Secret Spots in Occitanie) project using Puppeteer.

## Test Coverage

### 1. Security Tests (`map-security.test.js`)
- XSS prevention in spot names, descriptions, and types
- Input validation for coordinates
- Content Security Policy headers
- Safe DOM manipulation methods
- LocalStorage security
- Navigation security

### 2. IGN Integration Tests (`ign-integration.test.js`)
- Layer toggle functionality
- Environmental data display
- Popup tab navigation
- Filter integration with IGN data
- Performance and caching
- Mobile responsiveness

### 3. Accessibility Tests (`accessibility.test.js`)
- WCAG 2.1 compliance using axe-core
- Keyboard navigation
- Screen reader support
- Focus management
- Touch-friendly targets
- Reduced motion support
- Semantic HTML

### 4. Responsive Design Tests (`responsive.test.js`)
- Mobile, tablet, and desktop layouts
- Touch interactions
- Performance on different devices
- Responsive typography
- Orientation changes

## Setup

1. Install dependencies:
```bash
cd tests
npm install
```

2. Ensure the frontend files are available at the correct paths.

3. Start the backend API server on port 8000 (optional for full integration).

## Running Tests

### Run all tests:
```bash
npm test
```

### Run specific test suites:
```bash
npm run test:security       # Security tests only
npm run test:ign           # IGN integration tests
npm run test:accessibility  # Accessibility tests
npm run test:responsive    # Responsive design tests
```

### Run tests in headed mode (see browser):
```bash
npm run test:headed
```

### Debug tests:
```bash
npm run test:debug
```

## Test Configuration

Tests use Puppeteer to automate browser interactions. Key configurations:

- **Timeout**: 30 seconds per test (configurable)
- **Headless**: True by default
- **Viewport**: Varies by test (mobile, tablet, desktop)
- **Network**: Mocked API responses for consistency

## Mocked Data

Tests use mocked API responses to ensure consistency:
- `/api/config`: Returns test IGN API key
- `/api/spots`: Returns test spots data
- `/api/ign/*`: Returns test environmental data

## Writing New Tests

1. Create a new test file in `e2e/` directory
2. Import required modules:
```javascript
const puppeteer = require('puppeteer');
const { expect } = require('chai');
const path = require('path');
```

3. Follow the existing test structure with proper setup/teardown
4. Mock API responses as needed
5. Use meaningful test descriptions

## Best Practices

1. **Selectors**: Use data attributes or IDs for reliable selection
2. **Waits**: Use `waitForSelector` instead of arbitrary timeouts
3. **Assertions**: Be specific about what you're testing
4. **Cleanup**: Always close pages and browsers properly
5. **Performance**: Group related tests to minimize browser launches

## Continuous Integration

These tests can be integrated into CI/CD pipelines. Ensure:
- Headless Chrome dependencies are installed
- Backend API is available or properly mocked
- File paths are correctly configured

## Troubleshooting

### Tests timing out
- Increase timeout in test scripts
- Check network conditions
- Verify selectors are correct

### File not found errors
- Ensure correct file paths
- Check working directory
- Verify files exist

### API errors
- Check if backend is running
- Verify API mocking is working
- Check network interception

## Future Improvements

1. Add visual regression tests
2. Implement performance budgets
3. Add internationalization tests
4. Create custom Puppeteer helpers
5. Add test coverage reporting