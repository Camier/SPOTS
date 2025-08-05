/**
 * App UI Management Module
 * Handles spot management UI, activities list, modals, and import/export
 */

export class AppUIManager {
    constructor(services, config) {
        this.services = services;
        this.config = config;
        this.isSpotCreationMode = false;
        this.pendingSpotLocation = null;
        
        this.setupUI();
    }

    /**
     * Setup UI components and event listeners
     */
    setupUI() {
        console.log('AppUIManager: Setting up UI components...');
        
        this.setupSpotManagement();
        this.setupActivitiesList();
        this.setupModals();
        this.setupImportExport();
        
        console.log('AppUIManager: UI setup complete');
    }

    /**
     * Setup spot management UI and functionality
     * @private
     */
    setupSpotManagement() {
        // Add spot button
        const addBtn = document.getElementById('add-spot-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.startSpotCreation());
        }

        // Modal controls
        const form = document.getElementById('spot-form');
        const cancelBtn = document.getElementById('cancel-spot');
        
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveNewSpot();
            });
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelSpotCreation());
        }
        
        // Populate spot types dropdown
        this.populateSpotTypes();
        
        // Listen for map events
        this.services.mapController.on('spotLocationSelected', (e) => {
            this.showSpotModal(e.detail);
        });
        
        this.services.mapController.on('customSpotClicked', (e) => {
            this.handleCustomSpotClick(e.detail.spot);
        });
        
        // Load saved spots on startup
        this.loadSavedSpots();
    }

    /**
     * Setup activities list in side panel
     * @private
     */
    setupActivitiesList() {
        this.populateActivitiesList();
    }

    /**
     * Setup modal interactions
     * @private
     */
    setupModals() {
        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeAllModals();
            }
        });
        
        // ESC key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    /**
     * Setup import/export functionality
     * @private
     */
    setupImportExport() {
        const mesSpotBtn = document.getElementById('btn-mes-spots');
        const importExportBtn = document.getElementById('btn-import-export');
        const exportBtn = document.getElementById('export-spots-btn');
        const importBtn = document.getElementById('import-spots-btn');
        const importFile = document.getElementById('import-file');
        const closeImportExport = document.getElementById('close-import-export');
        
        if (mesSpotBtn) {
            mesSpotBtn.addEventListener('click', () => this.showMySpots());
        }
        
        if (importExportBtn) {
            importExportBtn.addEventListener('click', () => {
                this.showImportExportModal();
            });
        }
        
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportSpots());
        }
        
        if (importBtn && importFile) {
            importBtn.addEventListener('click', async () => {
                if (importFile.files.length > 0) {
                    await this.importSpots(importFile.files[0]);
                }
            });
        }
        
        if (closeImportExport) {
            closeImportExport.addEventListener('click', () => {
                this.hideImportExportModal();
            });
        }
    }

    /**
     * Populate activities list in side panel
     * @private
     */
    populateActivitiesList() {
        const listElement = document.getElementById('liste-activites');
        if (!listElement) {
            console.warn('AppUIManager: Activities list element not found');
            return;
        }
        
        listElement.innerHTML = '';
        
        this.config.activities.forEach((activity) => {
            const activityCard = document.createElement('div');
            activityCard.className = 'carte-meteo bg-white border rounded-lg shadow-sm cursor-pointer hover:shadow-md transition-shadow';
            
            activityCard.innerHTML = `
                <div class="p-3">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-medium text-sm">${this.services.mapController.getActivityIcon(activity.type)} ${activity.nom}</h4>
                        <span class="text-xs px-2 py-1 rounded-full bg-gray-100">${activity.type}</span>
                    </div>
                    <p class="text-xs text-gray-600 mb-2">${activity.description}</p>
                    <div class="flex gap-1">
                        <button class="text-xs bg-blue-500 text-white px-2 py-1 rounded flex-1" 
                                data-activity-center="${activity.nom}">
                            📍 Centrer
                        </button>
                        <button class="text-xs bg-green-500 text-white px-2 py-1 rounded flex-1" 
                                data-activity-route='${JSON.stringify(activity)}'>
                            ➕ Route
                        </button>
                    </div>
                </div>
            `;
            
            // Add event listeners to buttons
            const centerBtn = activityCard.querySelector('[data-activity-center]');
            const routeBtn = activityCard.querySelector('[data-activity-route]');
            
            if (centerBtn) {
                centerBtn.addEventListener('click', () => {
                    this.centerOnActivity(activity.nom);
                });
            }
            
            if (routeBtn) {
                routeBtn.addEventListener('click', () => {
                    this.addToRoute(activity);
                });
            }
            
            listElement.appendChild(activityCard);
        });
        
        console.log(`AppUIManager: Populated ${this.config.activities.length} activities`);
    }

    /**
     * Populate spot types dropdown
     * @private
     */
    populateSpotTypes() {
        const select = document.getElementById('spot-type');
        if (!select) return;
        
        const spotTypes = [
            { value: 'plage', label: '🏖️ Plage' },
            { value: 'randonnee', label: '🥾 Randonnée' },
            { value: 'velo', label: '🚴 Vélo' },
            { value: 'escalade', label: '🧗 Escalade' },
            { value: 'voile', label: '⛵ Voile' },
            { value: 'surf', label: '🏄 Surf' },
            { value: 'kayak', label: '🛶 Kayak' },
            { value: 'parapente', label: '🪂 Parapente' },
            { value: 'observation', label: '🔭 Observation' },
            { value: 'photographie', label: '📸 Photographie' },
            { value: 'peche', label: '🎣 Pêche' },
            { value: 'camping', label: '⛺ Camping' },
            { value: 'baignade', label: '🏊 Baignade' }
        ];
        
        select.innerHTML = spotTypes.map(type => 
            `<option value="${type.value}">${type.label}</option>`
        ).join('');
    }

    /**
     * Start spot creation mode
     */
    startSpotCreation() {
        console.log('AppUIManager: Starting spot creation mode');
        
        this.isSpotCreationMode = true;
        this.services.mapController.enableSpotCreation();
        
        // Show instructions
        this.services.uiState.showNotification(
            'Cliquez sur la carte pour placer votre spot!', 
            'info'
        );
    }

    /**
     * Cancel spot creation
     */
    cancelSpotCreation() {
        console.log('AppUIManager: Cancelling spot creation');
        
        this.isSpotCreationMode = false;
        this.pendingSpotLocation = null;
        this.services.mapController.disableSpotCreation();
        
        this.hideSpotModal();
    }

    /**
     * Show spot creation modal
     * @param {Object} location - Selected location
     */
    showSpotModal(location) {
        if (!this.isSpotCreationMode) return;
        
        console.log('AppUIManager: Showing spot modal for location:', location);
        
        this.pendingSpotLocation = location;
        
        const modal = document.getElementById('spot-modal');
        if (modal) {
            modal.classList.remove('hidden');
            
            // Pre-fill coordinates
            const latInput = document.getElementById('spot-lat');
            const lngInput = document.getElementById('spot-lng');
            
            if (latInput) latInput.value = location.lat.toFixed(6);
            if (lngInput) lngInput.value = location.lng.toFixed(6);
            
            // Focus on name input
            const nameInput = document.getElementById('spot-name');
            if (nameInput) {
                setTimeout(() => nameInput.focus(), 100);
            }
        }
    }

    /**
     * Hide spot modal
     */
    hideSpotModal() {
        const modal = document.getElementById('spot-modal');
        if (modal) {
            modal.classList.add('hidden');
            
            // Reset form
            const form = document.getElementById('spot-form');
            if (form) form.reset();
        }
    }

    /**
     * Save new spot
     */
    async saveNewSpot() {
        if (!this.pendingSpotLocation) return;
        
        const form = document.getElementById('spot-form');
        const formData = new FormData(form);
        
        const spot = {
            id: Date.now().toString(),
            name: formData.get('spot-name'),
            type: formData.get('spot-type'),
            description: formData.get('spot-description') || '',
            lat: parseFloat(formData.get('spot-lat')),
            lng: parseFloat(formData.get('spot-lng')),
            weatherSensitive: formData.get('weather-sensitive') === 'on',
            createdAt: new Date().toISOString()
        };
        
        try {
            await this.services.spotManager.addSpot(spot);
            
            console.log('AppUIManager: Spot saved:', spot.name);
            
            // Show success notification
            this.services.uiState.showNotification(
                `Spot "${spot.name}" enregistré avec succès!`,
                'success'
            );
            
            // Cleanup
            this.cancelSpotCreation();
            
        } catch (error) {
            console.error('AppUIManager: Failed to save spot:', error);
            this.services.uiState.showNotification(
                'Erreur lors de l\'enregistrement du spot',
                'error'
            );
        }
    }

    /**
     * Handle custom spot click
     * @param {Object} spot - Clicked spot
     */
    handleCustomSpotClick(spot) {
        console.log('AppUIManager: Custom spot clicked:', spot.name);
        
        // Show spot details (could be implemented as modal)
        this.services.uiState.showNotification(
            `Spot: ${spot.name} (${spot.type})`,
            'info'
        );
    }

    /**
     * Load saved spots
     * @private
     */
    loadSavedSpots() {
        const spots = this.services.spotManager.getAllSpots();
        this.services.mapController.updateCustomSpots(spots);
        
        console.log(`AppUIManager: Loaded ${spots.length} saved spots`);
    }

    /**
     * Show my spots
     */
    showMySpots() {
        const spots = this.services.spotManager.getAllSpots();
        
        if (spots.length === 0) {
            this.services.uiState.showNotification(
                'Aucun spot enregistré. Clique sur + pour ajouter!',
                'info'
            );
            return;
        }
        
        // Fit map to show all spots
        this.services.mapController.fitToCustomSpots();
        
        // Show stats
        const stats = this.services.spotManager.getStatistics();
        this.services.uiState.showNotification(
            `${stats.total} spots, ${stats.weatherSensitive} sensibles à la météo`,
            'info'
        );
    }

    /**
     * Show import/export modal
     */
    showImportExportModal() {
        const modal = document.getElementById('import-export-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    /**
     * Hide import/export modal
     */
    hideImportExportModal() {
        const modal = document.getElementById('import-export-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Export spots
     */
    exportSpots() {
        const stats = this.services.spotManager.getStatistics();
        
        if (stats.total === 0) {
            this.services.uiState.showNotification('Aucun spot à exporter', 'warning');
            return;
        }
        
        this.services.spotManager.exportAsFile('mes-spots-secrets');
        this.services.uiState.showNotification(
            `${stats.total} spots exportés avec succès!`,
            'success'
        );
        
        // Close modal
        this.hideImportExportModal();
    }

    /**
     * Import spots from file
     * @param {File} file - File to import
     */
    async importSpots(file) {
        try {
            const result = await this.services.spotManager.importFromFile(file);
            
            this.services.uiState.showNotification(
                `${result.imported} spots importés avec succès!`,
                'success'
            );
            
            // Update map with new spots
            const allSpots = this.services.spotManager.getAllSpots();
            this.services.mapController.updateCustomSpots(allSpots);
            
            // Close modal
            this.hideImportExportModal();
            
        } catch (error) {
            console.error('AppUIManager: Import failed:', error);
            this.services.uiState.showNotification(
                'Erreur lors de l\'importation des spots',
                'error'
            );
        }
    }

    /**
     * Center on activity
     * @param {string} activityName - Activity name
     */
    centerOnActivity(activityName) {
        const activity = this.config.activities.find(a => a.nom === activityName);
        if (activity) {
            console.log('AppUIManager: Centering on activity:', activityName);
            this.services.mapController.centerOn(activity.lat, activity.lon, 12);
        }
    }

    /**
     * Add activity to route
     * @param {Object} activity - Activity to add
     */
    addToRoute(activity) {
        console.log('AppUIManager: Adding to route:', activity.nom);
        
        // Route functionality would be implemented here
        // For now, just show a notification
        this.services.uiState.showNotification(
            `${activity.nom} ajouté à votre route!`,
            'success'
        );
    }

    /**
     * Close all modals
     */
    closeAllModals() {
        const modals = document.querySelectorAll('.modal, .modal-overlay');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
        
        // Cancel spot creation if active
        if (this.isSpotCreationMode) {
            this.cancelSpotCreation();
        }
    }

    /**
     * Cleanup UI manager
     */
    destroy() {
        console.log('AppUIManager: Cleaning up...');
        
        // Remove event listeners would go here
        // Reset state
        this.isSpotCreationMode = false;
        this.pendingSpotLocation = null;
        
        console.log('AppUIManager: Cleanup complete');
    }
}

export default AppUIManager;