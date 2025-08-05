/**
 * E2E Tests for IGN OpenData Integration
 * Tests map layers, environmental data, and interactive features
 */

import puppeteer from 'puppeteer';
import puppeteerConfig from './puppeteer-config-fixed.js';
import { expect } from 'chai';
import path from 'node:path';

import { fileURLToPath } from 'node:url';
import { describe, it, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


describe('IGN Integration Tests', () => {
    let browser;
    let page;
    const baseUrl = 'http://localhost:8085';

    beforeAll(async () => {
        browser = await puppeteer.launch(puppeteerConfig);
    });

    afterAll(async () => {
        await browser.close();
    });

    beforeEach(async () => {
        page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });
        
        // Mock API responses
        await page.setRequestInterception(true);
        page.on('request', (request) => {
            const url = request.url();
            
            if (url.includes('/api/config')) {
                request.respond({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({ ign_api_key: 'test-key' })
                });
            } else if (url.includes('/api/spots') && !url.includes('/environment')) {
                request.respond({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        total: 2,
                        spots: [
                            {
                                id: 1,
                                name: 'Cascade secrète',
                                type: 'waterfall',
                                latitude: 43.6047,
                                longitude: 1.4442,
                                elevation: 450,
                                description: 'Hidden waterfall in forest'
                            },
                            {
                                id: 2,
                                name: 'Grotte ancienne',
                                type: 'cave',
                                latitude: 43.5,
                                longitude: 1.3,
                                elevation: 800,
                                description: 'Ancient cave system'
                            }
                        ]
                    })
                });
            } else if (url.includes('/api/ign/spots/1/environment')) {
                request.respond({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        spot: { id: 1, name: 'Cascade secrète' },
                        environment: {
                            forest: {
                                coverage_percent: 75,
                                dominant_type: 'Forêt de feuillus',
                                canopy_density: 'Dense'
                            },
                            terrain: {
                                level: 'Moderate',
                                description: 'Some elevation changes, basic fitness required',
                                factors: {
                                    slope: '12.5°',
                                    elevation_gain: '160m',
                                    ruggedness: '0.70'
                                }
                            },
                            elevation: {
                                spot_elevation: 450,
                                slope_average: 12.5
                            },
                            accessibility: {
                                nearest_road: 450,
                                nearest_trail: 120,
                                nearest_parking: 850,
                                recommended_approach: 'From north via forest trail'
                            }
                        }
                    })
                });
            } else if (url.includes('/api/ign/map-layers/ign')) {
                request.respond({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        layers: {
                            forest: {
                                name: 'Forêts',
                                url: 'https://wxs.ign.fr/test/forest/{z}/{x}/{y}',
                                opacity: 0.6
                            },
                            elevation_contours: {
                                name: 'Courbes de niveau',
                                url: 'https://wxs.ign.fr/test/elevation/{z}/{x}/{y}',
                                opacity: 0.8
                            },
                            slopes: {
                                name: 'Pentes',
                                url: 'https://wxs.ign.fr/test/slopes/{z}/{x}/{y}',
                                opacity: 0.5
                            }
                        }
                    })
                });
            } else {
                request.continue();
            }
        });
    });

    afterEach(async () => {
        await page.close();
    });

    describe('Layer Toggle Tests', () => {
        it('should load and display IGN layer controls', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.layer-control', { timeout: 5000 });
            
            // Check all layer toggles are present
            const layerToggles = await page.$$('.layer-toggle');
            expect(layerToggles).to.have.lengthOf(6); // 6 layer types
            
            // Verify layer names
            const layerNames = await page.$$eval('.layer-name', els => 
                els.map(el => el.textContent)
            );
            expect(layerNames).to.include('Forêts');
            expect(layerNames).to.include('Courbes de niveau');
            expect(layerNames).to.include('Pentes');
        });

        it('should toggle layers on and off', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.layer-control', { timeout: 5000 });
            
            // Click forest layer toggle
            const forestToggle = await page.$('[data-layer="forest"]');
            await forestToggle.click();
            
            // Check toggle is active
            const isActive = await page.$eval('[data-layer="forest"]', el => 
                el.classList.contains('active')
            );
            expect(isActive).to.be.true;
            
            // Check switch is active
            const switchActive = await page.$eval('[data-layer="forest"] .toggle-switch', el => 
                el.classList.contains('active')
            );
            expect(switchActive).to.be.true;
            
            // Click again to deactivate
            await forestToggle.click();
            const isInactive = await page.$eval('[data-layer="forest"]', el => 
                el.classList.contains('active')
            );
            expect(isInactive).to.be.false;
        });

        it('should maintain multiple active layers', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.layer-control', { timeout: 5000 });
            
            // Activate multiple layers
            await page.click('[data-layer="forest"]');
            await page.click('[data-layer="elevation_contours"]');
            await page.click('[data-layer="hiking_trails"]');
            
            // Count active layers
            const activeCount = await page.$$eval('.layer-toggle.active', els => els.length);
            expect(activeCount).to.equal(3);
        });
    });

    describe('Environmental Data Display', () => {
        it('should show environment panel when clicking a spot', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Click on a marker
            const marker = await page.$('.leaflet-marker-icon');
            await marker.click();
            
            // Wait for environment panel
            await page.waitForSelector('.environment-panel.visible', { timeout: 5000 });
            
            // Check panel content
            const panelVisible = await page.$eval('.environment-panel', el => 
                el.classList.contains('visible')
            );
            expect(panelVisible).to.be.true;
        });

        it('should display forest coverage data', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Click marker
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.environment-panel.visible', { timeout: 5000 });
            
            // Check forest data
            const forestCoverage = await page.$eval('.env-section', section => {
                const text = section.textContent;
                return text.includes('75% de couverture');
            });
            expect(forestCoverage).to.be.true;
            
            // Check progress bar
            const barWidth = await page.$eval('.env-bar-fill', el => 
                el.style.width
            );
            expect(barWidth).to.equal('75%');
        });

        it('should display terrain difficulty', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.terrain-badge', { timeout: 5000 });
            
            const terrainLevel = await page.$eval('.terrain-badge', el => 
                el.textContent
            );
            expect(terrainLevel).to.equal('Moderate');
            
            // Check badge has correct class
            const hasModerateClass = await page.$eval('.terrain-badge', el => 
                el.classList.contains('moderate')
            );
            expect(hasModerateClass).to.be.true;
        });

        it('should display accessibility information', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.environment-panel.visible', { timeout: 5000 });
            
            const accessibilityText = await page.$eval('#environmentContent', el => 
                el.textContent
            );
            expect(accessibilityText).to.include('Route la plus proche: 450m');
            expect(accessibilityText).to.include('Sentier le plus proche: 120m');
            expect(accessibilityText).to.include('From north via forest trail');
        });
    });

    describe('Popup Tab Navigation', () => {
        it('should have three tabs in popup', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.popup-tabs', { timeout: 5000 });
            
            const tabs = await page.$$('.popup-tab');
            expect(tabs).to.have.lengthOf(3);
            
            const tabTexts = await page.$$eval('.popup-tab', tabs => 
                tabs.map(tab => tab.textContent.trim())
            );
            expect(tabTexts).to.include('Info');
            expect(tabTexts).to.include('Environnement');
            expect(tabTexts).to.include('Accès');
        });

        it('should switch between tabs', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.popup-tabs', { timeout: 5000 });
            
            // Click environment tab
            await page.evaluate(() => {
                const envTab = Array.from(document.querySelectorAll('.popup-tab'))
                    .find(tab => tab.textContent.includes('Environnement'));
                window.showPopupTab({ target: envTab }, 'environment');
            });
            
            // Check environment content is visible
            const envContentVisible = await page.$eval('#popup-environment', el => 
                el.classList.contains('active')
            );
            expect(envContentVisible).to.be.true;
            
            // Check info content is hidden
            const infoContentHidden = await page.$eval('#popup-info', el => 
                !el.classList.contains('active')
            );
            expect(infoContentHidden).to.be.true;
        });

        it('should load environment data in popup tab', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.popup-tabs', { timeout: 5000 });
            
            // Switch to environment tab
            await page.evaluate(() => {
                const envTab = Array.from(document.querySelectorAll('.popup-tab'))
                    .find(tab => tab.textContent.includes('Environnement'));
                window.showPopupTab({ target: envTab }, 'environment');
            });
            
            await page.waitForTimeout(1000); // Wait for data load
            
            const envContent = await page.$eval('#popup-environment', el => el.textContent);
            expect(envContent).to.include('Forêt: 75%');
            expect(envContent).to.include('Terrain: Moderate');
        });
    });

    describe('Filter Integration', () => {
        it('should filter spots by environment type', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.control-panel', { timeout: 5000 });
            
            // Click forested filter
            await page.click('[data-filter="forested"]');
            
            // Check filter is active
            const isActive = await page.$eval('[data-filter="forested"]', el => 
                el.classList.contains('active')
            );
            expect(isActive).to.be.true;
            
            // Markers should be filtered (in real implementation)
            const markers = await page.$$('.leaflet-marker-icon');
            expect(markers.length).to.be.at.least(1);
        });

        it('should filter by altitude', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.control-panel', { timeout: 5000 });
            
            await page.click('[data-filter="high_altitude"]');
            
            const isActive = await page.$eval('[data-filter="high_altitude"]', el => 
                el.classList.contains('active')
            );
            expect(isActive).to.be.true;
        });

        it('should filter by accessibility', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.control-panel', { timeout: 5000 });
            
            await page.click('[data-filter="easy_access"]');
            
            const isActive = await page.$eval('[data-filter="easy_access"]', el => 
                el.classList.contains('active')
            );
            expect(isActive).to.be.true;
        });
    });

    describe('Search Integration', () => {
        it('should search spots with environmental context', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#searchBox', { timeout: 5000 });
            
            await page.type('#searchBox', 'cascade');
            await page.waitForTimeout(500);
            
            // Should find cascade spot
            const markers = await page.$$('.leaflet-marker-icon');
            expect(markers.length).to.be.at.least(1);
        });
    });

    describe('Mobile Responsiveness', () => {
        it('should adapt layer control for mobile', async () => {
            await page.setViewport({ width: 375, height: 667 }); // iPhone size
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.layer-control', { timeout: 5000 });
            
            // Check layer control width
            const width = await page.$eval('.layer-control', el => 
                parseInt(window.getComputedStyle(el).width)
            );
            expect(width).to.equal(260);
        });

        it('should make environment panel full width on mobile', async () => {
            await page.setViewport({ width: 375, height: 667 });
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.environment-panel.visible', { timeout: 5000 });
            
            const styles = await page.$eval('.environment-panel', el => {
                const computed = window.getComputedStyle(el);
                return {
                    left: computed.left,
                    right: computed.right
                };
            });
            
            expect(styles.left).to.equal('10px');
            expect(styles.right).to.equal('10px');
        });
    });

    describe('Performance Tests', () => {
        it('should handle multiple layer toggles efficiently', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.layer-control', { timeout: 5000 });
            
            const startTime = Date.now();
            
            // Toggle all layers rapidly
            for (let i = 0; i < 3; i++) {
                await page.click('[data-layer="forest"]');
                await page.click('[data-layer="elevation_contours"]');
                await page.click('[data-layer="slopes"]');
                await page.click('[data-layer="protected_areas"]');
                await page.click('[data-layer="hiking_trails"]');
                await page.click('[data-layer="hydrography"]');
            }
            
            const endTime = Date.now();
            const duration = endTime - startTime;
            
            // Should complete in reasonable time
            expect(duration).to.be.below(3000);
        });

        it('should cache environment data', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Track API calls
            let envApiCalls = 0;
            page.on('request', (request) => {
                if (request.url().includes('/environment')) {
                    envApiCalls++;
                }
            });
            
            // Click same marker multiple times
            const marker = await page.$('.leaflet-marker-icon');
            await marker.click();
            await page.waitForSelector('.environment-panel.visible', { timeout: 5000 });
            
            // Close by clicking map
            await page.click('#map');
            await page.waitForTimeout(500);
            
            // Click again
            await marker.click();
            await page.waitForSelector('.environment-panel.visible', { timeout: 5000 });
            
            // Should only make one API call due to caching
            expect(envApiCalls).to.equal(1);
        });
    });
});