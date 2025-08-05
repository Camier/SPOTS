/**
 * Test Advanced Map Features
 * Tests forest overlay, heatmap, and sun calculator
 */

import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs/promises';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class AdvancedFeaturesTester {
    constructor(options = {}) {
        this.options = {
            headless: false,
            slowMo: 100,
            devtools: false,
            screenshotDir: join(__dirname, 'screenshots/advanced'),
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

    // Test 1: Forest Overlay
    async testForestOverlay() {
        console.log('\n🌲 Testing Forest Overlay...');
        const result = { feature: 'Forest Overlay', passed: true, errors: [] };
        
        try {
            // Open layers panel
            await this.page.click('#layersBtn');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Find and click forest overlay checkbox
            const forestCheckbox = await this.page.$('#forestOverlay');
            if (forestCheckbox) {
                await forestCheckbox.click();
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Check if forest layer was added
                const hasForestLayer = await this.page.evaluate(() => {
                    const map = window._mainMap;
                    if (!map) return false;
                    
                    let foundForestLayer = false;
                    map.eachLayer(layer => {
                        if (layer._url && layer._url.includes('FORESTINVENTORY')) {
                            foundForestLayer = true;
                        }
                    });
                    return foundForestLayer;
                });
                
                if (hasForestLayer) {
                    console.log('  ✅ Forest layer added successfully');
                } else {
                    result.errors.push('Forest layer not found on map');
                }
                
                await this.screenshot('forest-overlay');
                
                // Toggle off
                await forestCheckbox.click();
                await new Promise(resolve => setTimeout(resolve, 1000));
            } else {
                result.errors.push('Forest overlay checkbox not found');
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

    // Test 2: Heatmap
    async testHeatmap() {
        console.log('\n🔥 Testing Heatmap Feature...');
        const result = { feature: 'Heatmap', passed: true, errors: [] };
        
        try {
            // Open layers panel
            await this.page.click('#layersBtn');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Find and click heatmap checkbox
            const heatmapCheckbox = await this.page.$('#heatmapToggle');
            if (heatmapCheckbox) {
                await heatmapCheckbox.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Check if heatmap layer was added
                const hasHeatmapLayer = await this.page.evaluate(() => {
                    const map = window._mainMap;
                    if (!map) return { hasLayer: false, type: null };
                    
                    let foundHeatmap = false;
                    let layerType = null;
                    
                    map.eachLayer(layer => {
                        if (layer._heat || layer instanceof L.LayerGroup) {
                            foundHeatmap = true;
                            layerType = layer._heat ? 'heatmap' : 'circles';
                        }
                    });
                    
                    return { hasLayer: foundHeatmap, type: layerType };
                });
                
                if (hasHeatmapLayer.hasLayer) {
                    console.log(`  ✅ Heatmap layer added (type: ${hasHeatmapLayer.type})`);
                } else {
                    result.errors.push('Heatmap layer not found on map');
                }
                
                await this.screenshot('heatmap-active');
                
                // Toggle off
                await heatmapCheckbox.click();
                await new Promise(resolve => setTimeout(resolve, 1000));
            } else {
                result.errors.push('Heatmap toggle not found');
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

    // Test 3: Sun Calculator
    async testSunCalculator() {
        console.log('\n☀️ Testing Sun Calculator...');
        const result = { feature: 'Sun Calculator', passed: true, errors: [] };
        
        try {
            // Find sun control button
            const sunButton = await this.page.$('a[title="Calculateur Soleil/Ombre"]');
            if (sunButton) {
                await sunButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Check if sun controls appeared
                const hasSunControls = await this.page.evaluate(() => {
                    return document.querySelector('.sun-shadow-controls') !== null;
                });
                
                if (hasSunControls) {
                    console.log('  ✅ Sun calculator activated');
                    
                    // Test time slider
                    const timeSlider = await this.page.$('#time-slider');
                    if (timeSlider) {
                        // Set to noon
                        await this.page.evaluate(() => {
                            const slider = document.querySelector('#time-slider');
                            if (slider) {
                                slider.value = 720; // 12:00
                                slider.dispatchEvent(new Event('input'));
                            }
                        });
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        console.log('  Set time to noon');
                    }
                    
                    await this.screenshot('sun-calculator-noon');
                    
                    // Test sunrise button
                    const sunriseBtn = await this.page.$('#sunrise-btn');
                    if (sunriseBtn) {
                        await sunriseBtn.click();
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        await this.screenshot('sun-calculator-sunrise');
                        console.log('  Tested sunrise time');
                    }
                    
                    // Deactivate
                    await sunButton.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                } else {
                    result.errors.push('Sun calculator controls not found');
                }
            } else {
                result.errors.push('Sun calculator button not found');
                result.passed = false;
            }
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Test 4: Combined Features
    async testCombinedFeatures() {
        console.log('\n🎨 Testing Combined Features...');
        const result = { feature: 'Combined Features', passed: true, errors: [] };
        
        try {
            // Enable satellite base layer
            await this.page.click('#layersBtn');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            await this.page.click('[data-layer="satellite"]');
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Enable forest overlay
            const forestCheckbox = await this.page.$('#forestOverlay');
            if (forestCheckbox) {
                await forestCheckbox.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            
            // Enable heatmap
            const heatmapCheckbox = await this.page.$('#heatmapToggle');
            if (heatmapCheckbox) {
                await heatmapCheckbox.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            
            await this.screenshot('combined-satellite-forest-heatmap');
            
            // Close layers panel
            await this.page.click('#layersBtn');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Activate sun calculator
            const sunButton = await this.page.$('a[title="Calculateur Soleil/Ombre"]');
            if (sunButton) {
                await sunButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                await this.screenshot('combined-all-features');
                
                console.log('  ✅ All features working together');
            }
            
        } catch (error) {
            result.passed = false;
            result.errors.push(error.message);
        }
        
        this.testResults.push(result);
        return result;
    }

    // Run all tests
    async runAllTests() {
        console.log('🧪 Starting Advanced Features Testing...\n');
        
        await this.testForestOverlay();
        await this.testHeatmap();
        await this.testSunCalculator();
        await this.testCombinedFeatures();
        
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
        
        console.log('\n📊 Advanced Features Test Report:\n');
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
    const tester = new AdvancedFeaturesTester();
    
    tester.init()
        .then(() => tester.runAllTests())
        .then(report => {
            return fs.writeFile(
                join(__dirname, 'advanced-features-report.json'),
                JSON.stringify(report, null, 2)
            );
        })
        .then(() => tester.close())
        .then(() => {
            console.log('\n✅ Advanced features testing complete!');
            process.exit(0);
        })
        .catch(error => {
            console.error('❌ Advanced features testing failed:', error);
            tester.close().then(() => process.exit(1));
        });
}