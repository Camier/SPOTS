/**
 * Comprehensive Feature Testing for SPOTS Main Map
 * Tests all interactive features and functionality
 */

import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs/promises';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class FeatureTester {
    constructor(options = {}) {
        this.options = {
            headless: false, // Show browser for feature testing
            slowMo: 50,     // Slow down for visibility
            devtools: false,
            screenshotDir: join(__dirname, 'screenshots/features'),
            baseUrl: options.baseUrl || 'http://localhost:8085',
            timeout: 30000,
            ...options
        };
        
        this.browser = null;
        this.page = null;
        this.testResults = [];
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
        
        // Enable console logging
        this.page.on('console', msg => {
            if (msg.type() === 'error') {
                console.error('Browser error:', msg.text());
            }
        });
        
        // Ensure screenshot directory exists
        await fs.mkdir(this.options.screenshotDir, { recursive: true });
        
        // Load the main map
        const url = `${this.options.baseUrl}/main-map.html`;
        console.log(`Loading main map: ${url}`);
        await this.page.goto(url, { waitUntil: 'networkidle2' });
        
        // Wait for map to initialize
        await this.page.waitForSelector('#map');
        await this.page.waitForFunction(() => window.L && document.querySelector('.leaflet-container'));
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        return this;
    }

    async screenshot(name) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `${name}_${timestamp}.png`;
        const filepath = join(this.options.screenshotDir, filename);
        await this.page.screenshot({ path: filepath, fullPage: true });
        console.log(`  📸 Screenshot: ${filename}`);
        return filepath;
    }

    // Test 1: Search Functionality
    async testSearch() {
        console.log('\n🔍 Testing Search Feature...');
        const result = { feature: 'Search', passed: true, errors: [] };
        
        try {
            // Click search button
            await this.page.click('#searchBtn');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check if search panel opened
            const searchVisible = await this.page.evaluate(() => {
                const panel = document.querySelector('.search-panel');
                return panel && panel.style.display !== 'none';
            });
            
            if (!searchVisible) {
                result.errors.push('Search panel did not open');
                result.passed = false;
            }
            
            // Type in search input
            await this.page.type('#searchInput', 'Toulouse');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Press Enter or click search button
            await this.page.keyboard.press('Enter');
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check if map moved
            const mapCenter = await this.page.evaluate(() => {
                const map = window._mainMap;
                if (map) {
                    const center = map.getCenter();
                    return { lat: center.lat, lng: center.lng };
                }
                return null;
            });
            
            console.log('  Map center after search:', mapCenter);
            await this.screenshot('search-toulouse');
            
            // Close search panel
            await this.page.click('#searchBtn');
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test 2: Geolocation
    async testGeolocation() {
        console.log('\n📍 Testing Geolocation Feature...');
        const result = { feature: 'Geolocation', passed: true, errors: [] };
        
        try {
            // Mock geolocation
            await this.page.evaluateOnNewDocument(() => {
                navigator.geolocation.getCurrentPosition = (success) => {
                    success({
                        coords: {
                            latitude: 43.6047,
                            longitude: 1.4442,
                            accuracy: 100
                        }
                    });
                };
            });
            
            // Click geolocation button
            await this.page.click('#geolocateBtn');
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check if marker was added
            const hasLocationMarker = await this.page.evaluate(() => {
                let foundMarker = false;
                const map = window._mainMap;
                if (map) {
                    map.eachLayer(layer => {
                        if (layer instanceof L.Marker && layer.options.icon?.options?.className?.includes('location')) {
                            foundMarker = true;
                        }
                    });
                }
                return foundMarker;
            });
            
            if (!hasLocationMarker) {
                result.errors.push('Location marker not added to map');
            }
            
            await this.screenshot('geolocation-marker');
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test 3: Layer Switching
    async testLayers() {
        console.log('\n🗺️ Testing Layer Switching...');
        const result = { feature: 'Layer Switching', passed: true, errors: [] };
        
        try {
            // Click layers button
            await this.page.click('#layersBtn');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check if layers panel opened
            const layersVisible = await this.page.evaluate(() => {
                const panel = document.querySelector('.layers-panel');
                return panel && panel.style.display !== 'none';
            });
            
            if (!layersVisible) {
                result.errors.push('Layers panel did not open');
                result.passed = false;
            }
            
            // Test each layer
            const layers = ['OSM', 'Satellite', 'Terrain'];
            
            for (const layerName of layers) {
                console.log(`  Testing ${layerName} layer...`);
                
                // Click layer button
                const layerButton = await this.page.$(`button[data-layer="${layerName.toLowerCase()}"]`);
                if (layerButton) {
                    await layerButton.click();
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    // Verify layer changed
                    const currentLayer = await this.page.evaluate(() => {
                        const activeBtn = document.querySelector('.layer-btn.active');
                        return activeBtn ? activeBtn.textContent : null;
                    });
                    
                    console.log(`    Current layer: ${currentLayer}`);
                    await this.screenshot(`layer-${layerName.toLowerCase()}`);
                } else {
                    result.errors.push(`${layerName} layer button not found`);
                }
            }
            
            // Return to IGN layer
            await this.page.click('button[data-layer="ign"]');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Close layers panel
            await this.page.click('#layersBtn');
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test 4: Filters
    async testFilters() {
        console.log('\n🎯 Testing Filters Feature...');
        const result = { feature: 'Filters', passed: true, errors: [] };
        
        try {
            // Click filters button
            await this.page.click('#filtersBtn');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check if filters panel opened
            const filtersVisible = await this.page.evaluate(() => {
                const panel = document.querySelector('.filters-panel');
                return panel && panel.style.display !== 'none';
            });
            
            if (!filtersVisible) {
                result.errors.push('Filters panel did not open');
                result.passed = false;
            }
            
            // Test difficulty filter
            console.log('  Testing difficulty filter...');
            await this.page.click('input[name="difficulty"][value="facile"]');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Test spot type filter
            console.log('  Testing spot type filter...');
            await this.page.click('input[name="type"][value="cascade"]');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Test beauty slider
            console.log('  Testing beauty slider...');
            const beautySlider = await this.page.$('#beautyRange');
            if (beautySlider) {
                await this.page.evaluate(() => {
                    document.querySelector('#beautyRange').value = 4;
                    document.querySelector('#beautyRange').dispatchEvent(new Event('input'));
                });
            }
            
            // Apply filters
            await this.page.click('#applyFilters');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            await this.screenshot('filters-applied');
            
            // Reset filters
            await this.page.click('#resetFilters');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Close filters panel
            await this.page.click('#filtersBtn');
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test 5: Weather Display
    async testWeather() {
        console.log('\n☀️ Testing Weather Feature...');
        const result = { feature: 'Weather', passed: true, errors: [] };
        
        try {
            // Click weather button
            await this.page.click('#weatherBtn');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check if weather panel opened
            const weatherVisible = await this.page.evaluate(() => {
                const panel = document.querySelector('.weather-panel');
                return panel && panel.style.display !== 'none';
            });
            
            if (!weatherVisible) {
                result.errors.push('Weather panel did not open');
                result.passed = false;
            }
            
            // Wait for weather data to load
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check if weather data is displayed
            const hasWeatherData = await this.page.evaluate(() => {
                const weatherContent = document.querySelector('.weather-content');
                return weatherContent && weatherContent.textContent.includes('°C');
            });
            
            if (!hasWeatherData) {
                result.errors.push('Weather data not displayed');
            }
            
            await this.screenshot('weather-panel');
            
            // Close weather panel
            await this.page.click('#weatherBtn');
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test 6: Add Spot Modal
    async testAddSpot() {
        console.log('\n➕ Testing Add Spot Feature...');
        const result = { feature: 'Add Spot', passed: true, errors: [] };
        
        try {
            // Click add spot button
            await this.page.click('#addSpotBtn');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check if modal opened
            const modalVisible = await this.page.evaluate(() => {
                const modal = document.querySelector('#addSpotModal');
                return modal && modal.style.display === 'block';
            });
            
            if (!modalVisible) {
                result.errors.push('Add spot modal did not open');
                result.passed = false;
            }
            
            // Fill in form fields
            await this.page.type('#spotName', 'Test Cascade');
            await this.page.select('#spotType', 'cascade');
            await this.page.select('#spotDifficulty', 'moyen');
            
            // Set sliders
            await this.page.evaluate(() => {
                document.querySelector('#spotBeauty').value = 4;
                document.querySelector('#spotPopularity').value = 2;
            });
            
            await this.page.type('#spotDescription', 'Une belle cascade de test');
            
            await this.screenshot('add-spot-form');
            
            // Close modal
            await this.page.click('.close');
            await new Promise(resolve => setTimeout(resolve, 500));
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test 7: Map Interactions (Click on spots)
    async testSpotInteraction() {
        console.log('\n👆 Testing Spot Interaction...');
        const result = { feature: 'Spot Interaction', passed: true, errors: [] };
        
        try {
            // Click on map to simulate clicking a spot
            await this.page.click('#map', { position: { x: 960, y: 540 } });
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if popup appeared
            const hasPopup = await this.page.evaluate(() => {
                return document.querySelector('.leaflet-popup') !== null;
            });
            
            if (hasPopup) {
                console.log('  Popup appeared after click');
                await this.screenshot('spot-popup');
                
                // Try to click "Voir détails" if available
                const detailsBtn = await this.page.$('.leaflet-popup button');
                if (detailsBtn) {
                    await detailsBtn.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Check if spot details modal opened
                    const detailsVisible = await this.page.evaluate(() => {
                        const modal = document.querySelector('#spotDetailsModal');
                        return modal && modal.style.display === 'block';
                    });
                    
                    if (detailsVisible) {
                        console.log('  Spot details modal opened');
                        await this.screenshot('spot-details');
                        
                        // Close modal
                        await this.page.click('#spotDetailsModal .close');
                    }
                }
            } else {
                result.errors.push('No popup appeared when clicking on map');
            }
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test 8: Responsive Design
    async testResponsive() {
        console.log('\n📱 Testing Responsive Design...');
        const result = { feature: 'Responsive Design', passed: true, errors: [] };
        
        try {
            // Test mobile viewport
            await this.page.setViewport({ width: 375, height: 667 });
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if mobile menu is visible
            const hasMobileMenu = await this.page.evaluate(() => {
                const header = document.querySelector('.main-header');
                return window.getComputedStyle(header).getPropertyValue('flex-wrap') === 'wrap';
            });
            
            await this.screenshot('responsive-mobile');
            
            // Test tablet viewport
            await this.page.setViewport({ width: 768, height: 1024 });
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            await this.screenshot('responsive-tablet');
            
            // Return to desktop
            await this.page.setViewport({ width: 1920, height: 1080 });
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Run all feature tests
    async runAllTests() {
        console.log('🧪 Starting Comprehensive Feature Testing...\n');
        
        await this.testSearch();
        await this.testGeolocation();
        await this.testLayers();
        await this.testFilters();
        await this.testWeather();
        await this.testAddSpot();
        await this.testSpotInteraction();
        await this.testResponsive();
        
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
            tests: this.testResults
        };
        
        console.log('\n📊 Feature Test Report:\n');
        console.log(`Total Features Tested: ${report.summary.total}`);
        console.log(`Passed: ${report.summary.passed} ✅`);
        console.log(`Failed: ${report.summary.failed} ❌\n`);
        
        this.testResults.forEach(test => {
            const status = test.passed ? '✅' : '❌';
            console.log(`${status} ${test.feature}`);
            
            if (test.errors.length > 0) {
                test.errors.forEach(error => {
                    console.log(`   ⚠️  ${error}`);
                });
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
    const tester = new FeatureTester();
    
    tester.init()
        .then(() => tester.runAllTests())
        .then(report => {
            // Save report
            return fs.writeFile(
                join(__dirname, 'feature-test-report.json'),
                JSON.stringify(report, null, 2)
            );
        })
        .then(() => tester.close())
        .then(() => {
            console.log('\n✅ Feature testing complete!');
            process.exit(0);
        })
        .catch(error => {
            console.error('❌ Feature testing failed:', error);
            tester.close().then(() => process.exit(1));
        });
}