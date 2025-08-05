/**
 * Map Interactions Module
 * Handles user interactions, events, and mobile optimization
 */

export class MapInteractions {
    constructor(map, options = {}) {
        this.map = map;
        this.options = options;
        this.eventHandlers = new Map();
        this.touchOptimized = options.touchOptimized !== false;
        this.isCreatingSpot = false;
        
        this.setupEventListeners();
        if (this.touchOptimized) {
            this.setupMobileOptimizations();
        }
    }

    /**
     * Setup core map event listeners
     * @private
     */
    setupEventListeners() {
        // Map click for spot creation
        this.map.on('click', (e) => {
            if (this.isCreatingSpot) {
                this.handleSpotLocationSelection(e);
            }
        });

        // Zoom events for performance optimization
        this.map.on('zoomstart', () => {
            this.emit('zoomStart');
        });

        this.map.on('zoomend', () => {
            this.emit('zoomEnd', { zoom: this.map.getZoom() });
        });

        // Move events with debouncing
        let moveTimeout;
        this.map.on('moveend', () => {
            clearTimeout(moveTimeout);
            moveTimeout = setTimeout(() => {
                this.emit('mapMoved', {
                    center: this.map.getCenter(),
                    zoom: this.map.getZoom()
                });
            }, 100);
        });

        // Double click handling
        this.map.on('dblclick', (e) => {
            this.handleDoubleClick(e);
        });
    }

    /**
     * Setup mobile-specific optimizations
     * @private
     */
    setupMobileOptimizations() {
        // Disable map dragging on mobile when over UI elements
        this.map.dragging.disable();
        this.map.touchZoom.disable();
        this.map.doubleClickZoom.disable();
        this.map.scrollWheelZoom.disable();

        // Re-enable based on touch interaction
        this.map.on('focus', () => {
            this.map.dragging.enable();
            this.map.touchZoom.enable();
            this.map.scrollWheelZoom.enable();
        });

        // Touch event optimization
        this.setupTouchEvents();
    }

    /**
     * Setup touch-specific event handling
     * @private
     */
    setupTouchEvents() {
        let touchStartTime = 0;
        let touchStartPos = null;

        this.map.on('touchstart', (e) => {
            touchStartTime = Date.now();
            touchStartPos = e.latlng;
        });

        this.map.on('touchend', (e) => {
            const touchEndTime = Date.now();
            const touchDuration = touchEndTime - touchStartTime;

            // Long press detection (500ms)
            if (touchDuration > 500 && touchStartPos) {
                const distance = this.map.distance(touchStartPos, e.latlng);
                if (distance < 50) { // 50 meters tolerance
                    this.handleLongPress(e);
                }
            }
        });
    }

    /**
     * Handle spot location selection
     * @private
     */
    handleSpotLocationSelection(e) {
        this.emit('spotLocationSelected', {
            latlng: e.latlng,
            lat: e.latlng.lat,
            lng: e.latlng.lng
        });
    }

    /**
     * Handle double click events
     * @private
     */
    handleDoubleClick(e) {
        // Zoom in on double click with smooth animation
        this.map.setView(e.latlng, Math.min(this.map.getZoom() + 2, this.map.getMaxZoom()), {
            animate: true,
            duration: 0.5
        });
    }

    /**
     * Handle long press events (mobile)
     * @private
     */
    handleLongPress(e) {
        this.emit('longPress', {
            latlng: e.latlng,
            lat: e.latlng.lat,
            lng: e.latlng.lng
        });
    }

    /**
     * Enable spot creation mode
     */
    enableSpotCreation() {
        this.isCreatingSpot = true;
        this.map.getContainer().style.cursor = 'crosshair';
        this.emit('spotCreationEnabled');
    }

    /**
     * Disable spot creation mode
     */
    disableSpotCreation() {
        this.isCreatingSpot = false;
        this.map.getContainer().style.cursor = '';
        this.emit('spotCreationDisabled');
    }

    /**
     * Center map on coordinates with animation
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @param {number} zoom - Zoom level
     */
    centerOn(lat, lng, zoom = null) {
        const currentZoom = zoom || this.map.getZoom();
        this.map.setView([lat, lng], currentZoom, {
            animate: true,
            duration: 1.0
        });
    }

    /**
     * Fit map to bounds with padding
     * @param {L.LatLngBounds} bounds - Bounds to fit
     * @param {Object} options - Fit options
     */
    fitToBounds(bounds, options = {}) {
        const defaultOptions = {
            padding: [20, 20],
            animate: true,
            duration: 1.0
        };
        
        this.map.fitBounds(bounds, { ...defaultOptions, ...options });
    }

    /**
     * Get current map view info
     * @returns {Object} Current view information
     */
    getCurrentView() {
        return {
            center: this.map.getCenter(),
            zoom: this.map.getZoom(),
            bounds: this.map.getBounds()
        };
    }

    /**
     * Simple event emitter
     * @param {string} event - Event name
     * @param {Object} data - Event data
     */
    emit(event, data = {}) {
        const customEvent = new CustomEvent(`mapInteractions:${event}`, {
            detail: { ...data, timestamp: Date.now() }
        });
        document.dispatchEvent(customEvent);
    }

    /**
     * Listen to map interaction events
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    on(event, handler) {
        document.addEventListener(`mapInteractions:${event}`, handler);
    }

    /**
     * Remove event listener
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    off(event, handler) {
        document.removeEventListener(`mapInteractions:${event}`, handler);
    }

    /**
     * Cleanup interactions
     */
    destroy() {
        this.map.off();
        this.eventHandlers.clear();
    }
}

export default MapInteractions;