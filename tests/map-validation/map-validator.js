/**
 * Automated Map Validation Framework
 * Uses Puppeteer to validate map features and performance
 */

import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs/promises';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class MapValidator {
    constructor(options = {}) {
        this.options = {
            headless: options.headless !== false,
            slowMo: options.slowMo || 0,
            devtools: options.devtools || false,
            screenshotDir: options.screenshotDir || join(__dirname, 'screenshots'),
            baseUrl: options.baseUrl || 'http://localhost:8085',
            timeout: options.timeout || 30000,
            ...options
        };
        
        this.browser = null;
        this.page = null;
        this.validationResults = [];
    }

    /**
     * Initialize browser and page
     */
    async init() {
        this.browser = await puppeteer.launch({
            headless: this.options.headless,
            slowMo: this.options.slowMo,
            devtools: this.options.devtools,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        this.page = await this.browser.newPage();
        
        // Set viewport for consistent testing
        await this.page.setViewport({
            width: 1920,
            height: 1080
        });
        
        // Enable console logging
        this.page.on('console', msg => {
            const type = msg.type();
            if (type === 'error') {
                console.error('Browser console error:', msg.text());
            } else if (type === 'warning') {
                console.warn('Browser console warning:', msg.text());
            } else if (type === 'log' && msg.text().includes('Error')) {
                console.log('Browser console log:', msg.text());
            }
        });
        
        // Listen for failed requests
        this.page.on('requestfailed', request => {
            console.log(`❌ Request failed: ${request.url()}`);
            console.log(`   Failure reason: ${request.failure()?.errorText}`);
        });
        
        // Listen for responses to catch 404s
        this.page.on('response', response => {
            if (response.status() === 404) {
                console.log(`❌ 404 Not Found: ${response.url()}`);
            }
        });
        
        // Ensure screenshot directory exists
        await fs.mkdir(this.options.screenshotDir, { recursive: true });
        
        return this;
    }

    /**
     * Navigate to a map page and wait for it to load
     */
    async loadMap(path) {
        const url = `${this.options.baseUrl}${path}`;
        console.log(`Loading map: ${url}`);
        
        // Add error handler
        this.page.on('pageerror', error => {
            console.error('Page JavaScript error:', error.message);
        });
        
        await this.page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: this.options.timeout
        });
        
        // Check if the main map script is trying to load modules
        const hasModuleError = await this.page.evaluate(() => {
            return document.querySelector('script[type="module"][src*="main-map-app.js"]') !== null;
        });
        
        if (hasModuleError) {
            console.log('Page uses ES modules - checking module loading...');
        }
        
        // Wait for map container
        await this.page.waitForSelector('#map', { timeout: 10000 });
        
        // Wait for Leaflet to initialize
        await this.page.waitForFunction(() => {
            return window.L && document.querySelector('.leaflet-container');
        }, { timeout: 10000 });
        
        // Give map time to render tiles
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        return this;
    }

    /**
     * Validate map initialization
     */
    async validateMapInit() {
        const validation = { name: 'Map Initialization', passed: true, errors: [] };
        
        try {
            // Check if map object exists
            const hasMap = await this.page.evaluate(() => {
                return window.L && window.L.map && 
                       document.querySelector('.leaflet-container') !== null;
            });
            
            if (!hasMap) {
                validation.passed = false;
                validation.errors.push('Map not initialized');
            }
            
            // Check map dimensions
            const mapDimensions = await this.page.evaluate(() => {
                const container = document.querySelector('.leaflet-container');
                return {
                    width: container?.offsetWidth || 0,
                    height: container?.offsetHeight || 0
                };
            });
            
            if (mapDimensions.width === 0 || mapDimensions.height === 0) {
                validation.passed = false;
                validation.errors.push('Map has zero dimensions');
            }
            
            // Take screenshot
            await this.screenshot('map-init');
            
        } catch (error) {
            validation.passed = false;
            validation.errors.push(error.message);
        }
        
        this.validationResults.push(validation);
        return validation;
    }

    /**
     * Validate map layers
     */
    async validateLayers() {
        const validation = { name: 'Map Layers', passed: true, errors: [] };
        
        try {
            const layerInfo = await this.page.evaluate(() => {
                // Try different ways to find the map
                let map = window._mainMap || window.map || window._map || window.leafletMap;
                
                // If not found, search in window properties
                if (!map) {
                    map = Object.values(window).find(val => 
                        val && val._container && val._container.classList?.contains('leaflet-container')
                    );
                }
                
                if (!map) return null;
                
                const layers = [];
                map.eachLayer(layer => {
                    layers.push({
                        type: layer.constructor.name,
                        url: layer._url || 'N/A',
                        visible: map.hasLayer(layer)
                    });
                });
                
                return {
                    layerCount: layers.length,
                    layers: layers,
                    bounds: map.getBounds(),
                    zoom: map.getZoom(),
                    center: map.getCenter()
                };
            });
            
            if (!layerInfo) {
                validation.passed = false;
                validation.errors.push('Could not access map object');
            } else if (layerInfo.layerCount === 0) {
                validation.passed = false;
                validation.errors.push('No layers found on map');
            }
            
            console.log(`Found ${layerInfo?.layerCount || 0} layers`);
            
        } catch (error) {
            validation.passed = false;
            validation.errors.push(error.message);
        }
        
        this.validationResults.push(validation);
        return validation;
    }

    /**
     * Validate map controls
     */
    async validateControls() {
        const validation = { name: 'Map Controls', passed: true, errors: [] };
        
        try {
            // Check for zoom control
            const hasZoomControl = await this.page.$('.leaflet-control-zoom') !== null;
            if (!hasZoomControl) {
                validation.errors.push('Zoom control not found');
            }
            
            // Test zoom in
            await this.page.click('.leaflet-control-zoom-in');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Test zoom out
            await this.page.click('.leaflet-control-zoom-out');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check for custom controls
            const customControls = await this.page.evaluate(() => {
                return {
                    sunShadow: document.querySelector('.sun-shadow-controls') !== null,
                    layers: document.querySelector('.leaflet-control-layers') !== null,
                    scale: document.querySelector('.leaflet-control-scale') !== null
                };
            });
            
            console.log('Custom controls found:', customControls);
            
        } catch (error) {
            validation.passed = false;
            validation.errors.push(error.message);
        }
        
        this.validationResults.push(validation);
        return validation;
    }

    /**
     * Validate tile loading performance
     */
    async validateTileLoading() {
        const validation = { name: 'Tile Loading Performance', passed: true, errors: [], metrics: {} };
        
        try {
            // Clear browser cache
            await this.page.evaluate(() => {
                if ('caches' in window) {
                    caches.keys().then(names => {
                        names.forEach(name => caches.delete(name));
                    });
                }
            });
            
            // Start performance measurement
            await this.page.evaluateOnNewDocument(() => {
                window.tileLoadTimes = [];
                window.tileLoadStart = Date.now();
                
                // Intercept tile loading
                const originalCreateElement = document.createElement;
                document.createElement = function(tagName) {
                    const element = originalCreateElement.call(document, tagName);
                    
                    if (tagName === 'img' && element.src && element.src.includes('tile')) {
                        const loadStart = Date.now();
                        element.addEventListener('load', () => {
                            window.tileLoadTimes.push(Date.now() - loadStart);
                        });
                    }
                    
                    return element;
                };
            });
            
            // Reload map
            await this.page.reload({ waitUntil: 'networkidle2' });
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            // Get tile loading metrics
            const metrics = await this.page.evaluate(() => {
                const times = window.tileLoadTimes || [];
                return {
                    tilesLoaded: times.length,
                    avgLoadTime: times.length > 0 ? 
                        times.reduce((a, b) => a + b, 0) / times.length : 0,
                    maxLoadTime: times.length > 0 ? Math.max(...times) : 0,
                    minLoadTime: times.length > 0 ? Math.min(...times) : 0,
                    totalLoadTime: Date.now() - window.tileLoadStart
                };
            });
            
            validation.metrics = metrics;
            
            // Check performance thresholds
            if (metrics.avgLoadTime > 1000) {
                validation.errors.push(`Slow average tile load time: ${metrics.avgLoadTime}ms`);
            }
            
            if (metrics.tilesLoaded === 0) {
                validation.passed = false;
                validation.errors.push('No tiles loaded');
            }
            
            console.log('Tile loading metrics:', metrics);
            
        } catch (error) {
            validation.passed = false;
            validation.errors.push(error.message);
        }
        
        this.validationResults.push(validation);
        return validation;
    }

    /**
     * Validate map interactions
     */
    async validateInteractions() {
        const validation = { name: 'Map Interactions', passed: true, errors: [] };
        
        try {
            // Test pan
            const initialCenter = await this.page.evaluate(() => {
                let map = window._mainMap || window.map || window._map || window.leafletMap;
                if (!map) {
                    map = Object.values(window).find(val => 
                        val && val._container && val._container.classList?.contains('leaflet-container')
                    );
                }
                return map ? map.getCenter() : null;
            });
            
            await this.page.mouse.move(960, 540);
            await this.page.mouse.down();
            await this.page.mouse.move(860, 540);
            await this.page.mouse.up();
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const afterPanCenter = await this.page.evaluate(() => {
                let map = window._mainMap || window.map || window._map || window.leafletMap;
                if (!map) {
                    map = Object.values(window).find(val => 
                        val && val._container && val._container.classList?.contains('leaflet-container')
                    );
                }
                return map ? map.getCenter() : null;
            });
            
            if (initialCenter && afterPanCenter && 
                initialCenter.lat === afterPanCenter.lat && 
                initialCenter.lng === afterPanCenter.lng) {
                validation.errors.push('Map pan not working');
            }
            
            // Test click
            await this.page.click('#map', { position: { x: 500, y: 400 } });
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check for popups or click handlers
            const hasPopup = await this.page.$('.leaflet-popup') !== null;
            console.log('Popup after click:', hasPopup);
            
        } catch (error) {
            validation.passed = false;
            validation.errors.push(error.message);
        }
        
        this.validationResults.push(validation);
        return validation;
    }

    /**
     * Validate custom map features (like sun/shadow calculator)
     */
    async validateCustomFeatures() {
        const validation = { name: 'Custom Features', passed: true, errors: [], features: {} };
        
        try {
            // Check for sun/shadow calculator
            const hasSunControl = await this.page.$('.sun-shadow-controls, .sun-shadow-enhanced-controls') !== null;
            validation.features.sunShadowCalculator = hasSunControl;
            
            if (hasSunControl) {
                // Test sun control interaction
                const sunButton = await this.page.$('a[title*="Soleil"], button:has-text("Soleil")');
                if (sunButton) {
                    await sunButton.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    await this.screenshot('sun-shadow-active');
                }
            }
            
            // Check for elevation display
            const hasElevation = await this.page.evaluate(() => {
                return document.body.textContent.includes('Élévation') || 
                       document.body.textContent.includes('elevation');
            });
            validation.features.elevationDisplay = hasElevation;
            
            // Check for weather integration
            const hasWeather = await this.page.$('.weather-widget, .meteo') !== null;
            validation.features.weatherIntegration = hasWeather;
            
            console.log('Custom features found:', validation.features);
            
        } catch (error) {
            validation.passed = false;
            validation.errors.push(error.message);
        }
        
        this.validationResults.push(validation);
        return validation;
    }

    /**
     * Perform visual regression testing
     */
    async validateVisualRegression(referenceName) {
        const validation = { name: 'Visual Regression', passed: true, errors: [] };
        
        try {
            const screenshotPath = join(this.options.screenshotDir, `${referenceName}.png`);
            const referencePath = join(this.options.screenshotDir, 'reference', `${referenceName}.png`);
            
            // Take screenshot
            await this.page.screenshot({ path: screenshotPath, fullPage: true });
            
            // Check if reference exists
            try {
                await fs.access(referencePath);
                // TODO: Implement actual image comparison
                console.log('Reference image exists, visual comparison needed');
            } catch {
                // Create reference if it doesn't exist
                await fs.mkdir(dirname(referencePath), { recursive: true });
                await fs.copyFile(screenshotPath, referencePath);
                console.log('Created reference image');
            }
            
        } catch (error) {
            validation.passed = false;
            validation.errors.push(error.message);
        }
        
        this.validationResults.push(validation);
        return validation;
    }

    /**
     * Take a screenshot with timestamp
     */
    async screenshot(name) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `${name}_${timestamp}.png`;
        const filepath = join(this.options.screenshotDir, filename);
        
        await this.page.screenshot({ path: filepath, fullPage: true });
        console.log(`Screenshot saved: ${filename}`);
        
        return filepath;
    }

    /**
     * Run all validations
     */
    async runAllValidations(mapPath) {
        console.log('\n🔍 Starting Map Validation...\n');
        
        await this.loadMap(mapPath);
        
        await this.validateMapInit();
        await this.validateLayers();
        await this.validateControls();
        await this.validateTileLoading();
        await this.validateInteractions();
        await this.validateCustomFeatures();
        await this.validateVisualRegression('map-full');
        
        return this.generateReport();
    }

    /**
     * Generate validation report
     */
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: this.validationResults.length,
                passed: this.validationResults.filter(v => v.passed).length,
                failed: this.validationResults.filter(v => !v.passed).length
            },
            validations: this.validationResults
        };
        
        console.log('\n📊 Validation Report:\n');
        console.log(`Total Tests: ${report.summary.total}`);
        console.log(`Passed: ${report.summary.passed} ✅`);
        console.log(`Failed: ${report.summary.failed} ❌\n`);
        
        this.validationResults.forEach(validation => {
            const status = validation.passed ? '✅' : '❌';
            console.log(`${status} ${validation.name}`);
            
            if (validation.errors.length > 0) {
                validation.errors.forEach(error => {
                    console.log(`   ⚠️  ${error}`);
                });
            }
            
            if (validation.metrics) {
                console.log(`   📊 Metrics:`, validation.metrics);
            }
            
            if (validation.features) {
                console.log(`   🔧 Features:`, validation.features);
            }
        });
        
        return report;
    }

    /**
     * Close browser
     */
    async close() {
        if (this.browser) {
            await this.browser.close();
        }
    }
}

// Export for use
export default MapValidator;