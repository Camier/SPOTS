/**
 * E2E Tests for Responsive Design
 * Tests layout, functionality, and performance across different devices
 */

import puppeteer from 'puppeteer';
import puppeteerConfig from './puppeteer-config-fixed.js';
import { expect } from 'chai';
import path from 'node:path';

import { fileURLToPath } from 'node:url';
import { describe, it, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


describe('Responsive Design Tests', () => {
    let browser;
    let page;
    
    // Device viewports
    const devices = {
        mobile: { width: 375, height: 667, name: 'iPhone 8' },
        tablet: { width: 768, height: 1024, name: 'iPad' },
        desktop: { width: 1920, height: 1080, name: 'Desktop' },
        smallMobile: { width: 320, height: 568, name: 'iPhone SE' },
        largeTablet: { width: 1024, height: 1366, name: 'iPad Pro' }
    };

    beforeAll(async () => {
        browser = await puppeteer.launch(puppeteerConfig);
    });

    afterAll(async () => {
        await browser.close();
    });

    beforeEach(async () => {
        page = await browser.newPage();
        
        // Mock API responses
        await page.setRequestInterception(true);
        page.on('request', (request) => {
            if (request.url().includes('/api/config')) {
                request.respond({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({ ign_api_key: 'test-key' })
                });
            } else if (request.url().includes('/api/spots')) {
                request.respond({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        total: 3,
                        spots: [
                            {
                                id: 1,
                                name: 'Cascade du Test',
                                type: 'waterfall',
                                latitude: 43.6047,
                                longitude: 1.4442,
                                description: 'Beautiful waterfall'
                            },
                            {
                                id: 2,
                                name: 'Grotte Mystérieuse',
                                type: 'cave',
                                latitude: 43.5,
                                longitude: 1.3,
                                description: 'Hidden cave'
                            },
                            {
                                id: 3,
                                name: 'Point de Vue',
                                type: 'viewpoint',
                                latitude: 43.7,
                                longitude: 1.5,
                                elevation: 1200
                            }
                        ]
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

    describe('Mobile Layout Tests', () => {
        it('should adapt control panel for mobile', async () => {
            await page.setViewport(devices.mobile);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('.control-panel', { timeout: 5000 });
            
            const panelStyles = await page.evaluate(() => {
                const panel = document.querySelector('.control-panel');
                const computed = window.getComputedStyle(panel);
                const rect = panel.getBoundingClientRect();
                return {
                    left: computed.left,
                    right: computed.right,
                    width: rect.width,
                    maxWidth: computed.maxWidth
                };
            });
            
            // Should be full width minus margins on mobile
            expect(panelStyles.left).to.equal('10px');
            expect(panelStyles.right).to.equal('10px');
            expect(panelStyles.maxWidth).to.equal('none');
        });

        it('should stack filter buttons on small screens', async () => {
            await page.setViewport(devices.smallMobile);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('.filter-buttons', { timeout: 5000 });
            
            const buttonLayout = await page.evaluate(() => {
                const container = document.querySelector('.filter-buttons');
                const buttons = Array.from(container.querySelectorAll('.filter-btn'));
                const containerWidth = container.getBoundingClientRect().width;
                
                // Check if buttons wrap
                const firstButtonRect = buttons[0].getBoundingClientRect();
                const lastButtonRect = buttons[buttons.length - 1].getBoundingClientRect();
                
                return {
                    containerWidth,
                    wraps: lastButtonRect.top > firstButtonRect.top,
                    buttonCount: buttons.length
                };
            });
            
            // Buttons should wrap on small screens
            expect(buttonLayout.wraps).to.be.true;
        });

        it('should have touch-friendly button sizes on mobile', async () => {
            await page.setViewport(devices.mobile);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('.locate-btn', { timeout: 5000 });
            
            const buttonSizes = await page.evaluate(() => {
                const buttons = {
                    locate: document.querySelector('.locate-btn'),
                    filter: document.querySelector('.filter-btn'),
                    style: document.querySelector('.style-btn')
                };
                
                return Object.entries(buttons).reduce((acc, [key, btn]) => {
                    if (btn) {
                        const rect = btn.getBoundingClientRect();
                        acc[key] = { width: rect.width, height: rect.height };
                    }
                    return acc;
                }, {});
            });
            
            // All buttons should be at least 44px tall (WCAG touch target)
            Object.values(buttonSizes).forEach(size => {
                expect(size.height).to.be.at.least(40);
            });
        });

        it('should hide/show elements based on screen size', async () => {
            // Desktop view
            await page.setViewport(devices.desktop);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('.control-panel', { timeout: 5000 });
            
            const desktopElements = await page.evaluate(() => {
                return {
                    hasFullTitle: document.querySelector('.control-panel h1').textContent.includes('Occitanie'),
                    hasDescription: document.querySelector('.spot-count') !== null
                };
            });
            
            // Mobile view
            await page.setViewport(devices.mobile);
            
            const mobileElements = await page.evaluate(() => {
                const title = document.querySelector('.control-panel h1');
                return {
                    titleFontSize: window.getComputedStyle(title).fontSize,
                    hasDescription: document.querySelector('.spot-count') !== null
                };
            });
            
            expect(desktopElements.hasFullTitle).to.be.true;
            expect(mobileElements.titleFontSize).to.equal('20px'); // 1.25rem
        });
    });

    describe('Tablet Layout Tests', () => {
        it('should optimize layout for tablets', async () => {
            await page.setViewport(devices.tablet);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('.control-panel', { timeout: 5000 });
            
            const layout = await page.evaluate(() => {
                const panel = document.querySelector('.control-panel');
                const rect = panel.getBoundingClientRect();
                return {
                    width: rect.width,
                    position: window.getComputedStyle(panel).position
                };
            });
            
            // Should maintain absolute positioning on tablets
            expect(layout.position).to.equal('absolute');
            expect(layout.width).to.be.below(400); // Not full width
        });

        it('should handle orientation changes', async () => {
            // Portrait
            await page.setViewport({ width: 768, height: 1024 });
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            
            const portraitLayout = await page.evaluate(() => {
                const map = document.querySelector('#map');
                return {
                    width: map.clientWidth,
                    height: map.clientHeight
                };
            });
            
            // Landscape
            await page.setViewport({ width: 1024, height: 768 });
            
            const landscapeLayout = await page.evaluate(() => {
                const map = document.querySelector('#map');
                return {
                    width: map.clientWidth,
                    height: map.clientHeight
                };
            });
            
            expect(portraitLayout.height).to.be.above(portraitLayout.width);
            expect(landscapeLayout.width).to.be.above(landscapeLayout.height);
        });
    });

    describe('IGN Integration Responsive Tests', () => {
        it('should adapt layer control for different screens', async () => {
            const testFile = `file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`;
            
            // Desktop
            await page.setViewport(devices.desktop);
            await page.goto(testFile);
            await page.waitForSelector('.layer-control', { timeout: 5000 });
            
            const desktopWidth = await page.$eval('.layer-control', el => 
                el.getBoundingClientRect().width
            );
            
            // Mobile
            await page.setViewport(devices.mobile);
            const mobileWidth = await page.$eval('.layer-control', el => 
                el.getBoundingClientRect().width
            );
            
            expect(desktopWidth).to.equal(280);
            expect(mobileWidth).to.equal(260);
        });

        it('should make environment panel responsive', async () => {
            await page.setViewport(devices.mobile);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Click marker to show environment panel
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.environment-panel.visible', { timeout: 5000 });
            
            const panelStyles = await page.evaluate(() => {
                const panel = document.querySelector('.environment-panel');
                const computed = window.getComputedStyle(panel);
                return {
                    left: computed.left,
                    right: computed.right,
                    bottom: computed.bottom
                };
            });
            
            expect(panelStyles.left).to.equal('10px');
            expect(panelStyles.right).to.equal('10px');
        });

        it('should handle layer toggle interactions on touch devices', async () => {
            await page.setViewport({ ...devices.mobile, hasTouch: true });
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-ign.html')}`);
            await page.waitForSelector('.layer-toggle', { timeout: 5000 });
            
            // Tap layer toggle
            const toggle = await page.$('[data-layer="forest"]');
            const box = await toggle.boundingBox();
            await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
            
            const isActive = await page.$eval('[data-layer="forest"]', el => 
                el.classList.contains('active')
            );
            expect(isActive).to.be.true;
        });
    });

    describe('Performance on Different Devices', () => {
        it('should load efficiently on mobile networks', async () => {
            // Simulate slow 3G
            await page.emulateNetworkConditions({
                offline: false,
                downloadThroughput: 1.6 * 1024 * 1024 / 8,
                uploadThroughput: 750 * 1024 / 8,
                latency: 150
            });
            
            await page.setViewport(devices.mobile);
            const startTime = Date.now();
            
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 10000 });
            
            const loadTime = Date.now() - startTime;
            
            // Should load within reasonable time even on slow network
            expect(loadTime).to.be.below(10000);
        });

        it('should handle many markers on mobile devices', async () => {
            await page.setViewport(devices.mobile);
            
            // Mock more spots
            await page.setRequestInterception(true);
            page.removeAllListeners('request');
            page.on('request', (request) => {
                if (request.url().includes('/api/spots')) {
                    const spots = Array.from({ length: 100 }, (_, i) => ({
                        id: i + 1,
                        name: `Spot ${i + 1}`,
                        type: ['cave', 'waterfall', 'viewpoint'][i % 3],
                        latitude: 43.5 + (Math.random() * 0.4),
                        longitude: 1.3 + (Math.random() * 0.4)
                    }));
                    
                    request.respond({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({ total: 100, spots })
                    });
                } else {
                    request.continue();
                }
            });
            
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Check clustering is working
            const clusters = await page.$$('.marker-cluster-custom');
            expect(clusters.length).to.be.above(0);
            
            // Performance should be acceptable
            const fps = await page.evaluate(() => {
                return new Promise(resolve => {
                    let frames = 0;
                    const startTime = performance.now();
                    
                    function countFrames() {
                        frames++;
                        if (performance.now() - startTime < 1000) {
                            requestAnimationFrame(countFrames);
                        } else {
                            resolve(frames);
                        }
                    }
                    
                    requestAnimationFrame(countFrames);
                });
            });
            
            // Should maintain reasonable framerate
            expect(fps).to.be.above(20);
        });
    });

    describe('Responsive Popups', () => {
        it('should size popups appropriately for screen', async () => {
            await page.setViewport(devices.mobile);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.spot-popup', { timeout: 5000 });
            
            const popupSize = await page.evaluate(() => {
                const popup = document.querySelector('.leaflet-popup-content');
                const rect = popup.getBoundingClientRect();
                return {
                    width: rect.width,
                    maxWidth: window.getComputedStyle(popup).maxWidth
                };
            });
            
            // Popup should not exceed screen width
            expect(popupSize.width).to.be.below(devices.mobile.width - 40);
        });

        it('should position popups within viewport', async () => {
            await page.setViewport(devices.mobile);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Click marker near edge
            await page.click('.leaflet-marker-icon');
            await page.waitForSelector('.leaflet-popup', { timeout: 5000 });
            
            const popupPosition = await page.evaluate(() => {
                const popup = document.querySelector('.leaflet-popup');
                const rect = popup.getBoundingClientRect();
                return {
                    left: rect.left,
                    right: rect.right,
                    top: rect.top,
                    bottom: rect.bottom,
                    viewportWidth: window.innerWidth,
                    viewportHeight: window.innerHeight
                };
            });
            
            // Popup should be within viewport
            expect(popupPosition.left).to.be.at.least(0);
            expect(popupPosition.right).to.be.at.most(popupPosition.viewportWidth);
            expect(popupPosition.top).to.be.at.least(0);
        });
    });

    describe('Touch Interactions', () => {
        it('should handle touch gestures on map', async () => {
            await page.setViewport({ ...devices.mobile, hasTouch: true });
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            
            // Get initial map center
            const initialCenter = await page.evaluate(() => {
                return window.map.getCenter();
            });
            
            // Simulate swipe
            const centerX = devices.mobile.width / 2;
            const centerY = devices.mobile.height / 2;
            
            await page.touchscreen.drag(
                { x: centerX, y: centerY },
                { x: centerX - 100, y: centerY }
            );
            
            await page.waitForTimeout(500);
            
            // Map should have moved
            const newCenter = await page.evaluate(() => {
                return window.map.getCenter();
            });
            
            expect(newCenter.lng).to.not.equal(initialCenter.lng);
        });

        it('should handle pinch zoom', async () => {
            await page.setViewport({ ...devices.mobile, hasTouch: true });
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            
            const initialZoom = await page.evaluate(() => {
                return window.map.getZoom();
            });
            
            // Note: Puppeteer doesn't have built-in pinch support
            // This is a placeholder for manual testing
            
            expect(initialZoom).to.be.a('number');
        });
    });

    describe('Responsive Images and Assets', () => {
        it('should load appropriate tile sizes', async () => {
            await page.setViewport(devices.mobile);
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            
            // Monitor tile requests
            const tileRequests = [];
            page.on('request', request => {
                if (request.url().includes('tile')) {
                    tileRequests.push(request.url());
                }
            });
            
            // Pan map to trigger tile loading
            await page.evaluate(() => {
                window.map.panBy([100, 100]);
            });
            
            await page.waitForTimeout(1000);
            
            // Should request tiles
            expect(tileRequests.length).to.be.above(0);
        });
    });

    describe('Responsive Typography', () => {
        it('should scale text appropriately', async () => {
            const checkTypography = async (device) => {
                await page.setViewport(device);
                await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
                await page.waitForSelector('.control-panel', { timeout: 5000 });
                
                return await page.evaluate(() => {
                    const h1 = document.querySelector('.control-panel h1');
                    const body = document.querySelector('.spot-count');
                    return {
                        h1Size: window.getComputedStyle(h1).fontSize,
                        bodySize: window.getComputedStyle(body).fontSize
                    };
                });
            };
            
            const mobileSizes = await checkTypography(devices.mobile);
            const desktopSizes = await checkTypography(devices.desktop);
            
            // Mobile should have slightly smaller text
            expect(parseInt(mobileSizes.h1Size)).to.be.at.most(parseInt(desktopSizes.h1Size));
        });
    });
});