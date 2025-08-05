/**
 * Refactored Weather App - Main Coordinator
 * Orchestrates modules and provides public API
 */

import AppInitializer from './app-initialization.js';
import AppEventManager from './app-events.js';
import AppUIManager from './app-ui-management.js';
import MapController from './map-controller-refactored.js';

export class WeatherApp {
    constructor(config = {}) {
        this.config = this.mergeDefaultConfig(config);
        
        // Core state
        this.isInitialized = false;
        this.isWeatherDataLoaded = false;
        this.initializationPromise = null;
        
        // Module instances
        this.appInitializer = null;
        this.eventManager = null;
        this.uiManager = null;
        this.services = {};
        
        // Start initialization asynchronously (but don't block constructor)
        this.initializationPromise = this.initialize().catch(error => {
            console.error('WeatherApp: Initialization failed:', error);
            throw error;
        });
    }

    /**
     * Merge user config with defaults
     * @private
     */
    mergeDefaultConfig(userConfig) {
        const defaultConfig = {
            // Cities for weather data - Comprehensive French locations with diverse microclimates
            cities: [
                // Mediterranean Coast - Hot summers, mild winters
                { nom: 'Nice', lat: 43.7102, lon: 7.2620, region: 'PACA', climat: 'méditerranéen', altitude: 56 },
                { nom: 'Marseille', lat: 43.2965, lon: 5.3698, region: 'PACA', climat: 'méditerranéen', altitude: 12 },
                { nom: 'Montpellier', lat: 43.6109, lon: 3.8763, region: 'Occitanie', climat: 'méditerranéen', altitude: 27 },
                { nom: 'Perpignan', lat: 42.6886, lon: 2.8946, region: 'Occitanie', climat: 'méditerranéen', altitude: 42 },
                { nom: 'Toulon', lat: 43.1242, lon: 5.9280, region: 'PACA', climat: 'méditerranéen', altitude: 10 },
                
                // Atlantic Coast - Mild oceanic climate
                { nom: 'Bordeaux', lat: 44.8378, lon: -0.5792, region: 'Nouvelle-Aquitaine', climat: 'océanique', altitude: 4 },
                { nom: 'La Rochelle', lat: 46.1603, lon: -1.1511, region: 'Nouvelle-Aquitaine', climat: 'océanique', altitude: 28 },
                { nom: 'Biarritz', lat: 43.4832, lon: -1.5586, region: 'Nouvelle-Aquitaine', climat: 'océanique', altitude: 19 },
                { nom: 'Nantes', lat: 47.2184, lon: -1.5536, region: 'Pays de la Loire', climat: 'océanique', altitude: 8 },
                
                // Southwest - Diverse continental/oceanic mix
                { nom: 'Toulouse', lat: 43.6047, lon: 1.4442, region: 'Occitanie', climat: 'tempéré', altitude: 146 },
                { nom: 'Pau', lat: 43.2951, lon: -0.3707, region: 'Nouvelle-Aquitaine', climat: 'tempéré', altitude: 207 },
                { nom: 'Tarbes', lat: 43.2330, lon: 0.0780, region: 'Occitanie', climat: 'tempéré', altitude: 304 },
                
                // Mountain Areas - Alpine climate
                { nom: 'Grenoble', lat: 45.1885, lon: 5.7245, region: 'Auvergne-Rhône-Alpes', climat: 'montagnard', altitude: 214 },
                { nom: 'Annecy', lat: 45.8992, lon: 6.1294, region: 'Auvergne-Rhône-Alpes', climat: 'montagnard', altitude: 448 },
                { nom: 'Chambéry', lat: 45.5646, lon: 5.9178, region: 'Auvergne-Rhône-Alpes', climat: 'montagnard', altitude: 270 },
                { nom: 'Gap', lat: 44.5596, lon: 6.0821, region: 'PACA', climat: 'montagnard', altitude: 735 },
                
                // Central France - Continental climate
                { nom: 'Lyon', lat: 45.7640, lon: 4.8357, region: 'Auvergne-Rhône-Alpes', climat: 'semi-continental', altitude: 173 },
                { nom: 'Clermont-Ferrand', lat: 45.7797, lon: 3.0863, region: 'Auvergne-Rhône-Alpes', climat: 'semi-continental', altitude: 396 },
                { nom: 'Limoges', lat: 45.8336, lon: 1.2611, region: 'Nouvelle-Aquitaine', climat: 'océanique dégradé', altitude: 209 },
                { nom: 'Poitiers', lat: 46.5802, lon: 0.3404, region: 'Nouvelle-Aquitaine', climat: 'océanique dégradé', altitude: 116 },
                
                // Corsica - Mediterranean island climate
                { nom: 'Ajaccio', lat: 41.9198, lon: 8.7386, region: 'Corse', climat: 'méditerranéen insulaire', altitude: 2 },
                { nom: 'Bastia', lat: 42.7028, lon: 9.4502, region: 'Corse', climat: 'méditerranéen insulaire', altitude: 16 },
                
                // Unique microclimates
                { nom: 'Carcassonne', lat: 43.2130, lon: 2.3491, region: 'Occitanie', climat: 'méditerranéen continental', altitude: 110 },
                { nom: 'Albi', lat: 43.9297, lon: 2.1480, region: 'Occitanie', climat: 'tempéré continental', altitude: 174 },
                { nom: 'Cahors', lat: 44.4479, lon: 1.4399, region: 'Occitanie', climat: 'tempéré océanique', altitude: 135 }
            ],
            
            // Activities for map display - Comprehensive French outdoor activities
            activities: [
                // BEACHES & COASTAL ACTIVITIES - Mediterranean & Atlantic
                { nom: 'Plage des Catalans', type: 'plage', lat: 43.2885, lon: 5.3542, description: 'Belle plage urbaine à Marseille avec vue sur les îles', region: 'PACA', saison: 'été', niveau: 'facile' },
                { nom: 'Plage de Pampelonne', type: 'plage', lat: 43.2380, lon: 6.6790, description: 'Plage mythique de Saint-Tropez, sable fin et eaux turquoise', region: 'PACA', saison: 'été', niveau: 'facile' },
                { nom: 'Dune du Pilat', type: 'randonnee', lat: 44.5894, lon: -1.2156, description: 'Plus haute dune d Europe, panorama exceptionnel sur l océan', region: 'Nouvelle-Aquitaine', saison: 'toute année', niveau: 'modéré' },
                { nom: 'Presqu île de Crozon', type: 'randonnee', lat: 48.2447, lon: -4.4997, description: 'Côte sauvage bretonne, falaises et plages préservées', region: 'Bretagne', saison: 'printemps-automne', niveau: 'modéré' },
                { nom: 'Plage de Palombaggia', type: 'plage', lat: 41.5994, lon: 9.3644, description: 'Plage paradisiaque de Corse, sable blanc et pins parasols', region: 'Corse', saison: 'été', niveau: 'facile' },
                
                // MOUNTAIN HIKING & ALPINE ACTIVITIES
                { nom: 'Mont-Blanc par TMB', type: 'randonnee', lat: 45.8326, lon: 6.8652, description: 'Tour du Mont-Blanc, trek mythique des Alpes (170km)', region: 'Auvergne-Rhône-Alpes', saison: 'été', niveau: 'difficile' },
                { nom: 'Sentier des Calanques', type: 'randonnee', lat: 43.2090, lon: 5.4490, description: 'Randonnée spectaculaire entre falaises et criques turquoise', region: 'PACA', saison: 'printemps-automne', niveau: 'modéré' },
                { nom: 'Cirque de Gavarnie', type: 'randonnee', lat: 42.7414, lon: -0.0111, description: 'Patrimoine UNESCO, cirque glaciaire et cascade de 422m', region: 'Occitanie', saison: 'été', niveau: 'modéré' },
                { nom: 'Lac d Annecy', type: 'randonnee', lat: 45.8627, lon: 6.1604, description: 'Tour du lac alpin le plus pur d Europe, 42km de sentiers', region: 'Auvergne-Rhône-Alpes', saison: 'toute année', niveau: 'facile' },
                { nom: 'Massif du Vercors', type: 'randonnee', lat: 45.0667, lon: 5.4500, description: 'Plateaux calcaires, gorges et forêts, territoire de résistance', region: 'Auvergne-Rhône-Alpes', saison: 'toute année', niveau: 'modéré' },
                { nom: 'Aiguille du Midi', type: 'randonnee', lat: 45.8477, lon: 6.8875, description: 'Téléphérique vers 3842m, vue panoramique sur les Alpes', region: 'Auvergne-Rhône-Alpes', saison: 'été', niveau: 'difficile' },
                { nom: 'GR20 Corse', type: 'randonnee', lat: 42.1500, lon: 9.0000, description: 'Randonnée la plus difficile d Europe, traversée de la Corse', region: 'Corse', saison: 'été', niveau: 'très difficile' },
                
                // CYCLING & BIKE ROUTES
                { nom: 'Canal du Midi', type: 'velo', lat: 43.6047, lon: 1.4442, description: 'Piste cyclable historique UNESCO, 240km de Toulouse à Sète', region: 'Occitanie', saison: 'toute année', niveau: 'facile' },
                { nom: 'Loire à Vélo', type: 'velo', lat: 47.2639, lon: 1.5250, description: 'EuroVelo 6, châteaux de la Loire sur 900km aménagés', region: 'Centre-Val de Loire', saison: 'toute année', niveau: 'facile' },
                { nom: 'Via Rhôna', type: 'velo', lat: 46.2050, lon: 4.8350, description: 'Du lac Léman à la Méditerranée, 815km le long du Rhône', region: 'Multiple', saison: 'toute année', niveau: 'facile' },
                { nom: 'Alpe d Huez', type: 'velo', lat: 45.0914, lon: 6.0669, description: 'Montée mythique du Tour de France, 21 lacets, 13.8km', region: 'Auvergne-Rhône-Alpes', saison: 'été', niveau: 'très difficile' },
                { nom: 'Col du Tourmalet', type: 'velo', lat: 42.9067, lon: 0.1436, description: 'Col pyrénéen légendaire, 2115m d altitude, étape reine', region: 'Occitanie', saison: 'été', niveau: 'très difficile' },
                
                // WATER SPORTS & AQUATIC ACTIVITIES
                { nom: 'Gorges du Verdon', type: 'kayak', lat: 43.7642, lon: 6.3369, description: 'Grand Canyon européen, kayak et escalade dans les gorges', region: 'PACA', saison: 'printemps-automne', niveau: 'modéré' },
                { nom: 'Bassin d Arcachon', type: 'kayak', lat: 44.6667, lon: -1.1667, description: 'Kayak entre ostréiculture et Banc d Arguin, biodiversité unique', region: 'Nouvelle-Aquitaine', saison: 'toute année', niveau: 'facile' },
                { nom: 'Ardèche en canoë', type: 'kayak', lat: 44.3167, lon: 4.2833, description: 'Descente de l Ardèche, passage sous le Pont d Arc', region: 'Auvergne-Rhône-Alpes', saison: 'printemps-automne', niveau: 'modéré' },
                { nom: 'Lac de Serre-Ponçon', type: 'voile', lat: 44.5000, lon: 6.3500, description: 'Plus grand lac artificiel d Europe, voile et sports nautiques', region: 'PACA', saison: 'été', niveau: 'modéré' },
                
                // CULTURAL & HERITAGE SITES
                { nom: 'Cité de Carcassonne', type: 'patrimoine', lat: 43.2130, lon: 2.3491, description: 'Cité médiévale fortifiée UNESCO, 2500 ans d histoire', region: 'Occitanie', saison: 'toute année', niveau: 'facile' },
                { nom: 'Château de Chambord', type: 'patrimoine', lat: 47.6167, lon: 1.5167, description: 'Chef-d œuvre Renaissance, escalier double révolution', region: 'Centre-Val de Loire', saison: 'toute année', niveau: 'facile' },
                { nom: 'Rocamadour', type: 'patrimoine', lat: 44.8000, lon: 1.6167, description: 'Cité sacrée accrochée à la falaise, pèlerinage millénaire', region: 'Occitanie', saison: 'toute année', niveau: 'modéré' },
                { nom: 'Château des Papes', type: 'patrimoine', lat: 44.0833, lon: 4.8000, description: 'Palais des Papes d Avignon, patrimoine gothique exceptionnel', region: 'PACA', saison: 'toute année', niveau: 'facile' },
                
                // NATURAL PARKS & WILDLIFE
                { nom: 'Parc National des Écrins', type: 'randonnee', lat: 44.9167, lon: 6.2333, description: '100 sommets de plus de 3000m, glaciers et faune alpine', region: 'Auvergne-Rhône-Alpes', saison: 'été', niveau: 'difficile' },
                { nom: 'Camargue Sauvage', type: 'observation', lat: 43.5500, lon: 4.3667, description: 'Delta du Rhône, flamants roses et chevaux blancs', region: 'PACA', saison: 'toute année', niveau: 'facile' },
                { nom: 'Parc des Volcans d Auvergne', type: 'randonnee', lat: 45.5833, lon: 2.8333, description: 'Volcans endormis, lacs de cratère et nature préservée', region: 'Auvergne-Rhône-Alpes', saison: 'toute année', niveau: 'modéré' },
                { nom: 'Forêt de Brocéliande', type: 'randonnee', lat: 48.0167, lon: -2.2833, description: 'Forêt légendaire arthurienne, chênes millénaires et mégalithes', region: 'Bretagne', saison: 'toute année', niveau: 'facile' },
                
                // THERMAL SPRINGS & WELLNESS
                { nom: 'Thermes de Bagnères-de-Luchon', type: 'thermes', lat: 42.7889, lon: 0.5944, description: 'Station thermale pyrénéenne, eaux sulfureuses et montagne', region: 'Occitanie', saison: 'toute année', niveau: 'facile' },
                { nom: 'Thermes d Aix-les-Bains', type: 'thermes', lat: 45.6886, lon: 5.9158, description: 'Thermalisme thermal au bord du lac du Bourget', region: 'Auvergne-Rhône-Alpes', saison: 'toute année', niveau: 'facile' },
                { nom: 'Vals-les-Bains', type: 'thermes', lat: 44.6667, lon: 4.3667, description: 'Source volcanique d Ardèche, eaux bicarbonatées', region: 'Auvergne-Rhône-Alpes', saison: 'toute année', niveau: 'facile' },
                
                // WINTER SPORTS
                { nom: 'Chamonix Mont-Blanc', type: 'ski', lat: 45.9237, lon: 6.8694, description: 'Capitale mondiale de l alpinisme, domaine skiable mythique', region: 'Auvergne-Rhône-Alpes', saison: 'hiver', niveau: 'difficile' },
                { nom: 'Val d Isère', type: 'ski', lat: 45.4486, lon: 7.0014, description: 'Espace Killy, ski de haute altitude et hors-piste', region: 'Auvergne-Rhône-Alpes', saison: 'hiver', niveau: 'difficile' },
                { nom: 'Font-Romeu', type: 'ski', lat: 42.5000, lon: 2.0333, description: 'Station pyrénéenne ensoleillée, ski de fond et alpin', region: 'Occitanie', saison: 'hiver', niveau: 'modéré' },
                
                // GASTRONOMY & LOCAL EXPERIENCES
                { nom: 'Route des Vins d Alsace', type: 'gastronomie', lat: 48.2000, lon: 7.4500, description: 'Route viticole de 170km, villages pittoresques et grands crus', region: 'Grand Est', saison: 'toute année', niveau: 'facile' },
                { nom: 'Vignobles de Bordeaux', type: 'gastronomie', lat: 44.8378, lon: -0.5792, description: 'Saint-Émilion et Médoc, châteaux viticoles et dégustation', region: 'Nouvelle-Aquitaine', saison: 'toute année', niveau: 'facile' },
                { nom: 'Marchés de Provence', type: 'gastronomie', lat: 43.7102, lon: 7.2620, description: 'Marchés authentiques, produits du terroir et saveurs du Sud', region: 'PACA', saison: 'toute année', niveau: 'facile' }
            ],
            
            // Feature flags
            features: {
                backgroundSync: true,
                offlineMode: true,
                customSpots: true,
                routePlanning: false
            },
            
            // Map options
            mapOptions: {
                center: [43.7, 3.5],
                zoom: 7,
                maxZoom: 18,
                clusterRadius: 50,
                touchOptimized: true
            },
            
            // UI options
            uiOptions: {
                updateInterval: 3600000, // 1 hour
                maxNotifications: 5,
                showWeatherDetails: true
            },
            
            // Weather service options
            weatherOptions: {
                apiTimeout: 10000,
                cacheDuration: 1800000, // 30 minutes
                retryAttempts: 3
            },
            
            // Environment
            environment: 'production',
            debug: false
        };
        
        return this.deepMerge(defaultConfig, userConfig);
    }

    /**
     * Deep merge objects
     * @private
     */
    deepMerge(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (source[key] !== null && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = this.deepMerge(target[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }
        
        return result;
    }

    /**
     * Initialize the application
     * @private
     */
    async initialize() {
        try {
            console.log('WeatherApp: Starting application initialization...');
            
            // Make MapController available to AppInitializer
            window.MapController = MapController;
            
            // Initialize core services
            this.appInitializer = new AppInitializer(this.config);
            this.services = await this.appInitializer.initialize();
            
            // Initialize event management
            this.eventManager = new AppEventManager(this.services);
            this.eventManager.setupPeriodicUpdates(this.config);
            
            // Initialize UI management
            this.uiManager = new AppUIManager(this.services, this.config);
            
            // Setup activities on map
            this.setupActivities();
            
            // Mark as initialized
            this.isInitialized = true;
            
            // Setup global references for backward compatibility
            this.setupGlobalReferences();
            
            console.log('WeatherApp: Application initialization complete');
            
            // Load weather data asynchronously (non-blocking)
            this.loadWeatherDataAsync();
            
        } catch (error) {
            console.error('WeatherApp: Application initialization failed:', error);
            throw error;
        }
    }

    /**
     * Setup activities on map
     * @private
     */
    setupActivities() {
        this.services.mapController.updateActivityMarkers(
            this.config.activities,
            {} // No initial filters
        );
        
        console.log(`WeatherApp: Setup ${this.config.activities.length} activities`);
    }

    /**
     * Load weather data asynchronously
     * @private
     */
    async loadWeatherDataAsync() {
        try {
            console.log('WeatherApp: Loading weather data...');
            
            const weatherData = await this.services.weatherService.fetchWeatherData(this.config.cities);
            this.services.uiState.updateWeatherData(weatherData);
            
            // Update map with weather markers
            const currentData = this.services.uiState.getCurrentDayData();
            if (currentData) {
                this.services.mapController.updateWeatherMarkers(
                    currentData,
                    this.services.uiState.currentDayIndex,
                    this.services.uiState.showOnlyDry
                );
            }
            
            this.isWeatherDataLoaded = true;
            const loadTime = this.appInitializer.getPerformanceMetrics();
            console.log('WeatherApp: Weather data loaded successfully in', 
                Date.now() - loadTime.initStart, 'ms');
            
        } catch (error) {
            console.warn('WeatherApp: Failed to load weather data:', error);
            
            // Try to load cached data
            try {
                const cachedData = await this.services.weatherService.getCachedData();
                if (cachedData && cachedData.length > 0) {
                    console.log('WeatherApp: Using cached weather data');
                    this.services.uiState.updateWeatherData(cachedData);
                    this.isWeatherDataLoaded = true;
                } else {
                    console.warn('WeatherApp: No cached data available - app works in minimal mode');
                }
            } catch (cacheError) {
                console.error('WeatherApp: Failed to load cached data:', cacheError);
            }
        }
    }

    /**
     * Setup global references for backward compatibility
     * @private
     */
    setupGlobalReferences() {
        // Main app reference
        window.weatherApp = this;
        
        // Legacy references
        window.mapController = this.services.mapController;
        window.app = this;
        
        console.log('WeatherApp: Global references established');
    }

    // ===== PUBLIC API METHODS =====

    /**
     * Handle city selection
     * @param {Object} city - Selected city
     * @param {number} dayIndex - Day index
     */
    handleCitySelection(city, dayIndex) {
        if (!this.isInitialized) {
            console.warn('WeatherApp: Not initialized');
            return;
        }
        
        this.eventManager.handleCitySelection(city, dayIndex);
    }

    /**
     * Center on activity
     * @param {string} activityName - Activity name
     */
    centerOnActivity(activityName) {
        if (!this.isInitialized) {
            console.warn('WeatherApp: Not initialized');
            return;
        }
        
        this.eventManager.handleActivityCenter(activityName, this.config.activities);
    }

    /**
     * Add activity to route
     * @param {Object} activity - Activity to add
     */
    addToRoute(activity) {
        if (!this.isInitialized) {
            console.warn('WeatherApp: Not initialized');
            return;
        }
        
        this.eventManager.handleAddToRoute(activity);
    }

    /**
     * Wait for application to be ready
     * @returns {Promise<WeatherApp>} Promise that resolves when app is initialized
     */
    async ready() {
        if (this.initializationPromise) {
            await this.initializationPromise;
        }
        return this;
    }

    /**
     * Get application status
     * @returns {Object} Status information
     */
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            isWeatherDataLoaded: this.isWeatherDataLoaded,
            servicesReady: this.appInitializer?.isReady() || false,
            performanceMetrics: this.appInitializer?.getPerformanceMetrics() || {},
            initializationPromise: this.initializationPromise
        };
    }

    /**
     * Get configuration
     * @returns {Object} Current configuration
     */
    getConfig() {
        return { ...this.config }; // Return copy
    }

    /**
     * Get services (for advanced usage)
     * @returns {Object} Services object
     */
    getServices() {
        return { ...this.services }; // Return copy
    }

    // ===== EVENT SYSTEM =====

    /**
     * Listen to app events
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    on(event, handler) {
        if (this.eventManager) {
            this.eventManager.on(event, handler);
        } else {
            console.warn('WeatherApp: Event manager not initialized');
        }
    }

    /**
     * Remove event listener
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    off(event, handler) {
        if (this.eventManager) {
            this.eventManager.off(event, handler);
        }
    }

    /**
     * Emit app event
     * @param {string} event - Event name
     * @param {Object} data - Event data
     */
    emit(event, data = {}) {
        if (this.eventManager) {
            this.eventManager.emit(event, data);
        }
    }

    // ===== CLEANUP =====

    /**
     * Destroy weather app and cleanup resources
     */
    destroy() {
        console.log('WeatherApp: Cleaning up application...');
        
        // Cleanup modules
        if (this.uiManager) {
            this.uiManager.destroy();
        }
        
        if (this.eventManager) {
            this.eventManager.destroy();
        }
        
        if (this.appInitializer) {
            this.appInitializer.destroy();
        }
        
        // Remove global references
        if (window.weatherApp === this) {
            delete window.weatherApp;
        }
        if (window.app === this) {
            delete window.app;
        }
        
        // Reset state
        this.isInitialized = false;
        this.isWeatherDataLoaded = false;
        this.services = {};
        
        console.log('WeatherApp: Application cleanup complete');
    }
}

export default WeatherApp;