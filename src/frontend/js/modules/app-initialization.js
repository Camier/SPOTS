/**
 * App Initialization Module
 * Handles service setup, error monitoring, and module initialization
 */

export class AppInitializer {
    constructor(config) {
        this.config = config;
        this.performance = {
            initStart: Date.now(),
            weatherLoadTime: null,
            firstPaintTime: null
        };
        
        // Service instances
        this.weatherService = null;
        this.uiState = null;
        this.mapController = null;
        this.spotManager = null;
        this.errorMonitor = null;
        
        this.isInitialized = false;
    }

    /**
     * Initialize all application modules
     * @returns {Object} Initialized services
     */
    async initialize() {
        try {
            console.log('AppInitializer: Starting initialization...');
            
            // Initialize error monitoring first
            this.setupErrorMonitoring();
            
            // Initialize core services
            await this.initializeServices();
            
            // Mark as initialized
            this.isInitialized = true;
            this.performance.firstPaintTime = Date.now();
            
            console.log('AppInitializer: Core initialization complete in', 
                this.performance.firstPaintTime - this.performance.initStart, 'ms');
            
            // Setup global references for backward compatibility
            this.setupGlobalReferences();
            
            return this.getServices();
            
        } catch (error) {
            console.error('AppInitializer: Initialization failed:', error);
            this.handleInitializationError(error);
            throw error;
        }
    }

    /**
     * Initialize error monitoring
     * @private
     */
    setupErrorMonitoring() {
        if (!window.ErrorMonitor) {
            console.warn('AppInitializer: ErrorMonitor not available');
            return;
        }
        
        this.errorMonitor = new window.ErrorMonitor({
            appVersion: '2.0.0',
            environment: this.config.environment || 'production',
            enableConsoleLog: this.config.debug || false
        });
        
        // Global error boundaries
        this.setupGlobalErrorHandlers();
    }

    /**
     * Setup global error handlers
     * @private
     */
    setupGlobalErrorHandlers() {
        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('AppInitializer: Unhandled promise rejection:', event.reason);
            if (this.errorMonitor) {
                this.errorMonitor.logError(event.reason, 'unhandledrejection');
            }
        });

        // Global JavaScript errors
        window.addEventListener('error', (event) => {
            console.error('AppInitializer: Global error:', event.error);
            if (this.errorMonitor) {
                this.errorMonitor.logError(event.error, 'javascript');
            }
        });
    }

    /**
     * Initialize core services
     * @private
     */
    async initializeServices() {
        // Initialize weather service
        if (window.WeatherService) {
            this.weatherService = new window.WeatherService(this.config.weatherOptions);
            console.log('AppInitializer: WeatherService initialized');
        } else {
            throw new Error('WeatherService not available');
        }

        // Initialize UI state manager
        if (window.UIStateManager) {
            this.uiState = new window.UIStateManager(this.weatherService, this.config.uiOptions);
            console.log('AppInitializer: UIStateManager initialized');
        } else {
            throw new Error('UIStateManager not available');
        }

        // Initialize map controller (using refactored version if available)
        const MapControllerClass = window.MapController || window.MapControllerRefactored;
        if (MapControllerClass) {
            this.mapController = new MapControllerClass('map', this.config.mapOptions);
            console.log('AppInitializer: MapController initialized');
        } else {
            throw new Error('MapController not available');
        }

        // Initialize spot manager
        if (window.SpotManager) {
            this.spotManager = new window.SpotManager();
            console.log('AppInitializer: SpotManager initialized');
        } else {
            throw new Error('SpotManager not available');
        }
    }

    /**
     * Setup global references for backward compatibility
     * @private
     */
    setupGlobalReferences() {
        // Make services available globally for popup callbacks and legacy code
        window.appServices = {
            weatherService: this.weatherService,
            uiState: this.uiState,
            mapController: this.mapController,
            spotManager: this.spotManager,
            errorMonitor: this.errorMonitor
        };
        
        // Legacy compatibility
        window.mapController = this.mapController;
    }

    /**
     * Handle initialization errors
     * @private
     */
    handleInitializationError(error) {
        // Show user-friendly error message
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="error-message bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    <h3 class="font-bold">Erreur d'initialisation</h3>
                    <p>L'application n'a pas pu se charger correctement.</p>
                    <details class="mt-2">
                        <summary class="cursor-pointer">Détails techniques</summary>
                        <pre class="mt-2 text-xs bg-red-50 p-2 rounded">${error.message}</pre>
                    </details>
                    <button onclick="location.reload()" 
                            class="mt-3 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                        Recharger la page
                    </button>
                </div>
            `;
            errorContainer.classList.remove('hidden');
        }

        // Log to error monitoring service
        if (this.errorMonitor) {
            this.errorMonitor.logError(error, 'initialization');
        }
    }

    /**
     * Get all initialized services
     * @returns {Object} Services object
     */
    getServices() {
        return {
            weatherService: this.weatherService,
            uiState: this.uiState,
            mapController: this.mapController,
            spotManager: this.spotManager,
            errorMonitor: this.errorMonitor
        };
    }

    /**
     * Get initialization performance metrics
     * @returns {Object} Performance metrics
     */
    getPerformanceMetrics() {
        return {
            ...this.performance,
            totalInitTime: this.performance.firstPaintTime - this.performance.initStart,
            isInitialized: this.isInitialized
        };
    }

    /**
     * Check if all services are ready
     * @returns {boolean} Ready status
     */
    isReady() {
        return this.isInitialized && 
               this.weatherService && 
               this.uiState && 
               this.mapController && 
               this.spotManager;
    }

    /**
     * Cleanup initialization resources
     */
    destroy() {
        console.log('AppInitializer: Cleaning up...');
        
        // Remove global references
        if (window.appServices) {
            delete window.appServices;
        }
        
        // Remove error handlers
        window.removeEventListener('unhandledrejection', this.handleUnhandledRejection);
        window.removeEventListener('error', this.handleGlobalError);
        
        // Reset state
        this.isInitialized = false;
        this.weatherService = null;
        this.uiState = null;
        this.mapController = null;
        this.spotManager = null;
        this.errorMonitor = null;
        
        console.log('AppInitializer: Cleanup complete');
    }
}

export default AppInitializer;