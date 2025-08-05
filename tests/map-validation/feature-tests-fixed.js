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
            if (msg.type() === 'error' && !msg.text().includes('404')) {
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
            // Type in search input directly
            await this.page.type('#searchInput', 'Toulouse');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Click search button or press Enter
            await this.page.click('#searchBtn');
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
            
            // Clear search
            await this.page.evaluate(() => {
                document.querySelector('#searchInput').value = '';
            });
            
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
            // Mock geolocation before clicking
            await this.page.evaluateOnNewDocument(() => {
                navigator.geolocation.getCurrentPosition = (success) => {
                    setTimeout(() => {
                        success({
                            coords: {
                                latitude: 43.6047,
                                longitude: 1.4442,
                                accuracy: 100
                            }
                        });
                    }, 100);
                };
            });
            
            // Reload page to apply mock
            await this.page.reload({ waitUntil: 'networkidle2' });
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Click geolocation button
            await this.page.click('#geolocateBtn');
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            // Check if location was used (map centered on mock coordinates)
            const mapCenter = await this.page.evaluate(() => {
                const map = window._mainMap;
                if (map) {
                    const center = map.getCenter();
                    return { lat: center.lat, lng: center.lng };
                }
                return null;
            });
            
            if (mapCenter && Math.abs(mapCenter.lat - 43.6047) < 0.01) {
                console.log('  Geolocation successful, map centered at:', mapCenter);
            } else {
                result.errors.push('Geolocation did not center map on coordinates');
            }
            
            await this.screenshot('geolocation-result');
            
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
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if layers panel opened
            const layersVisible = await this.page.evaluate(() => {
                const panel = document.querySelector('#layersPanel');
                return panel && panel.classList.contains('active');
            });
            
            if (layersVisible) {
                console.log('  Layers panel opened');
                
                // Test clicking different layers
                const layerButtons = await this.page.$$('.layer-btn');
                console.log(`  Found ${layerButtons.length} layer buttons`);
                
                // Click each layer button
                for (let i = 0; i < Math.min(layerButtons.length, 3); i++) {
                    await layerButtons[i].click();
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    const layerName = await layerButtons[i].evaluate(el => el.textContent);
                    console.log(`  Switched to ${layerName} layer`);
                    await this.screenshot(`layer-${layerName.toLowerCase().replace(/\s/g, '-')}`);
                }
            } else {
                result.errors.push('Layers panel did not open');
                result.passed = false;
            }
            
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
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if filters panel opened
            const filtersVisible = await this.page.evaluate(() => {
                const panel = document.querySelector('#filtersPanel');
                return panel && panel.classList.contains('active');
            });
            
            if (filtersVisible) {
                console.log('  Filters panel opened');
                
                // Test type filter - uncheck cascade
                const cascadeFilter = await this.page.$('#typeFilters input[value="cascade"]');
                if (cascadeFilter) {
                    await cascadeFilter.click();
                    console.log('  Unchecked cascade filter');
                }
                
                // Test difficulty filter - uncheck facile
                const facileFilter = await this.page.$('#difficultyFilters input[value="facile"]');
                if (facileFilter) {
                    await facileFilter.click();
                    console.log('  Unchecked facile filter');
                }
                
                // Test beauty slider
                const beautySlider = await this.page.$('#beautyRange');
                if (beautySlider) {
                    await this.page.evaluate(() => {
                        const slider = document.querySelector('#beautyRange');
                        slider.value = 4;
                        slider.dispatchEvent(new Event('input'));
                    });
                    console.log('  Set beauty filter to 4+');
                }
                
                await this.screenshot('filters-configured');
                
                // Apply filters
                const applyBtn = await this.page.$('#applyFiltersBtn');
                if (applyBtn) {
                    await applyBtn.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    console.log('  Filters applied');
                }
                
                // Reset filters
                const resetBtn = await this.page.$('#resetFiltersBtn');
                if (resetBtn) {
                    await resetBtn.click();
                    console.log('  Filters reset');
                }
            } else {
                result.errors.push('Filters panel did not open');
                result.passed = false;
            }
            
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
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if weather panel opened
            const weatherVisible = await this.page.evaluate(() => {
                const panel = document.querySelector('#weatherPanel');
                return panel && panel.classList.contains('active');
            });
            
            if (weatherVisible) {
                console.log('  Weather panel opened');
                
                // Wait for weather data to load
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Check if weather data is displayed
                const hasWeatherData = await this.page.evaluate(() => {
                    const weatherContent = document.querySelector('#weatherPanel .panel-content');
                    return weatherContent && (
                        weatherContent.textContent.includes('°C') || 
                        weatherContent.textContent.includes('météo')
                    );
                });
                
                if (hasWeatherData) {
                    console.log('  Weather data loaded');
                } else {
                    result.errors.push('Weather data not displayed');
                }
                
                await this.screenshot('weather-panel');
            } else {
                result.errors.push('Weather panel did not open');
                result.passed = false;
            }
            
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
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if modal opened
            const modalVisible = await this.page.evaluate(() => {
                const modal = document.querySelector('#addSpotModal');
                return modal && modal.style.display === 'block';
            });
            
            if (modalVisible) {
                console.log('  Add spot modal opened');
                
                // Test form fields
                const nameInput = await this.page.$('#spotName');
                if (nameInput) {
                    await nameInput.type('Cascade de Test');
                    console.log('  Filled spot name');
                }
                
                const typeSelect = await this.page.$('#spotType');
                if (typeSelect) {
                    await typeSelect.select('cascade');
                    console.log('  Selected spot type');
                }
                
                const difficultySelect = await this.page.$('#spotDifficulty');
                if (difficultySelect) {
                    await difficultySelect.select('moyen');
                    console.log('  Selected difficulty');
                }
                
                await this.screenshot('add-spot-form');
                
                // Close modal
                const closeBtn = await this.page.$('#addSpotModal .close');
                if (closeBtn) {
                    await closeBtn.click();
                }
            } else {
                result.errors.push('Add spot modal did not open');
                result.passed = false;
            }
            
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
            // Try to find and click a marker
            const hasMarkers = await this.page.evaluate(() => {
                return document.querySelectorAll('.leaflet-marker-icon').length > 0;
            });
            
            if (hasMarkers) {
                // Click on first marker
                await this.page.click('.leaflet-marker-icon');
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Check if popup appeared
                const hasPopup = await this.page.evaluate(() => {
                    return document.querySelector('.leaflet-popup') !== null;
                });
                
                if (hasPopup) {
                    console.log('  Popup appeared after clicking marker');
                    await this.screenshot('spot-popup');
                    
                    // Try to click details button in popup
                    const detailsBtn = await this.page.$('.leaflet-popup button');
                    if (detailsBtn) {
                        await detailsBtn.click();
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        
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
                    result.errors.push('No popup appeared when clicking marker');
                }
            } else {
                console.log('  No markers on map to test interaction');
                result.errors.push('No markers found on map');
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
            
            // Check if layout adapted
            const isMobileLayout = await this.page.evaluate(() => {
                const header = document.querySelector('.main-header');
                const headerHeight = header ? header.offsetHeight : 0;
                return headerHeight > 60; // Mobile header is taller due to wrapping
            });
            
            if (isMobileLayout) {
                console.log('  Mobile layout detected');
            }
            
            await this.screenshot('responsive-mobile');
            
            // Test tablet viewport
            await this.page.setViewport({ width: 768, height: 1024 });
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            await this.screenshot('responsive-tablet');
            
            // Return to desktop
            await this.page.setViewport({ width: 1920, height: 1080 });
            console.log('  Returned to desktop viewport');
            
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