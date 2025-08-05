#!/usr/bin/env node

/**
 * Validate Main Map with Advanced Features
 */

import { MapValidator } from './map-validator.js';

const options = {
    headless: false,
    screenshotDir: './screenshots',
    baseUrl: 'http://localhost:8085'
};

console.log('🗺️  Validating Main Map with Advanced Features\n');

const validator = new MapValidator(options);

// Custom tests for advanced features
async function validateAdvancedFeatures(validator) {
    const advancedTests = [];
    
    // Test Forest Overlay
    const forestTest = { name: 'Forest Overlay', passed: true, errors: [] };
    try {
        await validator.page.click('#layersBtn');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const forestCheckbox = await validator.page.$('#forestOverlay');
        if (forestCheckbox) {
            await forestCheckbox.click();
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const hasForestLayer = await validator.page.evaluate(() => {
                const map = window._mainMap;
                if (!map) return false;
                
                let found = false;
                map.eachLayer(layer => {
                    if (layer._url && layer._url.includes('FORESTINVENTORY')) {
                        found = true;
                    }
                });
                return found;
            });
            
            if (!hasForestLayer) {
                forestTest.passed = false;
                forestTest.errors.push('Forest layer not activated');
            }
        } else {
            forestTest.passed = false;
            forestTest.errors.push('Forest overlay checkbox not found');
        }
    } catch (error) {
        forestTest.passed = false;
        forestTest.errors.push(error.message);
    }
    advancedTests.push(forestTest);
    
    // Test Heatmap
    const heatmapTest = { name: 'Heatmap View', passed: true, errors: [] };
    try {
        const heatmapCheckbox = await validator.page.$('#heatmapToggle');
        if (heatmapCheckbox) {
            await heatmapCheckbox.click();
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const hasHeatmap = await validator.page.evaluate(() => {
                const map = window._mainMap;
                if (!map) return false;
                
                let found = false;
                map.eachLayer(layer => {
                    if (layer._heat || layer instanceof L.LayerGroup) {
                        found = true;
                    }
                });
                return found;
            });
            
            if (!hasHeatmap) {
                heatmapTest.passed = false;
                heatmapTest.errors.push('Heatmap layer not activated');
            }
        } else {
            heatmapTest.passed = false;
            heatmapTest.errors.push('Heatmap toggle not found');
        }
        
        await validator.page.click('#layersBtn'); // Close panel
    } catch (error) {
        heatmapTest.passed = false;
        heatmapTest.errors.push(error.message);
    }
    advancedTests.push(heatmapTest);
    
    // Test Sun Calculator
    const sunTest = { name: 'Sun Calculator', passed: true, errors: [] };
    try {
        const sunButton = await validator.page.$('a[title="Calculateur Soleil/Ombre"]');
        if (sunButton) {
            await sunButton.click();
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const isSunActive = await validator.page.evaluate(() => {
                return window._mainMap && 
                       typeof window._mainMap.sunCalculatorActive !== 'undefined';
            });
            
            if (!isSunActive) {
                sunTest.errors.push('Sun calculator not properly initialized');
            }
        } else {
            sunTest.passed = false;
            sunTest.errors.push('Sun calculator button not found');
        }
    } catch (error) {
        sunTest.passed = false;
        sunTest.errors.push(error.message);
    }
    advancedTests.push(sunTest);
    
    // Add to validation results
    validator.validationResults.push(...advancedTests);
    
    // Take final screenshot
    await validator.screenshot('main-map-advanced-features');
}

validator.init()
    .then(() => validator.loadMap('/main-map.html'))
    .then(() => validator.validateMapInit())
    .then(() => validator.validateLayers())
    .then(() => validator.validateControls())
    .then(() => validateAdvancedFeatures(validator))
    .then(() => validator.generateReport())
    .then(report => {
        console.log('\n📊 Advanced Features Summary:');
        const advancedResults = report.validations.filter(v => 
            ['Forest Overlay', 'Heatmap View', 'Sun Calculator'].includes(v.name)
        );
        
        advancedResults.forEach(result => {
            const status = result.passed ? '✅' : '❌';
            console.log(`${status} ${result.name}`);
            if (result.errors.length > 0) {
                result.errors.forEach(err => console.log(`   ⚠️  ${err}`));
            }
        });
        
        return validator.close();
    })
    .then(() => {
        console.log('\n✅ Main map validation complete!');
        process.exit(0);
    })
    .catch(error => {
        console.error('❌ Validation failed:', error.message);
        validator.close().then(() => process.exit(1));
    });