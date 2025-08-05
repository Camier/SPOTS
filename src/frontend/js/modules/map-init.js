/**
 * Map Initialization Module
 * Handles Leaflet map setup, base layers, and initial configuration
 */

export class MapInitializer {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            center: options.center || [43.7, 3.5],
            zoom: options.zoom || 7,
            maxZoom: options.maxZoom || 18,
            minZoom: options.minZoom || 5,
            ...options
        };
        this.map = null;
        this.baseLayers = {};
    }

    /**
     * Initialize the Leaflet map
     * @returns {L.Map} Initialized map instance
     */
    initializeMap() {
        if (this.map) {
            this.map.remove();
        }

        this.map = L.map(this.containerId, {
            center: this.options.center,
            zoom: this.options.zoom,
            maxZoom: this.options.maxZoom,
            minZoom: this.options.minZoom,
            zoomControl: false,
            attributionControl: false
        });

        this.setupBaseLayers();
        this.setupControls();
        
        return this.map;
    }

    /**
     * Setup base map layers
     * @private
     */
    setupBaseLayers() {
        // OpenStreetMap
        this.baseLayers['OpenStreetMap'] = L.tileLayer(
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }
        );

        // Satellite
        this.baseLayers['Satellite'] = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: '© Esri, Maxar, GeoEye, Earthstar Geographics',
                maxZoom: 18
            }
        );

        // Terrain
        this.baseLayers['Terrain'] = L.tileLayer(
            'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenTopoMap contributors',
                maxZoom: 17
            }
        );

        // Add default layer
        this.baseLayers['OpenStreetMap'].addTo(this.map);
    }

    /**
     * Setup map controls
     * @private
     */
    setupControls() {
        // Custom zoom control position
        L.control.zoom({
            position: 'bottomright'
        }).addTo(this.map);

        // Layer control
        L.control.layers(this.baseLayers, null, {
            position: 'topright'
        }).addTo(this.map);

        // Scale control
        L.control.scale({
            position: 'bottomleft',
            metric: true,
            imperial: false
        }).addTo(this.map);
    }

    /**
     * Get the map instance
     * @returns {L.Map} Map instance
     */
    getMap() {
        return this.map;
    }

    /**
     * Get base layers
     * @returns {Object} Base layers object
     */
    getBaseLayers() {
        return this.baseLayers;
    }

    /**
     * Destroy map instance
     */
    destroy() {
        if (this.map) {
            this.map.remove();
            this.map = null;
        }
    }
}

export default MapInitializer;