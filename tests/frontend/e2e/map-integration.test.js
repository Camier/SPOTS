import { test, expect } from '@playwright/test';

test.describe('SPOTS Map Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Start on the main page
    await page.goto('http://localhost:8081');
  });

  test('should redirect to optimized map', async ({ page }) => {
    // Wait for redirect
    await page.waitForURL('**/regional-map-optimized.html');
    
    // Verify we're on the right page
    expect(page.url()).toContain('regional-map-optimized.html');
    
    // Check page title
    await expect(page).toHaveTitle('Spots Secrets - Carte Régionale Occitanie');
  });

  test('should load map container', async ({ page }) => {
    await page.goto('http://localhost:8081/regional-map-optimized.html');
    
    // Check map element exists
    const mapElement = page.locator('#map');
    await expect(mapElement).toBeVisible();
    
    // Check it has full viewport height
    const mapBox = await mapElement.boundingBox();
    const viewportSize = page.viewportSize();
    expect(mapBox.height).toBe(viewportSize.height);
  });

  test('should display info panel with controls', async ({ page }) => {
    await page.goto('http://localhost:8081/regional-map-optimized.html');
    
    // Check info panel
    const infoPanel = page.locator('.info-panel');
    await expect(infoPanel).toBeVisible();
    
    // Check title
    await expect(infoPanel.locator('h3')).toHaveText('Spots Secrets Occitanie');
    
    // Check filter buttons
    const filterButtons = page.locator('.filter-btn');
    await expect(filterButtons).toHaveCount(5); // All, Cascades, Grottes, Sources, Ruines
    
    // Check department selector
    const deptSelect = page.locator('#department-select');
    await expect(deptSelect).toBeVisible();
    
    // Check stats container
    const statsContainer = page.locator('#stats-container');
    await expect(statsContainer).toBeVisible();
  });

  test('should filter spots by type', async ({ page }) => {
    await page.goto('http://localhost:8081/regional-map-optimized.html');
    
    // Wait for initial load
    await page.waitForTimeout(2000);
    
    // Click on Cascades filter
    const cascadesBtn = page.locator('.filter-btn[data-filter-type="waterfall"]');
    await cascadesBtn.click();
    
    // Check button is active
    await expect(cascadesBtn).toHaveClass(/active/);
    
    // Other buttons should not be active
    const allBtn = page.locator('.filter-btn[data-filter-type="all"]');
    await expect(allBtn).not.toHaveClass(/active/);
  });

  test('should filter by department', async ({ page }) => {
    await page.goto('http://localhost:8081/regional-map-optimized.html');
    
    // Select Ariège department
    await page.selectOption('#department-select', '09');
    
    // Wait for map update
    await page.waitForTimeout(1000);
    
    // Verify selection
    const selectedValue = await page.locator('#department-select').inputValue();
    expect(selectedValue).toBe('09');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Block API calls
    await page.route('**/api/spots/**', route => route.abort());
    
    await page.goto('http://localhost:8081/regional-map-optimized.html');
    
    // Check for error handling
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.waitForTimeout(2000);
    
    // Should have error messages
    expect(consoleErrors.some(err => err.includes('Error loading spots'))).toBeTruthy();
  });

  test('should display map layers control', async ({ page }) => {
    await page.goto('http://localhost:8081/regional-map-optimized.html');
    
    // Look for Leaflet layer control
    const layerControl = page.locator('.leaflet-control-layers');
    await expect(layerControl).toBeVisible();
    
    // Expand layer control
    await layerControl.click();
    
    // Check for multiple layer options
    const layerInputs = page.locator('.leaflet-control-layers-base input');
    const count = await layerInputs.count();
    expect(count).toBeGreaterThan(5); // At least 6 layers
  });

  test('should load spots and display markers', async ({ page }) => {
    // Mock API response
    await page.route('**/api/spots/quality**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 2,
          spots: [
            {
              id: 1,
              name: 'Test Waterfall',
              latitude: 43.8,
              longitude: 1.8,
              type: 'waterfall',
              description: 'Beautiful waterfall',
              confidence_score: 0.9,
              elevation: 400
            },
            {
              id: 2,
              name: 'Test Cave',
              latitude: 43.7,
              longitude: 1.9,
              type: 'cave',
              description: 'Deep cave',
              confidence_score: 0.85,
              elevation: 600
            }
          ]
        })
      });
    });

    await page.goto('http://localhost:8081/regional-map-optimized.html');
    
    // Wait for markers to load
    await page.waitForTimeout(2000);
    
    // Check stats updated
    await expect(page.locator('#stats-container')).toContainText('2 spots affichés');
    
    // Check for marker clusters or individual markers
    const markers = page.locator('.leaflet-marker-icon, .leaflet-cluster-icon');
    const markerCount = await markers.count();
    expect(markerCount).toBeGreaterThan(0);
  });

  test('should show popup on marker click', async ({ page }) => {
    // Mock single spot
    await page.route('**/api/spots/quality**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 1,
          spots: [{
            id: 1,
            name: 'Cascade du Test',
            latitude: 43.8,
            longitude: 1.8,
            type: 'waterfall',
            description: 'Test waterfall description',
            confidence_score: 0.95,
            elevation: 450
          }]
        })
      });
    });

    await page.goto('http://localhost:8081/regional-map-optimized.html');
    await page.waitForTimeout(2000);
    
    // Click on marker
    const marker = page.locator('.spot-marker').first();
    if (await marker.isVisible()) {
      await marker.click();
      
      // Check popup appears
      const popup = page.locator('.leaflet-popup');
      await expect(popup).toBeVisible();
      
      // Check popup content
      await expect(popup).toContainText('Cascade du Test');
      await expect(popup).toContainText('waterfall');
    }
  });

  test('should handle multiple filter combinations', async ({ page }) => {
    await page.goto('http://localhost:8081/regional-map-optimized.html');
    await page.waitForTimeout(2000);
    
    // Select caves filter
    await page.click('.filter-btn[data-filter-type="cave"]');
    
    // Then select Ariège department
    await page.selectOption('#department-select', '09');
    
    // Wait for updates
    await page.waitForTimeout(1000);
    
    // Both filters should be active
    const caveBtn = page.locator('.filter-btn[data-filter-type="cave"]');
    await expect(caveBtn).toHaveClass(/active/);
    
    const deptValue = await page.locator('#department-select').inputValue();
    expect(deptValue).toBe('09');
  });
});