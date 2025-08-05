/**
 * App Events Module
 * Handles inter-module communication and event coordination
 */

export class AppEventManager {
    constructor(services) {
        this.services = services;
        this.eventHandlers = new Map();
        this.isSetup = false;
        
        this.setupEventHandlers();
    }

    /**
     * Setup event handlers between modules
     */
    setupEventHandlers() {
        if (this.isSetup) {
            console.warn('AppEventManager: Already setup');
            return;
        }
        
        console.log('AppEventManager: Setting up inter-module communication...');
        
        // UI State → Map Controller events
        this.setupUIStateEvents();
        
        // Map Controller → App events
        this.setupMapControllerEvents();
        
        // Spot Manager events
        this.setupSpotManagerEvents();
        
        // Weather Service events
        this.setupWeatherServiceEvents();
        
        this.isSetup = true;
        console.log('AppEventManager: Event handlers setup complete');
    }

    /**
     * Setup UI State events
     * @private
     */
    setupUIStateEvents() {
        if (!this.services.uiState || !this.services.mapController) {
            console.warn('AppEventManager: Missing uiState or mapController');
            return;
        }
        
        // Day changed event
        this.services.uiState.on('dayChanged', (e) => {
            const { dayIndex, weatherData } = e.detail;
            console.log('AppEventManager: Day changed to index', dayIndex);
            
            this.services.mapController.updateWeatherMarkers(
                weatherData, 
                dayIndex, 
                this.services.uiState.showOnlyDry
            );
            
            // Emit app-level event
            this.emit('dayChanged', { dayIndex, weatherData });
        });

        // Filter changed event
        this.services.uiState.on('filterChanged', (e) => {
            const { showOnlyDry } = e.detail;
            console.log('AppEventManager: Filter changed, showOnlyDry:', showOnlyDry);
            
            const currentData = this.services.uiState.getCurrentDayData();
            if (currentData) {
                this.services.mapController.updateWeatherMarkers(
                    currentData, 
                    this.services.uiState.currentDayIndex, 
                    showOnlyDry
                );
            }
            
            // Emit app-level event
            this.emit('filterChanged', { showOnlyDry });
        });
        
        // Weather data updated event
        this.services.uiState.on('weatherDataUpdated', (e) => {
            console.log('AppEventManager: Weather data updated');
            this.emit('weatherDataUpdated', e.detail);
        });
    }

    /**
     * Setup Map Controller events
     * @private
     */
    setupMapControllerEvents() {
        if (!this.services.mapController) {
            console.warn('AppEventManager: Missing mapController');
            return;
        }
        
        // Spot location selected event
        this.services.mapController.on('spotLocationSelected', (e) => {
            console.log('AppEventManager: Spot location selected', e.detail);
            this.emit('spotLocationSelected', e.detail);
        });

        // Custom spot clicked event
        this.services.mapController.on('customSpotClicked', (e) => {
            console.log('AppEventManager: Custom spot clicked', e.detail);
            this.emit('customSpotClicked', e.detail);
        });
        
        // Long press event (mobile)
        this.services.mapController.on('longPress', (e) => {
            console.log('AppEventManager: Long press detected', e.detail);
            this.emit('longPress', e.detail);
        });
    }

    /**
     * Setup Spot Manager events
     * @private
     */
    setupSpotManagerEvents() {
        if (!this.services.spotManager) {
            console.warn('AppEventManager: Missing spotManager');
            return;
        }
        
        // Spot added event
        this.services.spotManager.on('spotAdded', (e) => {
            console.log('AppEventManager: Spot added', e.detail);
            
            // Update map with new spots
            const allSpots = this.services.spotManager.getAllSpots();
            this.services.mapController.updateCustomSpots(allSpots);
            
            this.emit('spotAdded', e.detail);
        });

        // Spot removed event
        this.services.spotManager.on('spotRemoved', (e) => {
            console.log('AppEventManager: Spot removed', e.detail);
            
            // Update map with remaining spots
            const allSpots = this.services.spotManager.getAllSpots();
            this.services.mapController.updateCustomSpots(allSpots);
            
            this.emit('spotRemoved', e.detail);
        });
        
        // Spots imported event
        this.services.spotManager.on('spotsImported', (e) => {
            console.log('AppEventManager: Spots imported', e.detail);
            
            // Update map with all spots
            const allSpots = this.services.spotManager.getAllSpots();
            this.services.mapController.updateCustomSpots(allSpots);
            
            this.emit('spotsImported', e.detail);
        });
    }

    /**
     * Setup Weather Service events
     * @private
     */
    setupWeatherServiceEvents() {
        if (!this.services.weatherService) {
            console.warn('AppEventManager: Missing weatherService');
            return;
        }
        
        // Weather data loaded event
        this.services.weatherService.on('dataLoaded', (e) => {
            console.log('AppEventManager: Weather data loaded');
            this.emit('weatherDataLoaded', e.detail);
        });

        // Weather data error event
        this.services.weatherService.on('dataError', (e) => {
            console.warn('AppEventManager: Weather data error', e.detail);
            this.emit('weatherDataError', e.detail);
        });
    }

    /**
     * Setup periodic data updates
     * @param {Object} config - Update configuration
     */
    setupPeriodicUpdates(config) {
        if (!config.features.backgroundSync) {
            console.log('AppEventManager: Background sync disabled');
            return;
        }
        
        console.log('AppEventManager: Setting up periodic updates...');
        
        // Update weather data every hour when online
        const updateInterval = setInterval(async () => {
            if (!navigator.onLine) {
                console.log('AppEventManager: Offline, skipping update');
                return;
            }
            
            try {
                console.log('AppEventManager: Updating weather data...');
                
                const weatherData = await this.services.weatherService.fetchWeatherData(config.cities);
                this.services.uiState.updateWeatherData(weatherData);
                
                // Update current view
                const currentData = this.services.uiState.getCurrentDayData();
                if (currentData) {
                    this.services.mapController.updateWeatherMarkers(
                        currentData,
                        this.services.uiState.currentDayIndex,
                        this.services.uiState.showOnlyDry
                    );
                }
                
                this.emit('periodicUpdateComplete', { 
                    timestamp: Date.now(), 
                    recordCount: weatherData?.length || 0 
                });
                
            } catch (error) {
                console.warn('AppEventManager: Periodic update failed:', error);
                this.emit('periodicUpdateError', { error: error.message });
            }
        }, config.uiOptions.updateInterval);
        
        // Store interval ID for cleanup
        this.updateInterval = updateInterval;
    }

    /**
     * Handle city selection event
     * @param {Object} city - Selected city
     * @param {number} dayIndex - Day index
     */
    handleCitySelection(city, dayIndex) {
        console.log('AppEventManager: City selected:', city.nom, 'day:', dayIndex);
        
        // Center map on city
        this.services.mapController.centerOn(city.lat, city.lon, 10);
        
        // Update UI state if needed
        if (this.services.uiState.currentDayIndex !== dayIndex) {
            this.services.uiState.setCurrentDay(dayIndex);
        }
        
        this.emit('citySelected', { city, dayIndex });
    }

    /**
     * Handle activity center request
     * @param {string} activityName - Activity name to center on
     */
    handleActivityCenter(activityName, activities) {
        const activity = activities.find(a => a.nom === activityName);
        if (activity) {
            console.log('AppEventManager: Centering on activity:', activityName);
            this.services.mapController.centerOn(activity.lat, activity.lon, 12);
            this.emit('activityCentered', { activity });
        }
    }

    /**
     * Handle route addition
     * @param {Object} activity - Activity to add to route
     */
    handleAddToRoute(activity) {
        console.log('AppEventManager: Adding to route:', activity.nom);
        // Route functionality would be implemented here
        this.emit('activityAddedToRoute', { activity });
        
        // Show notification
        if (this.services.uiState) {
            this.services.uiState.showNotification(
                `${activity.nom} ajouté à votre route!`,
                'success'
            );
        }
    }

    // ===== EVENT SYSTEM =====

    /**
     * Simple event emitter
     * @param {string} event - Event name
     * @param {Object} data - Event data
     */
    emit(event, data = {}) {
        const customEvent = new CustomEvent(`app:${event}`, {
            detail: { ...data, timestamp: Date.now() }
        });
        document.dispatchEvent(customEvent);
    }

    /**
     * Listen to app events
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    on(event, handler) {
        document.addEventListener(`app:${event}`, handler);
        
        // Store handler for cleanup
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Remove event listener
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    off(event, handler) {
        document.removeEventListener(`app:${event}`, handler);
        
        // Remove from stored handlers
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Cleanup event manager
     */
    destroy() {
        console.log('AppEventManager: Cleaning up...');
        
        // Clear periodic update interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        // Remove all event listeners
        this.eventHandlers.forEach((handlers, event) => {
            handlers.forEach(handler => {
                document.removeEventListener(`app:${event}`, handler);
            });
        });
        
        this.eventHandlers.clear();
        this.isSetup = false;
        
        console.log('AppEventManager: Cleanup complete');
    }
}

export default AppEventManager;