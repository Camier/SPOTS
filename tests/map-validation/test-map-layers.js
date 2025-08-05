/**
 * Comprehensive Map Layers Testing
 * Tests all layer switching functionality and tile loading
 */

import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs/promises';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class MapLayersTester {
    constructor(options = {}) {
        this.options = {
            headless: false,
            slowMo: 100,
            devtools: false,
            screenshotDir: join(__dirname, 'screenshots/layers'),
            baseUrl: options.baseUrl || 'http://localhost:8085',
            timeout: 30000,
            ...options
        };
        
        this.browser = null;
        this.page = null;
        this.testResults = [];
        this.layerUrls = new Map();
    }

    async init() {
        this.browser = await puppeteer.launch({
            headless: this.options.headless,
            slowMo: this.options.slowMo,
            devtools: this.options.devtools,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        this.page = await this.browser.newPage();
        await this.page.setViewport({ width: 1920, height: 1080 });
        
        // Track network requests for tiles
        this.page.on('request', request => {
            const url = request.url();
            if (url.includes('tile') || url.includes('wmts') || url.includes('openstreetmap')) {
                const currentLayer = this.currentTestLayer || 'unknown';
                if (!this.layerUrls.has(currentLayer)) {
                    this.layerUrls.set(currentLayer, new Set());
                }
                this.layerUrls.get(currentLayer).add(new URL(url).hostname);
            }
        });
        
        // Log tile loading errors
        this.page.on('response', response => {
            const url = response.url();
            if ((url.includes('tile') || url.includes('wmts')) && response.status() >= 400) {
                console.log(`  ⚠️ Tile error ${response.status()}: ${url}`);
            }
        });
        
        await fs.mkdir(this.options.screenshotDir, { recursive: true });
        
        // Load the main map
        const url = `${this.options.baseUrl}/main-map.html`;
        console.log(`Loading main map: ${url}`);
        await this.page.goto(url, { waitUntil: 'networkidle2' });
        
        // Wait for map initialization
        await this.page.waitForSelector('#map');
        await this.page.waitForFunction(() => window.L && document.querySelector('.leaflet-container'));
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        return this;
    }

    async screenshot(name) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `${name}_${timestamp}.png`;
        const filepath = join(this.options.screenshotDir, filename);
        await this.page.screenshot({ path: filepath, fullPage: false });
        console.log(`  📸 Screenshot: ${filename}`);
        return filepath;
    }

    // Test initial map state and default layer
    async testDefaultLayer() {
        console.log('\n🗺️ Testing Default Layer (IGN)...');
        const result = { name: 'Default Layer', passed: true, errors: [], details: {} };
        
        try {
            // Check initial map state
            const mapInfo = await this.page.evaluate(() => {
                const map = window._mainMap;
                if (!map) return null;
                
                let tileLayer = null;
                let tileUrl = null;
                
                map.eachLayer(layer => {
                    if (layer._url && layer._url.includes('http')) {
                        tileLayer = layer;
                        tileUrl = layer._url;
                    }
                });
                
                return {
                    center: map.getCenter(),
                    zoom: map.getZoom(),
                    bounds: map.getBounds(),
                    hasTileLayer: !!tileLayer,
                    tileUrl: tileUrl
                };
            });
            
            if (!mapInfo) {
                result.passed = false;
                result.errors.push('Could not access map object');
            } else {
                result.details = mapInfo;
                console.log('  Map initialized with:');
                console.log(`    Center: ${mapInfo.center.lat.toFixed(4)}, ${mapInfo.center.lng.toFixed(4)}`);
                console.log(`    Zoom: ${mapInfo.zoom}`);
                console.log(`    Tile Layer: ${mapInfo.hasTileLayer ? 'Yes' : 'No'}`);
                
                if (mapInfo.tileUrl) {
                    console.log(`    Tile URL pattern: ${mapInfo.tileUrl.substring(0, 50)}...`);
                    
                    // Verify it's IGN
                    if (mapInfo.tileUrl.includes('geopf.fr')) {
                        console.log('    ✅ IGN layer confirmed');
                    } else {
                        result.errors.push('Default layer is not IGN');
                    }
                }
            }
            
            await this.screenshot('default-layer-ign');
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test layer panel functionality
    async testLayerPanel() {
        console.log('\n🎚️ Testing Layer Panel...');
        const result = { name: 'Layer Panel', passed: true, errors: [], details: {} };
        
        try {
            // Click layers button
            await this.page.click('#layersBtn');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if panel opened
            const panelInfo = await this.page.evaluate(() => {
                const panel = document.querySelector('#layersPanel');
                if (!panel) return null;
                
                const layerButtons = Array.from(panel.querySelectorAll('.layer-btn'));
                
                return {
                    isVisible: panel.classList.contains('active'),
                    panelHeight: panel.offsetHeight,
                    layerButtons: layerButtons.map(btn => ({
                        text: btn.textContent.trim(),
                        isActive: btn.classList.contains('active'),
                        dataLayer: btn.dataset.layer
                    }))
                };
            });
            
            if (!panelInfo || !panelInfo.isVisible) {
                result.passed = false;
                result.errors.push('Layer panel did not open');
            } else {
                result.details = panelInfo;
                console.log(`  Layer panel opened (height: ${panelInfo.panelHeight}px)`);
                console.log(`  Found ${panelInfo.layerButtons.length} layer buttons:`);
                
                panelInfo.layerButtons.forEach(btn => {
                    console.log(`    - ${btn.text} ${btn.isActive ? '(active)' : ''}`);
                });
                
                if (panelInfo.layerButtons.length === 0) {
                    result.errors.push('No layer buttons found');
                }
            }
            
            await this.screenshot('layer-panel-open');
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test switching to each available layer
    async testLayerSwitching() {
        console.log('\n🔄 Testing Layer Switching...');
        const results = [];
        
        // Define expected layers
        const expectedLayers = [
            { name: 'IGN', selector: '[data-layer="ign"]', urlPattern: 'geopf.fr' },
            { name: 'OSM', selector: '[data-layer="osm"]', urlPattern: 'openstreetmap.org' },
            { name: 'Satellite', selector: '[data-layer="satellite"]', urlPattern: ['arcgisonline', 'esri'] },
            { name: 'Terrain', selector: '[data-layer="terrain"]', urlPattern: 'opentopomap' }
        ];
        
        for (const layer of expectedLayers) {
            console.log(`\n  Testing ${layer.name} layer...`);
            const result = { 
                name: `Switch to ${layer.name}`, 
                passed: true, 
                errors: [], 
                details: {} 
            };
            
            try {
                this.currentTestLayer = layer.name;
                
                // Check if button exists
                const buttonExists = await this.page.$(layer.selector);
                if (!buttonExists) {
                    // Try alternative selector
                    const altButton = await this.page.$(`button:has-text("${layer.name}")`);
                    if (!altButton) {
                        result.errors.push(`${layer.name} button not found`);
                        result.passed = false;
                        results.push(result);
                        continue;
                    }
                }
                
                // Clear previous tile requests
                this.layerUrls.delete(layer.name);
                
                // Click the layer button
                await this.page.click(layer.selector || `button:has-text("${layer.name}")`);
                await new Promise(resolve => setTimeout(resolve, 3000)); // Wait for tiles to load
                
                // Verify layer switch
                const layerInfo = await this.page.evaluate((layerName) => {
                    const map = window._mainMap;
                    if (!map) return null;
                    
                    let currentTileUrl = null;
                    let tileCount = 0;
                    
                    map.eachLayer(layer => {
                        if (layer._url && layer._url.includes('http')) {
                            currentTileUrl = layer._url;
                            tileCount++;
                        }
                    });
                    
                    // Check active button
                    const activeButton = document.querySelector('.layer-btn.active');
                    
                    return {
                        tileUrl: currentTileUrl,
                        tileLayerCount: tileCount,
                        activeButtonText: activeButton ? activeButton.textContent.trim() : null,
                        mapCenter: map.getCenter(),
                        mapZoom: map.getZoom()
                    };
                }, layer.name);
                
                result.details = layerInfo;
                
                // Verify correct layer is active
                if (layerInfo) {
                    console.log(`    Tile URL: ${layerInfo.tileUrl ? layerInfo.tileUrl.substring(0, 60) + '...' : 'None'}`);
                    console.log(`    Active button: ${layerInfo.activeButtonText}`);
                    console.log(`    Tile layers count: ${layerInfo.tileLayerCount}`);
                    
                    // Check URL pattern
                    const patterns = Array.isArray(layer.urlPattern) ? layer.urlPattern : [layer.urlPattern];
                    const matchesPattern = patterns.some(pattern => 
                        layerInfo.tileUrl && layerInfo.tileUrl.includes(pattern)
                    );
                    
                    if (!matchesPattern && layerInfo.tileUrl) {
                        result.errors.push(`URL pattern mismatch. Expected: ${layer.urlPattern}, Got: ${layerInfo.tileUrl}`);
                    }
                    
                    // Check loaded tile domains
                    const loadedDomains = this.layerUrls.get(layer.name);
                    if (loadedDomains && loadedDomains.size > 0) {
                        console.log(`    Loaded tiles from: ${Array.from(loadedDomains).join(', ')}`);
                    }
                }
                
                await this.screenshot(`layer-${layer.name.toLowerCase()}`);
                
            } catch (error) {
                result.passed = false;
                result.errors.push(error.message);
            }
            
            results.push(result);
        }
        
        this.testResults.push(...results);
        return results;
    }

    // Test layer persistence after map interactions
    async testLayerPersistence() {
        console.log('\n🔒 Testing Layer Persistence...');
        const result = { name: 'Layer Persistence', passed: true, errors: [], details: {} };
        
        try {
            // Switch to Satellite layer
            await this.page.click('[data-layer="satellite"]');
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Get initial state
            const initialState = await this.page.evaluate(() => {
                const activeBtn = document.querySelector('.layer-btn.active');
                return activeBtn ? activeBtn.textContent.trim() : null;
            });
            
            // Perform map interactions
            console.log('  Testing persistence after zoom...');
            await this.page.click('.leaflet-control-zoom-in');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            await this.page.click('.leaflet-control-zoom-out');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            console.log('  Testing persistence after pan...');
            await this.page.mouse.move(960, 540);
            await this.page.mouse.down();
            await this.page.mouse.move(860, 540);
            await this.page.mouse.up();
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if layer persisted
            const finalState = await this.page.evaluate(() => {
                const activeBtn = document.querySelector('.layer-btn.active');
                return activeBtn ? activeBtn.textContent.trim() : null;
            });
            
            if (initialState !== finalState) {
                result.passed = false;
                result.errors.push(`Layer changed from ${initialState} to ${finalState} after interactions`);
            } else {
                console.log(`  ✅ Layer persisted as ${finalState}`);
            }
            
            result.details = { initialState, finalState };
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test layer loading performance
    async testLayerPerformance() {
        console.log('\n⚡ Testing Layer Performance...');
        const result = { name: 'Layer Performance', passed: true, errors: [], details: {} };
        
        try {
            const performanceMetrics = {};
            
            // Test each layer's loading time
            const layers = ['ign', 'osm', 'satellite'];
            
            for (const layerName of layers) {
                console.log(`  Measuring ${layerName} layer performance...`);
                
                // Clear cache and measure
                await this.page.evaluate(() => {
                    performance.clearResourceTimings();
                });
                
                const startTime = Date.now();
                
                // Switch layer
                await this.page.click(`[data-layer="${layerName}"]`);
                
                // Wait for tiles to start loading
                await this.page.waitForFunction(() => {
                    const entries = performance.getEntriesByType('resource');
                    return entries.some(e => e.name.includes('tile') || e.name.includes('wmts'));
                }, { timeout: 5000 });
                
                // Give more time for tiles to load
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                const loadTime = Date.now() - startTime;
                
                // Get performance metrics
                const metrics = await this.page.evaluate(() => {
                    const entries = performance.getEntriesByType('resource')
                        .filter(e => e.name.includes('tile') || e.name.includes('wmts'));
                    
                    if (entries.length === 0) return null;
                    
                    const durations = entries.map(e => e.duration);
                    return {
                        tileCount: entries.length,
                        avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
                        maxDuration: Math.max(...durations),
                        minDuration: Math.min(...durations),
                        totalSize: entries.reduce((sum, e) => sum + (e.transferSize || 0), 0)
                    };
                });
                
                performanceMetrics[layerName] = {
                    switchTime: loadTime,
                    ...metrics
                };
                
                if (metrics) {
                    console.log(`    Switch time: ${loadTime}ms`);
                    console.log(`    Tiles loaded: ${metrics.tileCount}`);
                    console.log(`    Avg tile time: ${metrics.avgDuration.toFixed(2)}ms`);
                    console.log(`    Total size: ${(metrics.totalSize / 1024).toFixed(2)}KB`);
                }
            }
            
            result.details = performanceMetrics;
            
            // Check performance thresholds
            Object.entries(performanceMetrics).forEach(([layer, metrics]) => {
                if (metrics && metrics.switchTime > 5000) {
                    result.errors.push(`${layer} layer took too long to load: ${metrics.switchTime}ms`);
                }
            });
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Run all layer tests
    async runAllTests() {
        console.log('🧪 Starting Map Layers Testing...\n');
        
        await this.testDefaultLayer();
        await this.testLayerPanel();
        await this.testLayerSwitching();
        await this.testLayerPersistence();
        await this.testLayerPerformance();
        
        // Close layers panel
        await this.page.click('#layersBtn');
        
        return this.generateReport();
    }

    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: this.testResults.length,
                passed: this.testResults.filter(t => t.passed).length,
                failed: this.testResults.filter(t => !t.passed).length
            },
            tests: this.testResults,
            tileServers: Object.fromEntries(this.layerUrls)
        };
        
        console.log('\n📊 Map Layers Test Report:\n');
        console.log(`Total Tests: ${report.summary.total}`);
        console.log(`Passed: ${report.summary.passed} ✅`);
        console.log(`Failed: ${report.summary.failed} ❌\n`);
        
        this.testResults.forEach(test => {
            const status = test.passed ? '✅' : '❌';
            console.log(`${status} ${test.name}`);
            
            if (test.errors.length > 0) {
                test.errors.forEach(error => {
                    console.log(`   ⚠️  ${error}`);
                });
            }
            
            if (test.details && Object.keys(test.details).length > 0) {
                console.log(`   📊 Details:`, test.details);
            }
        });
        
        console.log('\n🌐 Tile Servers Used:');
        this.layerUrls.forEach((domains, layer) => {
            if (domains.size > 0) {
                console.log(`  ${layer}: ${Array.from(domains).join(', ')}`);
            }
        });
        
        return report;
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
        }
    }
}

// Run tests if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const tester = new MapLayersTester();
    
    tester.init()
        .then(() => tester.runAllTests())
        .then(report => {
            return fs.writeFile(
                join(__dirname, 'layer-test-report.json'),
                JSON.stringify(report, null, 2)
            );
        })
        .then(() => tester.close())
        .then(() => {
            console.log('\n✅ Layer testing complete!');
            process.exit(0);
        })
        .catch(error => {
            console.error('❌ Layer testing failed:', error);
            tester.close().then(() => process.exit(1));
        });
}