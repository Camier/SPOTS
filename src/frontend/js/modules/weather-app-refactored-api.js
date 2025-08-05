/**
 * Weather App Refactored - Now with API Integration
 * Main application controller that uses live API data
 */

import { MapController } from './map-controller-refactored.js';
import ApiDataLoader from './api-data-loader.js';
import { REGIONAL_CONFIG } from './regional-config.js';

export class WeatherApp {
    constructor() {
        // Core components
        this.mapController = null;
        this.apiLoader = ApiDataLoader;
        
        // State
        this.spots = [];
        this.currentDepartment = null;
        this.filters = {
            type: 'all',
            minConfidence: 0.7,
            excludeUnknown: true
        };
        
        // UI elements
        this.elements = {};
        
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }

    async initialize() {
        try {
            console.log('WeatherApp: Initializing with API integration...');
            
            // Setup UI elements
            this.setupUIElements();
            
            // Initialize map
            this.mapController = new MapController('map', {
                center: REGIONAL_CONFIG.center,
                zoom: REGIONAL_CONFIG.defaultZoom,
                touchOptimized: true
            });
            
            // Load initial data from API
            await this.loadInitialData();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Update UI
            this.updateStats();
            
            console.log('WeatherApp: Initialization complete');
            
        } catch (error) {
            console.error('WeatherApp: Initialization failed:', error);
            this.showError('Failed to initialize application');
        }
    }

    setupUIElements() {
        this.elements = {
            statsContainer: document.getElementById('stats-container'),
            filterButtons: document.querySelectorAll('[data-filter-type]'),
            departmentSelect: document.getElementById('department-select'),
            searchInput: document.getElementById('search-spots'),
            refreshButton: document.getElementById('refresh-data'),
            loadingOverlay: document.getElementById('loading-overlay'),
            errorContainer: document.getElementById('error-container')
        };
    }

    async loadInitialData() {
        try {
            this.showLoading(true);
            
            // Load quality spots from API
            const response = await this.apiLoader.loadQualitySpots({
                minConfidence: this.filters.minConfidence,
                excludeUnknown: this.filters.excludeUnknown,
                limit: 1000
            });
            
            // Format spots for the app
            this.spots = this.apiLoader.formatSpotsForApp(response.spots);
            
            // Update map with spots
            this.mapController.updateCustomSpots(this.spots);
            
            // Load and display stats
            const stats = await this.apiLoader.getStats();
            this.displayStats(stats);
            
            console.log(`WeatherApp: Loaded ${this.spots.length} spots from API`);
            
        } catch (error) {
            console.error('WeatherApp: Failed to load data:', error);
            this.showError('Failed to load spots data. Please check if the API is running.');
        } finally {
            this.showLoading(false);
        }
    }

    setupEventListeners() {
        // Filter buttons
        this.elements.filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const filterType = e.target.dataset.filterType;
                this.applyTypeFilter(filterType);
            });
        });
        
        // Department select
        if (this.elements.departmentSelect) {
            this.elements.departmentSelect.addEventListener('change', (e) => {
                this.loadDepartmentSpots(e.target.value);
            });
        }
        
        // Search input
        if (this.elements.searchInput) {
            let searchTimeout;
            this.elements.searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchSpots(e.target.value);
                }, 300);
            });
        }
        
        // Refresh button
        if (this.elements.refreshButton) {
            this.elements.refreshButton.addEventListener('click', () => {
                this.apiLoader.clearCache();
                this.loadInitialData();
            });
        }
        
        // Map events
        this.mapController.on('customSpotClicked', (e) => {
            this.showSpotDetails(e.detail.spot);
        });
    }

    async applyTypeFilter(type) {
        try {
            this.showLoading(true);
            
            // Update active button
            this.elements.filterButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.filterType === type);
            });
            
            // Load filtered data
            const options = {
                minConfidence: this.filters.minConfidence,
                excludeUnknown: this.filters.excludeUnknown,
                limit: 1000
            };
            
            if (type !== 'all') {
                options.type = type;
            }
            
            const response = await this.apiLoader.loadAllSpots(options);
            this.spots = this.apiLoader.formatSpotsForApp(response.spots);
            this.mapController.updateCustomSpots(this.spots);
            
            this.updateStats();
            
        } catch (error) {
            console.error('WeatherApp: Filter failed:', error);
            this.showError('Failed to apply filter');
        } finally {
            this.showLoading(false);
        }
    }

    async loadDepartmentSpots(deptCode) {
        if (!deptCode || deptCode === 'all') {
            return this.loadInitialData();
        }
        
        try {
            this.showLoading(true);
            
            const response = await this.apiLoader.loadDepartmentSpots(deptCode, {
                limit: 500
            });
            
            this.spots = this.apiLoader.formatSpotsForApp(response.spots);
            this.mapController.updateCustomSpots(this.spots);
            
            // Center map on department
            const deptInfo = Object.values(REGIONAL_CONFIG.departments)
                .find(d => d.code === deptCode);
            
            if (deptInfo) {
                this.mapController.centerOn(deptInfo.center[0], deptInfo.center[1], 9);
            }
            
            this.updateStats();
            
        } catch (error) {
            console.error('WeatherApp: Department load failed:', error);
            this.showError('Failed to load department data');
        } finally {
            this.showLoading(false);
        }
    }

    async searchSpots(query) {
        if (!query || query.length < 2) {
            return this.loadInitialData();
        }
        
        try {
            const response = await this.apiLoader.searchSpots(query);
            this.spots = this.apiLoader.formatSpotsForApp(response.spots);
            this.mapController.updateCustomSpots(this.spots);
            
            this.updateStats(`Found ${response.count} spots`);
            
        } catch (error) {
            console.error('WeatherApp: Search failed:', error);
        }
    }

    async showSpotDetails(spot) {
        try {
            // Fetch full details from API
            const fullSpot = await this.apiLoader.getSpot(spot.id);
            
            // Create detail popup
            const detailHtml = `
                <div class="spot-details">
                    <h3>${fullSpot.name}</h3>
                    <p class="spot-type">${fullSpot.type} ${spot.icon}</p>
                    ${fullSpot.description ? `<p>${fullSpot.description}</p>` : ''}
                    <div class="spot-meta">
                        ${fullSpot.elevation ? `<span>Altitude: ${fullSpot.elevation}m</span>` : ''}
                        ${fullSpot.address ? `<span>${fullSpot.address}</span>` : ''}
                        <span>Confidence: ${Math.round(fullSpot.confidence_score * 100)}%</span>
                    </div>
                    ${fullSpot.weather_sensitive ? '<p class="weather-warning">⚠️ Weather sensitive location</p>' : ''}
                </div>
            `;
            
            // Show in modal or sidebar
            this.showModal(detailHtml);
            
        } catch (error) {
            console.error('WeatherApp: Failed to load spot details:', error);
        }
    }

    displayStats(stats) {
        if (!this.elements.statsContainer) return;
        
        const statsHtml = `
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Total Spots</h4>
                    <p class="stat-value">${stats.total_spots}</p>
                </div>
                ${Object.entries(stats.departments).map(([code, dept]) => `
                    <div class="stat-card dept-${code}">
                        <h4>${dept.name}</h4>
                        <p class="stat-value">${dept.count}</p>
                    </div>
                `).join('')}
            </div>
        `;
        
        this.elements.statsContainer.innerHTML = statsHtml;
    }

    updateStats(message) {
        if (!this.elements.statsContainer) return;
        
        const statsHtml = `
            <div class="current-stats">
                <p>${message || `Showing ${this.spots.length} spots`}</p>
            </div>
        `;
        
        this.elements.statsContainer.innerHTML = statsHtml;
    }

    showLoading(show) {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }

    showError(message) {
        if (this.elements.errorContainer) {
            this.elements.errorContainer.innerHTML = `
                <div class="error-message">
                    <p>⚠️ ${message}</p>
                </div>
            `;
            setTimeout(() => {
                this.elements.errorContainer.innerHTML = '';
            }, 5000);
        }
    }

    showModal(content) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('spot-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'spot-modal';
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <span class="close">&times;</span>
                    <div class="modal-body"></div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Close event
            modal.querySelector('.close').addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
        
        modal.querySelector('.modal-body').innerHTML = content;
        modal.style.display = 'block';
    }
}

// Initialize app
new WeatherApp();