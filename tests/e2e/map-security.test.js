/**
 * E2E Tests for Enhanced Map Security
 * Tests XSS prevention and security measures
 */

import puppeteer from 'puppeteer';
import puppeteerConfig from './puppeteer-config-fixed.js';
import { expect } from 'chai';
import path from 'node:path';

import { fileURLToPath } from 'node:url';
import { describe, it, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


describe('Enhanced Map Security Tests', () => {
    let browser;
    let page;
    const baseUrl = 'http://localhost:8085'; // Adjust to your test server

    beforeAll(async () => {
        browser = await puppeteer.launch(puppeteerConfig);
    });

    afterAll(async () => {
        await browser.close();
    });

    beforeEach(async () => {
        page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 800 });
        
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
                                name: 'Test Spot <script>alert("XSS")</script>',
                                description: 'Description with <img src=x onerror=alert("XSS")>',
                                type: 'cave',
                                latitude: 43.6047,
                                longitude: 1.4442,
                                elevation: 450
                            },
                            {
                                id: 2,
                                name: 'Safe Spot',
                                description: 'Normal description',
                                type: 'waterfall',
                                latitude: 43.7,
                                longitude: 1.5
                            },
                            {
                                id: 3,
                                name: null,
                                description: undefined,
                                type: '<script>alert("type-xss")</script>',
                                latitude: 'invalid',
                                longitude: 999
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

    describe('XSS Prevention Tests', () => {
        it('should prevent XSS in spot names', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            
            // Wait for markers to load
            await page.waitForTimeout(2000);
            
            // Check that no alerts were triggered
            const alerts = [];
            page.on('dialog', async dialog => {
                alerts.push(dialog.message());
                await dialog.dismiss();
            });
            
            // Click on first marker to open popup
            const marker = await page.$('.leaflet-marker-icon');
            await marker.click();
            await page.waitForSelector('.spot-popup', { timeout: 5000 });
            
            // Get popup content
            const popupContent = await page.$eval('.spot-popup', el => el.innerHTML);
            
            // Verify script tags are escaped
            expect(popupContent).to.not.include('<script>');
            expect(popupContent).to.include('&lt;script&gt;');
            expect(alerts).to.have.lengthOf(0);
        });

        it('should prevent XSS in spot descriptions', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Click on first marker
            const marker = await page.$('.leaflet-marker-icon');
            await marker.click();
            await page.waitForSelector('.spot-description', { timeout: 5000 });
            
            // Check description content
            const descContent = await page.$eval('.spot-description', el => el.textContent);
            expect(descContent).to.include('Description with <img src=x onerror=alert("XSS")>');
            expect(descContent).to.not.include('onerror=');
        });

        it('should sanitize spot type badges', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Find and click the third marker (with malicious type)
            const markers = await page.$$('.leaflet-marker-icon');
            if (markers.length >= 3) {
                await markers[2].click();
                await page.waitForSelector('.spot-type-badge', { timeout: 5000 });
                
                const badgeContent = await page.$eval('.spot-type-badge', el => el.textContent);
                expect(badgeContent).to.include('&lt;script&gt;');
            }
        });
    });

    describe('Input Validation Tests', () => {
        it('should validate coordinates', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            
            // Check that invalid coordinates are filtered out
            const markerCount = await page.$$eval('.leaflet-marker-icon', markers => markers.length);
            expect(markerCount).to.equal(2); // Only 2 valid spots out of 3
        });

        it('should handle null and undefined values gracefully', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // The third spot has null name and undefined description
            const markers = await page.$$('.leaflet-marker-icon');
            expect(markers.length).to.be.at.least(2);
            
            // Click on a valid marker and check it renders properly
            await markers[1].click();
            await page.waitForSelector('.spot-popup', { timeout: 5000 });
            
            const hasError = await page.evaluate(() => {
                return window.errorOccurred || false;
            });
            expect(hasError).to.be.false;
        });
    });

    describe('CSP Header Tests', () => {
        it('should have Content Security Policy meta tag', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            
            const cspMeta = await page.$eval('meta[http-equiv="Content-Security-Policy"]', el => el.content);
            expect(cspMeta).to.include("default-src 'self'");
            expect(cspMeta).to.include("script-src 'self' 'unsafe-inline'");
            expect(cspMeta).to.include("connect-src 'self' http://localhost:8000");
        });
    });

    describe('DOM Manipulation Security', () => {
        it('should use safe DOM methods instead of innerHTML for dynamic content', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            
            // Inject a test to verify createElement is used
            const usesSafeMethods = await page.evaluate(() => {
                // Check if SecurityUtils exists and has escapeHtml
                return window.SecurityUtils && 
                       typeof window.SecurityUtils.escapeHtml === 'function' &&
                       typeof window.SecurityUtils.sanitizeSpot === 'function';
            });
            
            expect(usesSafeMethods).to.be.true;
        });

        it('should escape HTML in search functionality', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#searchBox', { timeout: 5000 });
            
            // Type malicious content in search
            await page.type('#searchBox', '<script>alert("search-xss")</script>');
            await page.waitForTimeout(500);
            
            // Check no alert was triggered
            const alerts = [];
            page.on('dialog', async dialog => {
                alerts.push(dialog.message());
                await dialog.dismiss();
            });
            
            expect(alerts).to.have.lengthOf(0);
        });
    });

    describe('LocalStorage Security', () => {
        it('should safely handle localStorage for favorites', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            
            // Set malicious localStorage data
            await page.evaluate(() => {
                localStorage.setItem('favoriteSpots', '["<script>alert(1)</script>", "invalid", 1, 2]');
            });
            
            // Reload page
            await page.reload();
            await page.waitForSelector('#map', { timeout: 5000 });
            
            // Check that only valid numeric IDs are loaded
            const favorites = await page.evaluate(() => {
                return JSON.parse(localStorage.getItem('favoriteSpots') || '[]');
            });
            
            expect(favorites).to.deep.equal([1, 2]);
        });
    });

    describe('Navigation Security', () => {
        it('should validate coordinates before navigation', async () => {
            await page.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await page.waitForSelector('#map', { timeout: 5000 });
            await page.waitForTimeout(2000);
            
            // Override window.open to track calls
            await page.evaluateOnNewDocument(() => {
                window.openCalls = [];
                window.open = (url) => {
                    window.openCalls.push(url);
                };
            });
            
            // Click on marker and navigate button
            const marker = await page.$('.leaflet-marker-icon');
            await marker.click();
            await page.waitForSelector('[data-action="navigate"]', { timeout: 5000 });
            
            await page.click('[data-action="navigate"]');
            
            const openCalls = await page.evaluate(() => window.openCalls);
            
            // Should have valid coordinates in URL
            expect(openCalls).to.have.lengthOf(1);
            expect(openCalls[0]).to.match(/destination=43\.\d+,1\.\d+/);
        });
    });

    describe('Error Handling', () => {
        it('should handle API errors gracefully', async () => {
            const errorPage = await browser.newPage();
            await errorPage.setRequestInterception(true);
            
            errorPage.on('request', (request) => {
                if (request.url().includes('/api/spots')) {
                    request.respond({
                        status: 500,
                        contentType: 'application/json',
                        body: JSON.stringify({ error: 'Server error' })
                    });
                } else {
                    request.continue();
                }
            });
            
            await errorPage.goto(`file://${path.resolve(__dirname, '../../src/frontend/enhanced-map-secure.html')}`);
            await errorPage.waitForSelector('#map', { timeout: 5000 });
            
            // Check that map still loads despite API error
            const mapExists = await errorPage.$('#map');
            expect(mapExists).to.not.be.null;
            
            await errorPage.close();
        });
    });
});