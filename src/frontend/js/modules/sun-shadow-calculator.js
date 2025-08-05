/**
 * Sun & Shadow Calculator Module
 * Calculates sun position and shadow effects for outdoor spots
 * Uses SunCalc library with IGN elevation data
 */

// SunCalc is loaded globally via script tag
const SunCalc = window.SunCalc;

export class SunShadowCalculator {
    constructor(map, elevationService) {
        this.map = map;
        this.elevationService = elevationService;
        this.shadowLayer = null;
        this.sunPositionMarker = null;
        this.timeSliderControl = null;
        this.isActive = false;
        this.controlContainer = null;
        
        // Default time settings
        this.currentDate = new Date();
        this.currentTime = new Date();
        
        // Shadow rendering settings
        this.shadowOpacity = 0.4;
        this.shadowColor = '#000033';
        this.sunColor = '#FFD700';
    }

    /**
     * Initialize the sun/shadow calculator
     */
    async init() {
        // Create shadow overlay layer
        this.shadowLayer = L.layerGroup().addTo(this.map);
        
        // Create sun position marker
        this.createSunMarker();
        
        // Add time control UI
        this.createTimeControls();
        
        // Initialize with current time
        this.updateSunPosition();
        
        return this;
    }

    /**
     * Create visual marker for sun position
     */
    createSunMarker() {
        const sunIcon = L.divIcon({
            className: 'sun-position-marker',
            html: `<div style="
                width: 30px;
                height: 30px;
                background: radial-gradient(circle, ${this.sunColor} 0%, rgba(255,215,0,0.3) 70%);
                border-radius: 50%;
                box-shadow: 0 0 20px ${this.sunColor};
                position: relative;
                left: -15px;
                top: -15px;
            ">☀</div>`,
            iconSize: [30, 30]
        });

        this.sunPositionMarker = L.marker([0, 0], { 
            icon: sunIcon,
            interactive: false,
            zIndexOffset: 1000
        });
    }

    /**
     * Create time slider and controls
     */
    createTimeControls() {
        const TimeControl = L.Control.extend({
            options: {
                position: 'topright'
            },

            onAdd: (map) => {
                const container = L.DomUtil.create('div', 'sun-shadow-controls');
                container.innerHTML = `
                    <div style="
                        background: white;
                        padding: 15px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                        min-width: 300px;
                    ">
                        <h4 style="margin: 0 0 10px 0;">☀️ Calculateur Soleil/Ombre</h4>
                        
                        <div class="sun-info" style="margin-bottom: 10px;">
                            <span id="sun-time">--:--</span> | 
                            <span id="sun-altitude">Alt: --°</span> | 
                            <span id="sun-azimuth">Az: --°</span>
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <label>Heure: </label>
                            <input type="range" id="time-slider" 
                                min="0" max="1440" step="5" 
                                style="width: 100%;">
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <label>Date: </label>
                            <input type="date" id="date-picker" 
                                style="width: 100%;">
                        </div>
                        
                        <div style="display: flex; gap: 5px;">
                            <button id="sun-now" class="sun-btn">Maintenant</button>
                            <button id="sun-sunrise" class="sun-btn">Lever</button>
                            <button id="sun-noon" class="sun-btn">Midi</button>
                            <button id="sun-sunset" class="sun-btn">Coucher</button>
                        </div>
                        
                        <div style="margin-top: 10px;">
                            <label>
                                <input type="checkbox" id="show-shadows" checked>
                                Afficher les ombres
                            </label>
                        </div>
                    </div>
                `;

                // Style buttons
                const style = document.createElement('style');
                style.textContent = `
                    .sun-btn {
                        padding: 5px 10px;
                        border: 1px solid #ddd;
                        background: #f5f5f5;
                        border-radius: 4px;
                        cursor: pointer;
                        flex: 1;
                    }
                    .sun-btn:hover {
                        background: #e5e5e5;
                    }
                    .sun-shadow-controls {
                        pointer-events: auto;
                    }
                `;
                document.head.appendChild(style);

                // Prevent map interaction
                L.DomEvent.disableClickPropagation(container);
                L.DomEvent.disableScrollPropagation(container);

                return container;
            }
        });

        this.timeSliderControl = new TimeControl();
        this.map.addControl(this.timeSliderControl);

        // Set up event handlers
        this.setupControlHandlers();
    }

    /**
     * Set up control event handlers
     */
    setupControlHandlers() {
        const timeSlider = document.getElementById('time-slider');
        const datePicker = document.getElementById('date-picker');
        const showShadows = document.getElementById('show-shadows');

        // Time slider
        timeSlider.addEventListener('input', (e) => {
            const minutes = parseInt(e.target.value);
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            
            this.currentTime.setHours(hours);
            this.currentTime.setMinutes(mins);
            this.updateSunPosition();
        });

        // Date picker
        datePicker.value = this.currentDate.toISOString().split('T')[0];
        datePicker.addEventListener('change', (e) => {
            this.currentDate = new Date(e.target.value);
            this.currentTime = new Date(this.currentDate);
            this.updateSunPosition();
        });

        // Quick buttons
        document.getElementById('sun-now').addEventListener('click', () => {
            this.setCurrentTime();
        });

        document.getElementById('sun-sunrise').addEventListener('click', () => {
            this.setSunrise();
        });

        document.getElementById('sun-noon').addEventListener('click', () => {
            this.setSolarNoon();
        });

        document.getElementById('sun-sunset').addEventListener('click', () => {
            this.setSunset();
        });

        // Shadow toggle
        showShadows.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.shadowLayer.addTo(this.map);
            } else {
                this.shadowLayer.remove();
            }
        });

        // Initialize time slider
        const currentMinutes = this.currentTime.getHours() * 60 + this.currentTime.getMinutes();
        timeSlider.value = currentMinutes;
    }

    /**
     * Update sun position and shadows
     */
    updateSunPosition() {
        const center = this.map.getCenter();
        const sunPos = SunCalc.getPosition(this.currentTime, center.lat, center.lng);
        
        // Convert to degrees
        const altitude = sunPos.altitude * 180 / Math.PI;
        const azimuth = (sunPos.azimuth * 180 / Math.PI + 180) % 360;

        // Update info display
        this.updateInfoDisplay(altitude, azimuth);

        // Update sun marker position (visual representation)
        this.updateSunMarker(center, altitude, azimuth);

        // Calculate and render shadows
        if (altitude > 0) { // Sun is above horizon
            this.calculateShadows(center, altitude, azimuth);
        } else {
            this.clearShadows();
        }
    }

    /**
     * Update information display
     */
    updateInfoDisplay(altitude, azimuth) {
        const timeStr = this.currentTime.toLocaleTimeString('fr-FR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        document.getElementById('sun-time').textContent = timeStr;
        document.getElementById('sun-altitude').textContent = `Alt: ${altitude.toFixed(1)}°`;
        document.getElementById('sun-azimuth').textContent = `Az: ${azimuth.toFixed(1)}°`;
    }

    /**
     * Update sun marker position on map
     */
    updateSunMarker(center, altitude, azimuth) {
        if (altitude > 0) {
            // Calculate visual position based on azimuth
            const distance = 0.01; // degrees
            const azimuthRad = (azimuth - 90) * Math.PI / 180;
            
            const sunLat = center.lat + distance * Math.sin(azimuthRad);
            const sunLng = center.lng + distance * Math.cos(azimuthRad);
            
            this.sunPositionMarker.setLatLng([sunLat, sunLng]);
            
            if (!this.map.hasLayer(this.sunPositionMarker)) {
                this.sunPositionMarker.addTo(this.map);
            }
        } else {
            // Sun below horizon
            if (this.map.hasLayer(this.sunPositionMarker)) {
                this.sunPositionMarker.remove();
            }
        }
    }

    /**
     * Calculate and render shadows based on terrain
     */
    async calculateShadows(center, altitude, azimuth) {
        // Clear previous shadows
        this.shadowLayer.clearLayers();

        // Get current map bounds and zoom
        const bounds = this.map.getBounds();
        const zoom = this.map.getZoom();

        // Only calculate shadows at appropriate zoom levels
        if (zoom < 13) {
            return; // Too zoomed out for meaningful shadows
        }

        // Calculate shadow length based on sun altitude
        const shadowLength = this.calculateShadowLength(altitude);
        
        // Shadow direction (opposite of sun)
        const shadowAzimuth = (azimuth + 180) % 360;
        const shadowAzimuthRad = shadowAzimuth * Math.PI / 180;

        // Create shadow polygons for terrain features
        // This is simplified - in production, you'd query elevation data
        this.renderSimplifiedShadows(center, shadowLength, shadowAzimuthRad);
    }

    /**
     * Calculate shadow length based on sun altitude
     */
    calculateShadowLength(altitude) {
        // Simple shadow length calculation
        // tan(altitude) = height / shadow_length
        const altitudeRad = altitude * Math.PI / 180;
        const shadowMultiplier = 1 / Math.tan(altitudeRad);
        
        // Cap shadow length for very low sun
        return Math.min(shadowMultiplier, 10);
    }

    /**
     * Render simplified shadows (without elevation data)
     */
    renderSimplifiedShadows(center, shadowLength, shadowAzimuthRad) {
        // Create a simple shadow gradient overlay
        const shadowPolygon = L.polygon([
            [center.lat - 0.001, center.lng - 0.001],
            [center.lat - 0.001, center.lng + 0.001],
            [center.lat + 0.001, center.lng + 0.001],
            [center.lat + 0.001, center.lng - 0.001]
        ], {
            fillColor: this.shadowColor,
            fillOpacity: this.shadowOpacity * (1 - Math.abs(shadowLength) / 10),
            stroke: false,
            interactive: false
        });

        this.shadowLayer.addLayer(shadowPolygon);
    }

    /**
     * Clear all shadows
     */
    clearShadows() {
        this.shadowLayer.clearLayers();
    }

    /**
     * Set time to current
     */
    setCurrentTime() {
        this.currentTime = new Date();
        this.currentDate = new Date();
        
        const minutes = this.currentTime.getHours() * 60 + this.currentTime.getMinutes();
        document.getElementById('time-slider').value = minutes;
        document.getElementById('date-picker').value = this.currentDate.toISOString().split('T')[0];
        
        this.updateSunPosition();
    }

    /**
     * Set time to sunrise
     */
    setSunrise() {
        const center = this.map.getCenter();
        const times = SunCalc.getTimes(this.currentDate, center.lat, center.lng);
        
        this.currentTime = new Date(times.sunrise);
        const minutes = this.currentTime.getHours() * 60 + this.currentTime.getMinutes();
        document.getElementById('time-slider').value = minutes;
        
        this.updateSunPosition();
    }

    /**
     * Set time to solar noon
     */
    setSolarNoon() {
        const center = this.map.getCenter();
        const times = SunCalc.getTimes(this.currentDate, center.lat, center.lng);
        
        this.currentTime = new Date(times.solarNoon);
        const minutes = this.currentTime.getHours() * 60 + this.currentTime.getMinutes();
        document.getElementById('time-slider').value = minutes;
        
        this.updateSunPosition();
    }

    /**
     * Set time to sunset
     */
    setSunset() {
        const center = this.map.getCenter();
        const times = SunCalc.getTimes(this.currentDate, center.lat, center.lng);
        
        this.currentTime = new Date(times.sunset);
        const minutes = this.currentTime.getHours() * 60 + this.currentTime.getMinutes();
        document.getElementById('time-slider').value = minutes;
        
        this.updateSunPosition();
    }

    /**
     * Toggle calculator visibility
     */
    toggle() {
        this.isActive = !this.isActive;
        
        if (this.isActive) {
            this.activate();
        } else {
            this.deactivate();
        }
        
        return this.isActive;
    }
    
    /**
     * Activate the sun calculator
     */
    activate() {
        this.isActive = true;
        this.shadowLayer.addTo(this.map);
        if (this.timeSliderControl) {
            this.map.addControl(this.timeSliderControl);
        }
        this.updateSunPosition();
    }
    
    /**
     * Deactivate the sun calculator
     */
    deactivate() {
        this.isActive = false;
        this.shadowLayer.remove();
        if (this.map.hasLayer(this.sunPositionMarker)) {
            this.sunPositionMarker.remove();
        }
        if (this.timeSliderControl && this.map._controlCorners) {
            this.map.removeControl(this.timeSliderControl);
        }
    }

    /**
     * Clean up resources
     */
    destroy() {
        if (this.shadowLayer) {
            this.shadowLayer.remove();
        }
        if (this.sunPositionMarker) {
            this.sunPositionMarker.remove();
        }
        if (this.timeSliderControl) {
            this.map.removeControl(this.timeSliderControl);
        }
    }
}

// Export for use in main app
export default SunShadowCalculator;