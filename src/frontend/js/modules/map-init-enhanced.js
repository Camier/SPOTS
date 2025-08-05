/**
 * Enhanced Map Initialization Module
 * Advanced tile layers, satellite views, and professional map controls
 */

export class MapInitializer {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            center: options.center || [43.6047, 1.4442], // Toulouse center
            zoom: options.zoom || 12,
            maxZoom: options.maxZoom || 20,
            minZoom: options.minZoom || 5,
            preferCanvas: true, // Better performance for many markers
            ...options
        };
        this.map = null;
        this.baseLayers = {};
        this.overlayLayers = {};
    }

    /**
     * Initialize the Leaflet map with enhanced features
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
            attributionControl: false,
            preferCanvas: this.options.preferCanvas,
            worldCopyJump: true // Smooth panning across dateline
        });

        this.setupBaseLayers();
        this.setupOverlayLayers();
        this.setupControls();
        this.setupMapEnhancements();
        
        return this.map;
    }

    /**
     * Setup enhanced base map layers
     * @private
     */
    setupBaseLayers() {
        // High-quality satellite imagery from multiple providers
        
        // ESRI World Imagery (High Resolution Satellite)
        this.baseLayers['Satellite HD'] = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: '© Esri, Maxar, Earthstar Geographics',
                maxZoom: 20,
                maxNativeZoom: 18
            }
        );

        // Mapbox Satellite Streets (Hybrid - Satellite + Labels)
        this.baseLayers['Hybrid'] = L.tileLayer(
            'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
                attribution: '© Mapbox © OpenStreetMap',
                maxZoom: 22,
                tileSize: 512,
                zoomOffset: -1
            }
        );

        // Google Satellite (Alternative high-quality satellite)
        this.baseLayers['Google Satellite'] = L.tileLayer(
            'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
                attribution: '© Google',
                maxZoom: 20,
                subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
            }
        );

        // Google Hybrid (Satellite + Roads/Labels)
        this.baseLayers['Google Hybrid'] = L.tileLayer(
            'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
                attribution: '© Google',
                maxZoom: 20,
                subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
            }
        );

        // Detailed Street Map
        this.baseLayers['Streets Detailed'] = L.tileLayer(
            'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors, HOT',
                maxZoom: 20
            }
        );

        // Terrain/Topographic
        this.baseLayers['Terrain 3D'] = L.tileLayer(
            'https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg', {
                attribution: '© Stamen Design, © OpenStreetMap',
                maxZoom: 18,
                subdomains: 'abcd'
            }
        );

        // Dark Mode Map
        this.baseLayers['Dark Mode'] = L.tileLayer(
            'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
                attribution: '© Stadia Maps, © OpenStreetMap',
                maxZoom: 20
            }
        );

        // Watercolor Artistic
        this.baseLayers['Artistic'] = L.tileLayer(
            'https://stamen-tiles-{s}.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.jpg', {
                attribution: '© Stamen Design, © OpenStreetMap',
                maxZoom: 16,
                subdomains: 'abcd'
            }
        );

        // IGN France (Official French Maps)
        this.baseLayers['IGN Classic'] = L.tileLayer(
            'https://wxs.ign.fr/choisirgeoportail/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg', {
                attribution: '© IGN-F/Geoportail',
                maxZoom: 18
            }
        );

        // Set default to Hybrid view
        this.baseLayers['Hybrid'].addTo(this.map);
    }

    /**
     * Setup overlay layers for additional data
     * @private
     */
    setupOverlayLayers() {
        // Weather radar overlay
        this.overlayLayers['Weather Radar'] = L.tileLayer(
            'https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=YOUR_API_KEY', {
                attribution: '© OpenWeatherMap',
                opacity: 0.6,
                maxZoom: 18
            }
        );

        // Hiking trails overlay
        this.overlayLayers['Hiking Trails'] = L.tileLayer(
            'https://tile.waymarkedtrails.org/hiking/{z}/{x}/{y}.png', {
                attribution: '© Waymarked Trails',
                opacity: 0.8,
                maxZoom: 18
            }
        );

        // Cycling routes overlay
        this.overlayLayers['Cycling Routes'] = L.tileLayer(
            'https://tile.waymarkedtrails.org/cycling/{z}/{x}/{y}.png', {
                attribution: '© Waymarked Trails',
                opacity: 0.8,
                maxZoom: 18
            }
        );
    }

    /**
     * Setup enhanced map controls
     * @private
     */
    setupControls() {
        // Enhanced zoom control with home button
        const zoomHome = L.Control.zoomHome({
            position: 'bottomright',
            zoomHomeTitle: 'Reset view to Toulouse',
            homeCoordinates: this.options.center,
            homeZoom: 12
        });
        this.map.addControl(zoomHome);

        // Layer control with preview
        const layerControl = L.control.layers(this.baseLayers, this.overlayLayers, {
            position: 'topright',
            collapsed: true,
            sortLayers: true
        });
        this.map.addControl(layerControl);

        // Scale control
        L.control.scale({
            position: 'bottomleft',
            metric: true,
            imperial: false,
            maxWidth: 200
        }).addTo(this.map);

        // Fullscreen control
        this.map.addControl(new L.Control.Fullscreen({
            position: 'topleft',
            title: {
                'false': 'View Fullscreen',
                'true': 'Exit Fullscreen'
            }
        }));

        // Coordinate display
        L.control.coordinates({
            position: 'bottomleft',
            decimals: 5,
            decimalSeperator: '.',
            labelTemplateLat: 'Lat: {y}',
            labelTemplateLng: 'Lon: {x}'
        }).addTo(this.map);

        // Minimap
        const miniMapLayer = L.tileLayer(
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                minZoom: 0,
                maxZoom: 13
            }
        );
        
        const miniMap = new L.Control.MiniMap(miniMapLayer, {
            toggleDisplay: true,
            position: 'bottomleft',
            width: 150,
            height: 150,
            zoomLevelOffset: -5
        });
        miniMap.addTo(this.map);
    }

    /**
     * Setup additional map enhancements
     * @private
     */
    setupMapEnhancements() {
        // Add geocoding search control
        const searchControl = L.Control.geocoder({
            defaultMarkGeocode: false,
            placeholder: 'Search for places...',
            errorMessage: 'Nothing found.',
            position: 'topleft',
            collapsed: true
        }).on('markgeocode', (e) => {
            const bbox = e.geocode.bbox;
            const poly = L.polygon([
                bbox.getSouthEast(),
                bbox.getNorthEast(),
                bbox.getNorthWest(),
                bbox.getSouthWest()
            ]);
            this.map.fitBounds(poly.getBounds());
        }).addTo(this.map);

        // Add measurement tool
        const measureControl = new L.Control.Measure({
            position: 'topleft',
            primaryLengthUnit: 'kilometers',
            secondaryLengthUnit: 'meters',
            primaryAreaUnit: 'hectares',
            secondaryAreaUnit: 'sqmeters'
        });
        measureControl.addTo(this.map);

        // Add drawing tools
        const drawnItems = new L.FeatureGroup();
        this.map.addLayer(drawnItems);
        
        const drawControl = new L.Control.Draw({
            position: 'topleft',
            draw: {
                polygon: {
                    shapeOptions: {
                        color: '#3388ff',
                        fillOpacity: 0.4
                    }
                },
                polyline: {
                    shapeOptions: {
                        color: '#ff3333',
                        weight: 4
                    }
                },
                circle: {
                    shapeOptions: {
                        color: '#ff9933',
                        fillOpacity: 0.3
                    }
                },
                rectangle: false,
                circlemarker: false
            },
            edit: {
                featureGroup: drawnItems
            }
        });
        this.map.addControl(drawControl);

        // Handle drawing events
        this.map.on(L.Draw.Event.CREATED, (event) => {
            drawnItems.addLayer(event.layer);
        });

        // Add map hash for URL sharing
        const hash = new L.Hash(this.map);

        // Context menu
        this.map.on('contextmenu', (e) => {
            L.popup()
                .setLatLng(e.latlng)
                .setContent(`
                    <div style="text-align: center;">
                        <strong>Coordinates</strong><br>
                        Lat: ${e.latlng.lat.toFixed(5)}<br>
                        Lon: ${e.latlng.lng.toFixed(5)}<br>
                        <button onclick="navigator.clipboard.writeText('${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}')">
                            Copy Coordinates
                        </button>
                    </div>
                `)
                .openOn(this.map);
        });
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
     * Get overlay layers
     * @returns {Object} Overlay layers object
     */
    getOverlayLayers() {
        return this.overlayLayers;
    }

    /**
     * Switch to satellite view
     */
    switchToSatellite() {
        Object.values(this.baseLayers).forEach(layer => this.map.removeLayer(layer));
        this.baseLayers['Satellite HD'].addTo(this.map);
    }

    /**
     * Switch to hybrid view
     */
    switchToHybrid() {
        Object.values(this.baseLayers).forEach(layer => this.map.removeLayer(layer));
        this.baseLayers['Hybrid'].addTo(this.map);
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
