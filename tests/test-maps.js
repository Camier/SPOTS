const puppeteer = require('puppeteer');

async function testMaps() {
    const browser = await puppeteer.launch({ headless: false });
    
    try {
        // Test debug map
        console.log('Testing debug map...');
        const debugPage = await browser.newPage();
        await debugPage.goto('http://localhost:8085/debug-map.html');
        await debugPage.waitForTimeout(3000);
        
        const debugStatus = await debugPage.$eval('#status', el => el.textContent);
        console.log('Debug map status:', debugStatus);
        
        // Test secure map
        console.log('\nTesting secure map...');
        const securePage = await browser.newPage();
        await securePage.goto('http://localhost:8085/enhanced-map-secure.html');
        await securePage.waitForTimeout(3000);
        
        // Check if markers are present - secure map uses spotsLayer
        const secureMarkers = await securePage.evaluate(() => {
            // The secure map doesn't expose variables globally
            // Check if the map has loaded by looking for markers on the page
            const markers = document.querySelectorAll('.leaflet-marker-icon');
            const clusters = document.querySelectorAll('.leaflet-marker-cluster');
            return `Markers: ${markers.length}, Clusters: ${clusters.length}`;
        });
        console.log('Secure map markers:', secureMarkers);
        
        // Test IGN map
        console.log('\nTesting IGN map...');
        const ignPage = await browser.newPage();
        await ignPage.goto('http://localhost:8085/enhanced-map-ign.html');
        await ignPage.waitForTimeout(3000);
        
        const ignMarkers = await ignPage.evaluate(() => {
            // The IGN map also doesn't expose variables globally
            // Check for actual DOM elements
            const markers = document.querySelectorAll('.leaflet-marker-icon');
            const clusters = document.querySelectorAll('.leaflet-marker-cluster');
            return `Markers: ${markers.length}, Clusters: ${clusters.length}`;
        });
        console.log('IGN map markers:', ignMarkers);
        
        console.log('\nKeeping browser open for 10 seconds to inspect...');
        await debugPage.waitForTimeout(10000);
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

testMaps();