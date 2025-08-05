/**
 * Enhanced Sun & Shadow Calculator with Working IGN Elevation
 * Uses our existing API endpoints for elevation data
 */

// SunCalc is loaded globally via script tag
const SunCalc = window.SunCalc;

export class EnhancedSunShadowCalculator {
    constructor(map, apiBaseUrl = 'http://localhost:8000') {
        this.map = map;
        this.apiBaseUrl = apiBaseUrl;
        this.shadowLayer = L.layerGroup();
        this.terrainLayer = L.layerGroup();
        this.elevationCache = new Map();
        
        // Shadow settings
        this.shadowOpacity = 0.3;
        this.terrainShadowOpacity = 0.5;
        
        // Current state
        this.currentTime = new Date();
        this.isActive = false;
        this.showTerrainShadows = false;
    }

    /**
     * Get elevation from our API
     */
    async getElevation(lat, lng) {
        const cacheKey = `${lat.toFixed(4)}_${lng.toFixed(4)}`;
        
        if (this.elevationCache.has(cacheKey)) {
            return this.elevationCache.get(cacheKey);
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/mapping/elevation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    latitude: lat,
                    longitude: lng
                })
            });

            const data = await response.json();
            const elevation = data.elevation || 0;
            
            this.elevationCache.set(cacheKey, elevation);
            return elevation;
        } catch (error) {
            console.error('Elevation API error:', error);
            return 0;
        }
    }

    /**
     * Calculate terrain shadows using elevation grid
     */
    async calculateTerrainShadows(bounds, sunAltitude, sunAzimuth) {
        if (sunAltitude <= 0) return []; // Sun below horizon
        
        const shadows = [];
        const zoom = this.map.getZoom();
        
        // Adjust grid based on zoom level
        const gridSize = zoom < 12 ? 5 : zoom < 14 ? 10 : 20;
        const latStep = (bounds.getNorth() - bounds.getSouth()) / gridSize;
        const lngStep = (bounds.getEast() - bounds.getWest()) / gridSize;
        
        // Get elevation grid
        const elevationGrid = [];
        for (let i = 0; i <= gridSize; i++) {
            const row = [];
            for (let j = 0; j <= gridSize; j++) {
                const lat = bounds.getSouth() + i * latStep;
                const lng = bounds.getWest() + j * lngStep;
                const elevation = await this.getElevation(lat, lng);
                row.push({ lat, lng, elevation });
            }
            elevationGrid.push(row);
        }

        // Calculate shadows
        const sunAltRad = sunAltitude * Math.PI / 180;
        const sunAzRad = (sunAzimuth - 180) * Math.PI / 180; // Opposite direction for shadows
        
        for (let i = 0; i < gridSize; i++) {
            for (let j = 0; j < gridSize; j++) {
                const point = elevationGrid[i][j];
                
                // Check if this point casts a shadow
                const shadowLength = this.calculateShadowLength(point.elevation, sunAltRad);
                
                if (shadowLength > 10) { // Only show significant shadows
                    // Calculate shadow polygon
                    const shadowEnd = this.projectPoint(
                        point.lat, 
                        point.lng, 
                        shadowLength, 
                        sunAzRad
                    );
                    
                    shadows.push({
                        start: [point.lat, point.lng],
                        end: shadowEnd,
                        elevation: point.elevation,
                        length: shadowLength
                    });
                }
            }
        }
        
        return shadows;
    }

    /**
     * Calculate shadow length based on object height and sun angle
     */
    calculateShadowLength(objectHeight, sunAltitudeRad) {
        if (sunAltitudeRad <= 0) return 0;
        // Assume 10m height difference for terrain features
        const heightDiff = 10;
        return heightDiff / Math.tan(sunAltitudeRad);
    }

    /**
     * Project a point given distance and bearing
     */
    projectPoint(lat, lng, distance, bearing) {
        const R = 6371000; // Earth radius in meters
        const lat1 = lat * Math.PI / 180;
        const lng1 = lng * Math.PI / 180;
        
        const lat2 = Math.asin(
            Math.sin(lat1) * Math.cos(distance / R) +
            Math.cos(lat1) * Math.sin(distance / R) * Math.cos(bearing)
        );
        
        const lng2 = lng1 + Math.atan2(
            Math.sin(bearing) * Math.sin(distance / R) * Math.cos(lat1),
            Math.cos(distance / R) - Math.sin(lat1) * Math.sin(lat2)
        );
        
        return [
            lat2 * 180 / Math.PI,
            lng2 * 180 / Math.PI
        ];
    }

    /**
     * Render terrain shadows on map
     */
    renderTerrainShadows(shadows) {
        this.terrainLayer.clearLayers();
        
        shadows.forEach(shadow => {
            // Create gradient shadow polygon
            const polygon = L.polygon([
                shadow.start,
                [shadow.start[0], shadow.start[1] + 0.0001],
                [shadow.end[0], shadow.end[1] + 0.0001],
                shadow.end
            ], {
                fillColor: '#000033',
                fillOpacity: this.terrainShadowOpacity * (1 - shadow.length / 1000),
                stroke: false,
                interactive: false
            });
            
            this.terrainLayer.addLayer(polygon);
        });
        
        if (!this.map.hasLayer(this.terrainLayer)) {
            this.terrainLayer.addTo(this.map);
        }
    }

    /**
     * Find sun exposure for current view
     */
    async analyzeSunExposure() {
        const bounds = this.map.getBounds();
        const center = bounds.getCenter();
        const results = [];
        
        // Sample points across current view
        const samples = 9; // 3x3 grid
        const latStep = (bounds.getNorth() - bounds.getSouth()) / 3;
        const lngStep = (bounds.getEast() - bounds.getWest()) / 3;
        
        for (let i = 0; i <= 2; i++) {
            for (let j = 0; j <= 2; j++) {
                const lat = bounds.getSouth() + i * latStep + latStep/2;
                const lng = bounds.getWest() + j * lngStep + lngStep/2;
                
                const elevation = await this.getElevation(lat, lng);
                const exposure = await this.calculateDailySunExposure(lat, lng, elevation);
                
                results.push({
                    position: [lat, lng],
                    elevation: elevation,
                    sunHours: exposure.hours,
                    firstSun: exposure.firstSun,
                    lastSun: exposure.lastSun
                });
            }
        }
        
        return results;
    }

    /**
     * Calculate daily sun exposure for a point
     */
    async calculateDailySunExposure(lat, lng, elevation) {
        const times = SunCalc.getTimes(this.currentTime, lat, lng);
        let sunMinutes = 0;
        let firstSun = null;
        let lastSun = null;
        
        // Check every 30 minutes
        const sunrise = times.sunrise.getTime();
        const sunset = times.sunset.getTime();
        
        for (let time = sunrise; time <= sunset; time += 30 * 60000) {
            const checkTime = new Date(time);
            const sunPos = SunCalc.getPosition(checkTime, lat, lng);
            
            if (sunPos.altitude > 0) {
                sunMinutes += 30;
                if (!firstSun) firstSun = checkTime;
                lastSun = checkTime;
            }
        }
        
        return {
            hours: sunMinutes / 60,
            firstSun: firstSun,
            lastSun: lastSun
        };
    }

    /**
     * Create enhanced UI controls
     */
    createControls() {
        const ControlPanel = L.Control.extend({
            options: { position: 'topright' },
            
            onAdd: (map) => {
                const container = L.DomUtil.create('div', 'sun-shadow-enhanced-controls');
                container.innerHTML = `
                    <div style="background: white; padding: 15px; border-radius: 8px; 
                               box-shadow: 0 2px 10px rgba(0,0,0,0.2); min-width: 320px;">
                        <h4 style="margin: 0 0 10px 0;">☀️ Calculateur Soleil/Ombre Pro</h4>
                        
                        <div class="sun-stats" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                            <div style="text-align: center; padding: 5px; background: #f0f0f0; border-radius: 4px;">
                                <div style="font-size: 20px;" id="sun-alt-display">--°</div>
                                <small>Altitude</small>
                            </div>
                            <div style="text-align: center; padding: 5px; background: #f0f0f0; border-radius: 4px;">
                                <div style="font-size: 20px;" id="sun-az-display">--°</div>
                                <small>Azimut</small>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <label>Heure: <span id="time-display">--:--</span></label>
                            <input type="range" id="time-slider-enhanced" 
                                min="0" max="1440" step="5" style="width: 100%;">
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <button onclick="window.enhancedSunCalc.setToNow()" style="width: 100%; padding: 5px;">
                                🕐 Maintenant
                            </button>
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <label>
                                <input type="checkbox" id="terrain-shadows" onchange="window.enhancedSunCalc.toggleTerrainShadows()">
                                Ombres du terrain (élévation IGN)
                            </label>
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <button onclick="window.enhancedSunCalc.analyzeSunExposure()" 
                                style="width: 100%; padding: 5px; background: #3498db; color: white; border: none; border-radius: 4px;">
                                📊 Analyser l'exposition solaire
                            </button>
                        </div>
                        
                        <div id="elevation-info" style="font-size: 12px; color: #666; text-align: center;">
                            Cliquez sur la carte pour l'élévation
                        </div>
                    </div>
                `;
                
                L.DomEvent.disableClickPropagation(container);
                L.DomEvent.disableScrollPropagation(container);
                
                return container;
            }
        });
        
        this.controlPanel = new ControlPanel();
        this.map.addControl(this.controlPanel);
        
        // Set up event handlers
        this.setupEventHandlers();
    }

    /**
     * Set up all event handlers
     */
    setupEventHandlers() {
        // Time slider
        const slider = document.getElementById('time-slider-enhanced');
        slider.addEventListener('input', (e) => {
            const minutes = parseInt(e.target.value);
            this.currentTime.setHours(Math.floor(minutes / 60));
            this.currentTime.setMinutes(minutes % 60);
            this.updateDisplay();
        });
        
        // Map click for elevation
        this.map.on('click', async (e) => {
            const elevation = await this.getElevation(e.latlng.lat, e.latlng.lng);
            document.getElementById('elevation-info').innerHTML = 
                `📍 Élévation: ${elevation.toFixed(0)}m<br>
                <small>${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}</small>`;
        });
        
        // Update on map move
        this.map.on('moveend', () => {
            if (this.showTerrainShadows) {
                this.updateTerrainShadows();
            }
        });
        
        // Make functions globally accessible
        window.enhancedSunCalc = this;
    }

    /**
     * Update all displays
     */
    async updateDisplay() {
        const center = this.map.getCenter();
        const sunPos = SunCalc.getPosition(this.currentTime, center.lat, center.lng);
        
        const altitude = sunPos.altitude * 180 / Math.PI;
        const azimuth = (sunPos.azimuth * 180 / Math.PI + 180) % 360;
        
        // Update displays
        document.getElementById('sun-alt-display').textContent = altitude.toFixed(1) + '°';
        document.getElementById('sun-az-display').textContent = azimuth.toFixed(0) + '°';
        document.getElementById('time-display').textContent = 
            this.currentTime.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        
        // Update basic shadows
        this.updateBasicShadows(altitude, azimuth);
        
        // Update terrain shadows if enabled
        if (this.showTerrainShadows && altitude > 0) {
            await this.updateTerrainShadows();
        }
    }

    /**
     * Update basic object shadows
     */
    updateBasicShadows(altitude, azimuth) {
        this.shadowLayer.clearLayers();
        
        if (altitude <= 0) return;
        
        // Add shadows for any markers on the map
        this.map.eachLayer((layer) => {
            if (layer instanceof L.Marker) {
                const pos = layer.getLatLng();
                const shadowLength = 20 / Math.tan(altitude * Math.PI / 180);
                const shadowBearing = (azimuth + 180) * Math.PI / 180;
                
                const shadowEnd = this.projectPoint(pos.lat, pos.lng, shadowLength, shadowBearing);
                
                const shadow = L.polygon([
                    [pos.lat, pos.lng],
                    [pos.lat + 0.0001, pos.lng],
                    [shadowEnd[0] + 0.0001, shadowEnd[1]],
                    shadowEnd
                ], {
                    fillColor: '#000033',
                    fillOpacity: this.shadowOpacity,
                    stroke: false,
                    interactive: false
                });
                
                this.shadowLayer.addLayer(shadow);
            }
        });
        
        if (!this.map.hasLayer(this.shadowLayer)) {
            this.shadowLayer.addTo(this.map);
        }
    }

    /**
     * Update terrain shadows
     */
    async updateTerrainShadows() {
        const bounds = this.map.getBounds();
        const sunPos = SunCalc.getPosition(this.currentTime, bounds.getCenter().lat, bounds.getCenter().lng);
        
        const altitude = sunPos.altitude * 180 / Math.PI;
        const azimuth = (sunPos.azimuth * 180 / Math.PI + 180) % 360;
        
        const shadows = await this.calculateTerrainShadows(bounds, altitude, azimuth);
        this.renderTerrainShadows(shadows);
    }

    /**
     * Toggle terrain shadows
     */
    toggleTerrainShadows() {
        this.showTerrainShadows = !this.showTerrainShadows;
        document.getElementById('terrain-shadows').checked = this.showTerrainShadows;
        
        if (this.showTerrainShadows) {
            this.updateTerrainShadows();
        } else {
            this.terrainLayer.clearLayers();
        }
    }

    /**
     * Set time to now
     */
    setToNow() {
        this.currentTime = new Date();
        const minutes = this.currentTime.getHours() * 60 + this.currentTime.getMinutes();
        document.getElementById('time-slider-enhanced').value = minutes;
        this.updateDisplay();
    }

    /**
     * Analyze and display sun exposure
     */
    async analyzeSunExposure() {
        const results = await this.analyzeSunExposure();
        
        // Display results as markers
        results.forEach(result => {
            const color = result.sunHours > 10 ? '#FFD700' : 
                         result.sunHours > 6 ? '#FFA500' : '#FF6347';
            
            const marker = L.circleMarker(result.position, {
                radius: 8,
                fillColor: color,
                fillOpacity: 0.7,
                stroke: true,
                weight: 2,
                color: 'white'
            }).addTo(this.map);
            
            marker.bindPopup(`
                <strong>Exposition solaire</strong><br>
                Élévation: ${result.elevation.toFixed(0)}m<br>
                Heures de soleil: ${result.sunHours.toFixed(1)}h<br>
                Premier soleil: ${result.firstSun ? result.firstSun.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'}) : 'N/A'}<br>
                Dernier soleil: ${result.lastSun ? result.lastSun.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'}) : 'N/A'}
            `);
        });
    }

    /**
     * Initialize the calculator
     */
    async init() {
        this.createControls();
        this.setToNow();
        this.updateDisplay();
        return this;
    }

    /**
     * Clean up
     */
    destroy() {
        this.shadowLayer.remove();
        this.terrainLayer.remove();
        if (this.controlPanel) {
            this.map.removeControl(this.controlPanel);
        }
        this.map.off('click');
        this.map.off('moveend');
    }
}

export default EnhancedSunShadowCalculator;