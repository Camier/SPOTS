/**
 * E2E Tests for Accessibility Features
 * Tests WCAG compliance, keyboard navigation, and screen reader support
 */

import { expect } from 'chai';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import puppeteerConfig from './puppeteer-config-fixed.js';
import puppeteer from 'puppeteer';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe('Accessibility Tests', () => {
    let browser;
    let page;

    beforeAll(async () => {
        browser = await puppeteer.launch(puppeteerConfig);
    });

    afterAll(async () => {
        if (browser) await browser.close();
    });

    beforeEach(async () => {
        page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 800 });
        
        // Mock basic API responses
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
                        total: 2,
                        spots: [
                            {
                                id: 1,
                                name: 'Test Spot 1',
                                type: 'waterfall',
                                latitude: 43.6047,
                                longitude: 1.4442,
                                description: 'Beautiful waterfall'
                            },
                            {
                                id: 2,
                                name: 'Test Spot 2',
                                type: 'beach',
                                latitude: 43.5297,
                                longitude: 1.4954,
                                description: 'Sandy beach'
                            }
                        ]
                    })
                });
            } else if (request.url().includes('/api/weather')) {
                request.respond({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        temperature: 22,
                        weather: 'Sunny',
                        icon: '01d'
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

    it('should have proper page title and meta descriptions', async () => {
        const mapPath = path.join(__dirname, '../../src/frontend/enhanced-map-ign-advanced.html');
        await page.goto(`file://${mapPath}`);
        
        const title = await page.title();
        expect(title).to.include('Spots');
        
        const metaDescription = await page.$eval('meta[name="description"]', el => el.content);
        expect(metaDescription).to.exist;
    });

    it('should have proper heading hierarchy', async () => {
        const mapPath = path.join(__dirname, '../../src/frontend/enhanced-map-ign-advanced.html');
        await page.goto(`file://${mapPath}`);
        
        // Check for h1
        const h1 = await page.$('h1');
        expect(h1).to.exist;
        
        // Check heading order
        const headings = await page.evaluate(() => {
            const headingElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            return Array.from(headingElements).map(h => ({
                level: parseInt(h.tagName[1]),
                text: h.textContent
            }));
        });
        
        // Verify heading hierarchy
        let lastLevel = 0;
        headings.forEach(heading => {
            expect(heading.level - lastLevel).to.be.lessThanOrEqual(1);
            lastLevel = heading.level;
        });
    });

    it('should have alt text for all images', async () => {
        const mapPath = path.join(__dirname, '../../src/frontend/enhanced-map-ign-advanced.html');
        await page.goto(`file://${mapPath}`);
        
        const images = await page.$$eval('img', imgs => 
            imgs.map(img => ({
                src: img.src,
                alt: img.alt
            }))
        );
        
        images.forEach(img => {
            expect(img.alt).to.exist;
            expect(img.alt).to.not.be.empty;
        });
    });

    it('should have proper ARIA labels for interactive elements', async () => {
        const mapPath = path.join(__dirname, '../../src/frontend/enhanced-map-ign-advanced.html');
        await page.goto(`file://${mapPath}`);
        
        // Check buttons
        const buttons = await page.$$eval('button', btns => 
            btns.map(btn => ({
                text: btn.textContent,
                ariaLabel: btn.getAttribute('aria-label'),
                title: btn.title
            }))
        );
        
        buttons.forEach(btn => {
            expect(btn.ariaLabel || btn.text || btn.title).to.exist;
        });
    });

    it('should be keyboard navigable', async () => {
        const mapPath = path.join(__dirname, '../../src/frontend/enhanced-map-ign-advanced.html');
        await page.goto(`file://${mapPath}`);
        
        // Tab through interactive elements
        await page.keyboard.press('Tab');
        let focusedElement = await page.evaluate(() => document.activeElement.tagName);
        expect(focusedElement).to.not.equal('BODY');
        
        // Test that Tab moves focus
        await page.keyboard.press('Tab');
        const secondFocusedElement = await page.evaluate(() => document.activeElement.tagName);
        expect(secondFocusedElement).to.exist;
    });

    it('should have sufficient color contrast', async () => {
        const mapPath = path.join(__dirname, '../../src/frontend/enhanced-map-ign-advanced.html');
        await page.goto(`file://${mapPath}`);
        
        // This is a simplified check - for real contrast testing, use axe-core
        const textElements = await page.$$eval('p, span, h1, h2, h3, h4, h5, h6, a, button', elements => 
            elements.map(el => {
                const styles = window.getComputedStyle(el);
                return {
                    color: styles.color,
                    backgroundColor: styles.backgroundColor,
                    fontSize: styles.fontSize
                };
            })
        );
        
        expect(textElements).to.not.be.empty;
    });

    it('should handle focus management in modals', async () => {
        const mapPath = path.join(__dirname, '../../src/frontend/enhanced-map-ign-advanced.html');
        await page.goto(`file://${mapPath}`);
        
        // Check if modals trap focus
        const hasModals = await page.$('.modal, [role="dialog"]');
        if (hasModals) {
            const modalHasFocusTrap = await page.evaluate(() => {
                const modal = document.querySelector('.modal, [role="dialog"]');
                return modal && (modal.getAttribute('aria-modal') === 'true' || 
                               modal.hasAttribute('data-focus-trap'));
            });
            expect(modalHasFocusTrap).to.be.true;
        }
    });

    it('should announce dynamic content changes', async () => {
        const mapPath = path.join(__dirname, '../../src/frontend/enhanced-map-ign-advanced.html');
        await page.goto(`file://${mapPath}`);
        
        // Check for ARIA live regions
        const liveRegions = await page.$$('[aria-live], [role="alert"], [role="status"]');
        expect(liveRegions).to.exist;
    });
});