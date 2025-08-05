/**
 * Map Validation Test Scenarios
 * Specific tests for SPOTS project maps
 */

import MapValidator from './map-validator.js';

export const testScenarios = {
    /**
     * Main production map
     */
    mainMap: {
        path: '/main-map.html',
        name: 'Main Production Map',
        tests: [
            {
                name: 'Map Initialization',
                async validate(validator) {
                    const mapInfo = await validator.page.evaluate(() => {
                        const map = window._mainMap;
                        if (map && map._container) {
                            return {
                                hasMap: true,
                                center: map.getCenter(),
                                zoom: map.getZoom()
                            };
                        }
                        return { hasMap: false };
                    });
                    
                    return {
                        passed: mapInfo.hasMap,
                        message: mapInfo.hasMap ? 
                            `Main map initialized at ${mapInfo.center.lat.toFixed(4)}, ${mapInfo.center.lng.toFixed(4)} zoom ${mapInfo.zoom}` : 
                            'Map not found'
                    };
                }
            },
            {
                name: 'Header Controls',
                async validate(validator) {
                    const controls = await validator.page.evaluate(() => {
                        return {
                            search: document.querySelector('#searchInput') !== null,
                            geolocate: document.querySelector('#geolocateBtn') !== null,
                            layers: document.querySelector('#layersBtn') !== null,
                            filters: document.querySelector('#filtersBtn') !== null,
                            weather: document.querySelector('#weatherBtn') !== null,
                            addSpot: document.querySelector('#addSpotBtn') !== null
                        };
                    });
                    
                    const allPresent = Object.values(controls).every(v => v);
                    
                    return {
                        passed: allPresent,
                        message: allPresent ? 'All controls present' : 'Missing controls',
                        details: controls
                    };
                }
            },
            {
                name: 'Spot Counter',
                async validate(validator) {
                    const counter = await validator.page.$eval('#spotCounter', el => el.textContent);
                    
                    return {
                        passed: true,
                        message: `Spot counter shows: ${counter}`
                    };
                }
            },
            {
                name: 'Sidebar Panels',
                async validate(validator) {
                    const panels = await validator.page.evaluate(() => {
                        return {
                            filters: document.querySelector('#filtersPanel') !== null,
                            layers: document.querySelector('#layersPanel') !== null,
                            weather: document.querySelector('#weatherPanel') !== null
                        };
                    });
                    
                    const allPresent = Object.values(panels).every(v => v);
                    
                    return {
                        passed: allPresent,
                        message: allPresent ? 'All panels present' : 'Missing panels'
                    };
                }
            },
            {
                name: 'Modals',
                async validate(validator) {
                    const modals = await validator.page.evaluate(() => {
                        return {
                            spotModal: document.querySelector('#spotModal') !== null,
                            addSpotModal: document.querySelector('#addSpotModal') !== null
                        };
                    });
                    
                    const allPresent = Object.values(modals).every(v => v);
                    
                    return {
                        passed: allPresent,
                        message: allPresent ? 'All modals present' : 'Missing modals'
                    };
                }
            },
            {
                name: 'Filter Interaction',
                async validate(validator) {
                    // Click filters button
                    await validator.page.click('#filtersBtn');
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    // Check if panel opened
                    const panelActive = await validator.page.evaluate(() => {
                        return document.querySelector('#filtersPanel').classList.contains('active');
                    });
                    
                    return {
                        passed: panelActive,
                        message: panelActive ? 'Filter panel opens correctly' : 'Filter panel failed to open'
                    };
                }
            }
        ]
    },
    
    /**
     * Simple test map for validation testing
     */
    testMap: {
        path: '/test-map.html',
        name: 'Test Map Validation',
        tests: [
            {
                name: 'Map Loads',
                async validate(validator) {
                    const hasMap = await validator.page.evaluate(() => {
                        return window.map && window.map._container;
                    });
                    
                    return {
                        passed: hasMap,
                        message: hasMap ? 'Map loaded successfully' : 'Map not found'
                    };
                }
            },
            {
                name: 'IGN Tiles Present',
                async validate(validator) {
                    const tileInfo = await validator.page.evaluate(() => {
                        const tiles = document.querySelectorAll('img[src*="data.geopf.fr"]');
                        return {
                            count: tiles.length,
                            loaded: Array.from(tiles).filter(img => img.complete).length
                        };
                    });
                    
                    return {
                        passed: tileInfo.count > 0,
                        message: `Found ${tileInfo.loaded}/${tileInfo.count} IGN tiles`
                    };
                }
            },
            {
                name: 'Marker Present',
                async validate(validator) {
                    const hasMarker = await validator.page.evaluate(() => {
                        return document.querySelector('.leaflet-marker-icon') !== null;
                    });
                    
                    return {
                        passed: hasMarker,
                        message: hasMarker ? 'Marker found' : 'No marker found'
                    };
                }
            }
        ]
    },
    /**
     * Test the main regional map
     */
    regionalMap: {
        path: '/regional-map-optimized.html',
        name: 'Regional Map Optimized',
        tests: [
            {
                name: 'IGN Tiles Load',
                async validate(validator) {
                    const tiles = await validator.page.evaluate(() => {
                        const images = Array.from(document.querySelectorAll('img[src*="data.geopf.fr"]'));
                        return {
                            count: images.length,
                            loaded: images.filter(img => img.complete && img.naturalHeight > 0).length
                        };
                    });
                    
                    return {
                        passed: tiles.count > 0 && tiles.loaded === tiles.count,
                        message: `${tiles.loaded}/${tiles.count} IGN tiles loaded`
                    };
                }
            },
            {
                name: 'Spot Markers Display',
                async validate(validator) {
                    const markers = await validator.page.evaluate(() => {
                        return {
                            count: document.querySelectorAll('.leaflet-marker-icon').length,
                            clusters: document.querySelectorAll('.leaflet-marker-cluster').length
                        };
                    });
                    
                    return {
                        passed: markers.count > 0 || markers.clusters > 0,
                        message: `${markers.count} markers, ${markers.clusters} clusters`
                    };
                }
            },
            {
                name: 'Filter Controls Work',
                async validate(validator) {
                    // Look for filter controls
                    const hasFilters = await validator.page.$('#controls, .filter-controls') !== null;
                    
                    if (hasFilters) {
                        // Test a filter
                        const filterButton = await validator.page.$('button[data-type], input[type="checkbox"]');
                        if (filterButton) {
                            await filterButton.click();
                            await new Promise(resolve => setTimeout(resolve, 500));
                        }
                    }
                    
                    return {
                        passed: hasFilters,
                        message: hasFilters ? 'Filter controls found' : 'No filter controls'
                    };
                }
            }
        ]
    },

    /**
     * Test sun/shadow calculator
     */
    sunShadowDemo: {
        path: '/sun-shadow-demo.html',
        name: 'Sun Shadow Calculator Demo',
        tests: [
            {
                name: 'Sun Calculator Loads',
                async validate(validator) {
                    const hasCalculator = await validator.page.evaluate(() => {
                        return document.querySelector('.sun-shadow-controls') !== null ||
                               window.sunCalc !== undefined;
                    });
                    
                    return {
                        passed: hasCalculator,
                        message: hasCalculator ? 'Sun calculator initialized' : 'Sun calculator not found'
                    };
                }
            },
            {
                name: 'Time Slider Works',
                async validate(validator) {
                    const slider = await validator.page.$('#time-slider, #time-slider-enhanced');
                    if (!slider) {
                        return { passed: false, message: 'Time slider not found' };
                    }
                    
                    // Get initial value
                    const initialTime = await validator.page.$eval(
                        '#sun-time, #time-display', 
                        el => el.textContent
                    );
                    
                    // Move slider
                    await validator.page.evaluate(() => {
                        const slider = document.querySelector('#time-slider, #time-slider-enhanced');
                        slider.value = '720'; // Noon
                        slider.dispatchEvent(new Event('input'));
                    });
                    
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    // Check if time changed
                    const newTime = await validator.page.$eval(
                        '#sun-time, #time-display', 
                        el => el.textContent
                    );
                    
                    return {
                        passed: initialTime !== newTime,
                        message: `Time changed from ${initialTime} to ${newTime}`
                    };
                }
            },
            {
                name: 'Sun Position Updates',
                async validate(validator) {
                    const position = await validator.page.evaluate(() => {
                        const altEl = document.querySelector('#sun-altitude, #sun-alt-display');
                        const azEl = document.querySelector('#sun-azimuth, #sun-az-display');
                        
                        return {
                            altitude: altEl?.textContent || 'N/A',
                            azimuth: azEl?.textContent || 'N/A'
                        };
                    });
                    
                    return {
                        passed: position.altitude !== 'N/A' && position.azimuth !== 'N/A',
                        message: `Sun position: ${position.altitude}, ${position.azimuth}`
                    };
                }
            }
        ]
    },

    /**
     * Test elevation integration
     */
    sunShadowWorking: {
        path: '/sun-shadow-working.html',
        name: 'Sun Shadow with IGN Elevation',
        tests: [
            {
                name: 'API Connection',
                async validate(validator) {
                    const apiStatus = await validator.page.evaluate(() => {
                        const statusEl = document.querySelector('#api-status');
                        return statusEl?.classList.contains('status-ok') || false;
                    });
                    
                    return {
                        passed: apiStatus,
                        message: apiStatus ? 'API connected' : 'API not connected'
                    };
                }
            },
            {
                name: 'Elevation on Click',
                async validate(validator) {
                    // Click on map
                    await validator.page.click('#map', { position: { x: 500, y: 400 } });
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Check if elevation was displayed
                    const elevation = await validator.page.evaluate(() => {
                        const el = document.querySelector('#click-elevation, #elevation-info');
                        return el?.textContent || '';
                    });
                    
                    const hasElevation = elevation.includes('m') && 
                                        (elevation.includes('Élévation') || elevation.includes('elevation'));
                    
                    return {
                        passed: hasElevation,
                        message: hasElevation ? 'Elevation displayed' : 'No elevation data'
                    };
                }
            },
            {
                name: 'Terrain Shadows Toggle',
                async validate(validator) {
                    const checkbox = await validator.page.$('#terrain-shadows');
                    if (!checkbox) {
                        return { passed: false, message: 'Terrain shadows checkbox not found' };
                    }
                    
                    await checkbox.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    const isChecked = await validator.page.$eval('#terrain-shadows', el => el.checked);
                    
                    return {
                        passed: true,
                        message: `Terrain shadows ${isChecked ? 'enabled' : 'disabled'}`
                    };
                }
            }
        ]
    },

    /**
     * Performance benchmarks
     */
    performanceBenchmark: {
        path: '/regional-map-optimized.html',
        name: 'Performance Benchmark',
        tests: [
            {
                name: 'Initial Load Time',
                async validate(validator) {
                    const metrics = await validator.page.evaluate(() => {
                        const perf = window.performance;
                        const navigation = perf.getEntriesByType('navigation')[0];
                        
                        return {
                            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                            loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                            totalTime: navigation.loadEventEnd - navigation.fetchStart
                        };
                    });
                    
                    const passed = metrics.totalTime < 3000; // 3 second threshold
                    
                    return {
                        passed: passed,
                        message: `Total load time: ${metrics.totalTime.toFixed(0)}ms`,
                        metrics: metrics
                    };
                }
            },
            {
                name: 'Memory Usage',
                async validate(validator) {
                    if (!validator.page.evaluate(() => window.performance.memory)) {
                        return { passed: true, message: 'Memory API not available' };
                    }
                    
                    const memory = await validator.page.evaluate(() => {
                        const mem = window.performance.memory;
                        return {
                            used: Math.round(mem.usedJSHeapSize / 1024 / 1024),
                            total: Math.round(mem.totalJSHeapSize / 1024 / 1024),
                            limit: Math.round(mem.jsHeapSizeLimit / 1024 / 1024)
                        };
                    });
                    
                    const passed = memory.used < 100; // 100MB threshold
                    
                    return {
                        passed: passed,
                        message: `Memory: ${memory.used}MB / ${memory.total}MB`,
                        metrics: memory
                    };
                }
            },
            {
                name: 'Frame Rate',
                async validate(validator) {
                    // Measure FPS during pan
                    const fps = await validator.page.evaluate(async () => {
                        let frameCount = 0;
                        let lastTime = performance.now();
                        const fpsValues = [];
                        
                        const measureFPS = () => {
                            const currentTime = performance.now();
                            const delta = currentTime - lastTime;
                            
                            if (delta >= 1000) {
                                fpsValues.push(frameCount);
                                frameCount = 0;
                                lastTime = currentTime;
                            }
                            
                            frameCount++;
                            
                            if (fpsValues.length < 3) {
                                requestAnimationFrame(measureFPS);
                            }
                        };
                        
                        requestAnimationFrame(measureFPS);
                        
                        // Pan the map
                        let map = window.map || window._map || window.leafletMap;
                        if (!map) {
                            map = Object.values(window).find(val => 
                                val && val._container && val._container.classList?.contains('leaflet-container')
                            );
                        }
                        
                        if (map) {
                            const center = map.getCenter();
                            for (let i = 0; i < 10; i++) {
                                map.panBy([50, 0], { animate: true });
                                await new Promise(resolve => setTimeout(resolve, 100));
                            }
                        }
                        
                        // Wait for measurement
                        await new Promise(resolve => setTimeout(resolve, 3500));
                        
                        return fpsValues.length > 0 ? 
                            Math.round(fpsValues.reduce((a, b) => a + b) / fpsValues.length) : 0;
                    });
                    
                    const passed = fps >= 30; // 30 FPS threshold
                    
                    return {
                        passed: passed,
                        message: `Average FPS: ${fps}`,
                        metrics: { fps }
                    };
                }
            }
        ]
    }
};

/**
 * Run all test scenarios
 */
export async function runAllScenarios(options = {}) {
    const validator = new MapValidator(options);
    await validator.init();
    
    const results = {};
    
    for (const [key, scenario] of Object.entries(testScenarios)) {
        console.log(`\n🧪 Testing: ${scenario.name}\n`);
        
        try {
            await validator.loadMap(scenario.path);
            
            const scenarioResults = [];
            
            for (const test of scenario.tests) {
                console.log(`  Running: ${test.name}...`);
                
                try {
                    const result = await test.validate(validator);
                    scenarioResults.push({
                        name: test.name,
                        ...result
                    });
                    
                    console.log(`    ${result.passed ? '✅' : '❌'} ${result.message}`);
                    
                    if (result.metrics) {
                        console.log(`    📊 Metrics:`, result.metrics);
                    }
                } catch (error) {
                    scenarioResults.push({
                        name: test.name,
                        passed: false,
                        message: `Error: ${error.message}`
                    });
                    
                    console.log(`    ❌ Error: ${error.message}`);
                }
            }
            
            results[key] = {
                scenario: scenario.name,
                path: scenario.path,
                tests: scenarioResults,
                passed: scenarioResults.every(r => r.passed)
            };
            
            // Take screenshot after scenario
            await validator.screenshot(`${key}-complete`);
            
        } catch (error) {
            console.error(`  ❌ Failed to load scenario: ${error.message}`);
            results[key] = {
                scenario: scenario.name,
                path: scenario.path,
                error: error.message,
                passed: false
            };
        }
    }
    
    await validator.close();
    
    return results;
}

// Export individual scenarios for selective testing
export default testScenarios;