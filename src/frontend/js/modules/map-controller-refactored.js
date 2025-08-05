/**
 * Refactored Map Controller - Core Orchestration
 * Coordinates map modules and provides public API
 */

import MapInitializer from './map-init.js';
import MapInteractions from './map-interactions.js';
import MapVisualization from './map-visualization.js';

export class MapController {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            center: options.center || [43.7, 3.5],
            zoom: options.zoom || 7,
            maxZoom: options.maxZoom || 18,
            clusterRadius: options.clusterRadius || 50,
            touchOptimized: options.touchOptimized !== false,
            ...options
        };
        
        // Core state
        this.isInitialized = false;
        this.weatherConditions = null;
        
        // Module instances
        this.mapInitializer = null;
        this.mapInteractions = null;
        this.mapVisualization = null;
        this.map = null;
        
        this.initialize();
    }

    /**
     * Initialize map controller and modules
     * @private
     */
    initialize() {
        try {
            console.log('MapController: Initializing modules...');
            
            // Initialize map
            this.mapInitializer = new MapInitializer(this.containerId, this.options);
            this.map = this.mapInitializer.initializeMap();
            
            // Initialize weather conditions (passed from main app)
            if (window.WeatherConditions) {
                this.weatherConditions = new window.WeatherConditions();
            }
            
            // Initialize interactions
            this.mapInteractions = new MapInteractions(this.map, this.options);
            
            // Initialize visualization
            this.mapVisualization = new MapVisualization(
                this.map, 
                this.weatherConditions, 
                this.options
            );
            
            // Setup inter-module communication
            this.setupModuleCommunication();
            
            this.isInitialized = true;
            console.log('MapController: Initialization complete');
            
        } catch (error) {
            console.error('MapController: Initialization failed:', error);
            throw error;
        }
    }

    /**
     * Setup communication between modules
     * @private
     */
    setupModuleCommunication() {
        // Store event handlers for cleanup
        this._eventHandlers = [];
        
        // Forward interaction events to main app
        const spotSelectedHandler = (e) => this.emit('spotLocationSelected', e.detail);
        this.mapInteractions.on('spotLocationSelected', spotSelectedHandler);
        this._eventHandlers.push(['spotLocationSelected', spotSelectedHandler, this.mapInteractions]);
        
        const longPressHandler = (e) => this.emit('longPress', e.detail);
        this.mapInteractions.on('longPress', longPressHandler);
        this._eventHandlers.push(['longPress', longPressHandler, this.mapInteractions]);
        
        // Forward visualization events
        const spotClickedHandler = (e) => this.emit('customSpotClicked', e.detail);
        this.mapVisualization.on('customSpotClicked', spotClickedHandler);
        this._eventHandlers.push(['customSpotClicked', spotClickedHandler, this.mapVisualization]);
    }
    
    /**
     * Cleanup event listeners
     * @private
     */
    _cleanupEventListeners() {
        if (this._eventHandlers) {
            this._eventHandlers.forEach(([event, handler, module]) => {
                if (module && module.off) {
                    module.off(event, handler);
                }
            });
            this._eventHandlers = [];
        }
    }

    // ===== PUBLIC API METHODS =====

    /**
     * Update weather markers on map
     * @param {Array} weatherData - Weather data array
     * @param {number} dayIndex - Current day index  
     * @param {boolean} showOnlyDry - Filter for dry conditions
     */
    updateWeatherMarkers(weatherData, dayIndex = 0, showOnlyDry = false) {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return;
        }
        
        this.mapVisualization.updateWeatherMarkers(weatherData, dayIndex, showOnlyDry);
    }

    /**
     * Update activity markers on map
     * @param {Array} activities - Activities array
     * @param {Object} filters - Active filters
     */
    updateActivityMarkers(activities, filters = {}) {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return;
        }
        
        this.mapVisualization.updateActivityMarkers(activities, filters);
    }

    /**
     * Update custom spots on map
     * @param {Array} spots - Custom spots array
     */
    updateCustomSpots(spots) {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return;
        }
        
        this.mapVisualization.updateCustomSpots(spots);
    }

    /**
     * Center map on coordinates
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @param {number} zoom - Zoom level
     */
    centerOn(lat, lng, zoom = null) {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return;
        }
        
        this.mapInteractions.centerOn(lat, lng, zoom);
    }

    /**
     * Fit map to bounds
     * @param {L.LatLngBounds} bounds - Bounds to fit
     * @param {Object} options - Fit options
     */
    fitToBounds(bounds, options = {}) {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return;
        }
        
        this.mapInteractions.fitToBounds(bounds, options);
    }

    /**
     * Fit map to show all custom spots
     */
    fitToCustomSpots() {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return;
        }
        
        this.mapVisualization.fitToCustomSpots();
    }

    /**
     * Enable spot creation mode
     */
    enableSpotCreation() {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return;
        }
        
        this.mapInteractions.enableSpotCreation();
    }

    /**
     * Disable spot creation mode
     */
    disableSpotCreation() {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return;
        }
        
        this.mapInteractions.disableSpotCreation();
    }

    /**
     * Get activity icon for activity type
     * @param {string} type - Activity type
     * @returns {string} Icon emoji
     */
    getActivityIcon(type) {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return '📍';
        }
        
        return this.mapVisualization.getActivityIcon(type);
    }

    /**
     * Get current map view information
     * @returns {Object} Current view info
     */
    getCurrentView() {
        if (!this.isInitialized) {
            console.warn('MapController: Not initialized');
            return null;
        }
        
        return this.mapInteractions.getCurrentView();
    }

    /**
     * Get map instance (for advanced usage)
     * @returns {L.Map} Leaflet map instance
     */
    getMap() {
        return this.map;
    }

    // ===== EVENT SYSTEM =====

    /**
     * Simple event emitter
     * @param {string} event - Event name
     * @param {Object} data - Event data
     */
    emit(event, data = {}) {
        const customEvent = new CustomEvent(`mapController:${event}`, {
            detail: { ...data, timestamp: Date.now() }
        });
        document.dispatchEvent(customEvent);
    }

    /**
     * Listen to map controller events
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    on(event, handler) {
        document.addEventListener(`mapController:${event}`, handler);
    }

    /**
     * Remove event listener
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    off(event, handler) {
        document.removeEventListener(`mapController:${event}`, handler);
    }

    // ===== CLEANUP =====

    /**
     * Destroy map controller and cleanup resources
     */
    destroy() {
        console.log('MapController: Cleaning up...');
        
        // Remove all event listeners
        this._cleanupEventListeners();
        
        // Cleanup modules
        if (this.mapVisualization) {
            this.mapVisualization.destroy();
        }
        
        if (this.mapInteractions) {
            this.mapInteractions.destroy();
        }
        
        if (this.mapInitializer) {
            this.mapInitializer.destroy();
        }
        
        // Reset state
        this.isInitialized = false;
        this.map = null;
        this.weatherConditions = null;
        
        console.log('MapController: Cleanup complete');
    }
}

export default MapController;