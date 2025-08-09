/**
 * Offline Maps Manager for IGN tiles
 * Handles offline map layers, fallback strategies, and download management
 */

class OfflineMapsManager {
    constructor(map) {
        this.map = map;
        this.layers = {};
        this.currentLayer = null;
        this.apiBase = 'http://localhost:8000/api/ign-offline';
        this.offlineStatus = {};
        
        this.init();
    }
    
    async init() {
        await this.loadOfflineStatus();
        await this.loadAvailableLayers();
        this.setupUI();
        this.startProgressMonitoring();
    }
    
    async loadOfflineStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            this.offlineStatus = await response.json();
            console.log('Offline maps status:', this.offlineStatus);
        } catch (error) {
            console.error('Failed to load offline status:', error);
        }
    }
    
    async loadAvailableLayers() {
        try {
            const response = await fetch(`${this.apiBase}/layers`);
            const data = await response.json();
            
            for (const [id, config] of Object.entries(data.layers)) {
                this.addOfflineLayer(id, config);
            }
        } catch (error) {
            console.error('Failed to load offline layers:', error);
        }
    }
    
    addOfflineLayer(id, config) {
        // Create offline tile layer with fallback
        const offlineLayer = L.tileLayer(config.url_template, {
            attribution: config.attribution,
            minZoom: config.minzoom,
            maxZoom: config.maxzoom,
            opacity: config.opacity,
            errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        });
        
        // Add error handling
        offlineLayer.on('tileerror', (error) => {
            this.handleTileError(error, id);
        });
        
        // Store layer
        this.layers[id] = {
            layer: offlineLayer,
            config: config,
            errorCount: 0,
            loadedTiles: 0
        };
        
        // Add success handler
        offlineLayer.on('tileload', () => {
            this.layers[id].loadedTiles++;
            this.updateStats(id);
        });
    }
    
    handleTileError(error, layerId) {
        const layer = this.layers[layerId];
        if (layer) {
            layer.errorCount++;
            
            // Try fallback if too many errors
            if (layer.errorCount > 10 && !layer.fallbackActive) {
                this.activateFallback(layerId);
            }
        }
    }
    
    activateFallback(layerId) {
        console.log(`Activating fallback for ${layerId}`);
        const layer = this.layers[layerId];
        layer.fallbackActive = true;
        
        // Switch to online IGN if available
        if (window.IGN_API_KEY) {
            const onlineUrl = this.getOnlineUrl(layerId);
            if (onlineUrl) {
                layer.layer.setUrl(onlineUrl);
                this.showNotification('Basculement vers les tuiles en ligne', 'warning');
            }
        }
    }
    
    getOnlineUrl(layerId) {
        const onlineUrls = {
            'ign_plan': 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
            'ign_ortho': 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg',
            'ign_cartes': 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg'
        };
        return onlineUrls[layerId];
    }
    
    switchToLayer(layerId) {
        // Remove current layer
        if (this.currentLayer && this.map.hasLayer(this.currentLayer)) {
            this.map.removeLayer(this.currentLayer);
        }
        
        // Add new layer
        if (this.layers[layerId]) {
            this.currentLayer = this.layers[layerId].layer;
            this.map.addLayer(this.currentLayer);
            this.updateUI(layerId);
        }
    }
    
    setupUI() {
        // Create control panel
        const OfflineControl = L.Control.extend({
            options: { position: 'topright' },
            
            onAdd: (map) => {
                const container = L.DomUtil.create('div', 'offline-maps-control');
                container.innerHTML = this.createControlHTML();
                
                // Prevent map interactions
                L.DomEvent.disableClickPropagation(container);
                L.DomEvent.disableScrollPropagation(container);
                
                // Setup event handlers
                this.setupEventHandlers(container);
                
                return container;
            }
        });
        
        this.control = new OfflineControl();
        this.map.addControl(this.control);
    }
    
    createControlHTML() {
        const totalSize = this.offlineStatus.total_size_mb || 0;
        const totalTiles = this.offlineStatus.total_tiles || 0;
        
        return `
            <div class="offline-control-header">
                <h4>🗺️ Cartes Hors-ligne</h4>
                <span class="offline-status">
                    ${totalTiles.toLocaleString()} tuiles • ${totalSize.toFixed(1)} MB
                </span>
            </div>
            <div class="offline-layers-list">
                ${Object.entries(this.layers).map(([id, layer]) => `
                    <div class="offline-layer-item" data-layer-id="${id}">
                        <input type="radio" name="offline-layer" id="layer-${id}" value="${id}">
                        <label for="layer-${id}">
                            <span class="layer-name">${layer.config.name}</span>
                            <span class="layer-stats">${layer.config.tile_count} tuiles</span>
                        </label>
                    </div>
                `).join('')}
            </div>
            <div class="offline-progress" id="download-progress" style="display: none;">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <span class="progress-text">Téléchargement...</span>
            </div>
            <div class="offline-actions">
                <button id="refresh-offline" class="btn-small">↻ Actualiser</button>
                <button id="download-more" class="btn-small">⬇ Télécharger</button>
            </div>
        `;
    }
    
    setupEventHandlers(container) {
        // Layer selection
        container.querySelectorAll('input[name="offline-layer"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.switchToLayer(e.target.value);
            });
        });
        
        // Refresh button
        container.querySelector('#refresh-offline').addEventListener('click', async () => {
            await this.loadOfflineStatus();
            await this.loadAvailableLayers();
            this.updateUI();
        });
        
        // Download button
        container.querySelector('#download-more').addEventListener('click', () => {
            this.showDownloadDialog();
        });
    }
    
    updateUI(activeLayerId) {
        // Update radio buttons
        const radios = document.querySelectorAll('input[name="offline-layer"]');
        radios.forEach(radio => {
            radio.checked = radio.value === activeLayerId;
        });
    }
    
    updateStats(layerId) {
        const layer = this.layers[layerId];
        if (layer && layer.loadedTiles % 100 === 0) {
            console.log(`Layer ${layerId}: ${layer.loadedTiles} tiles loaded, ${layer.errorCount} errors`);
        }
    }
    
    async startProgressMonitoring() {
        // Check download progress every 5 seconds
        setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBase}/download/progress`);
                const progress = await response.json();
                
                if (progress.status === 'downloading') {
                    this.updateDownloadProgress(progress);
                }
            } catch (error) {
                // Silently fail - downloads might not be active
            }
        }, 5000);
    }
    
    updateDownloadProgress(progress) {
        const progressDiv = document.getElementById('download-progress');
        if (progressDiv) {
            progressDiv.style.display = 'block';
            
            const fill = progressDiv.querySelector('.progress-fill');
            const text = progressDiv.querySelector('.progress-text');
            
            const percentage = progress.overall_progress.percentage;
            fill.style.width = `${percentage}%`;
            text.textContent = `${percentage.toFixed(1)}% - ${progress.overall_progress.tiles_downloaded.toLocaleString()} tuiles`;
        }
    }
    
    showDownloadDialog() {
        // Create download dialog
        const dialog = document.createElement('div');
        dialog.className = 'offline-download-dialog';
        dialog.innerHTML = `
            <div class="dialog-content">
                <h3>Télécharger des cartes hors-ligne</h3>
                <div class="download-options">
                    <label>
                        <input type="radio" name="region" value="toulouse" checked>
                        Toulouse et environs (5 GB)
                    </label>
                    <label>
                        <input type="radio" name="region" value="pyrenees">
                        Pyrénées (15 GB)
                    </label>
                    <label>
                        <input type="radio" name="region" value="occitanie">
                        Occitanie complète (50 GB)
                    </label>
                </div>
                <div class="download-layers">
                    <label>
                        <input type="checkbox" name="layer" value="ign_plan" checked>
                        Plan IGN
                    </label>
                    <label>
                        <input type="checkbox" name="layer" value="ign_ortho">
                        Photos aériennes
                    </label>
                    <label>
                        <input type="checkbox" name="layer" value="ign_cartes">
                        Cartes topographiques
                    </label>
                </div>
                <div class="dialog-actions">
                    <button id="start-download" class="btn-primary">Démarrer</button>
                    <button id="cancel-download" class="btn-secondary">Annuler</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        
        // Handle actions
        dialog.querySelector('#start-download').addEventListener('click', () => {
            this.startDownload(dialog);
        });
        
        dialog.querySelector('#cancel-download').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });
    }
    
    async startDownload(dialog) {
        const region = dialog.querySelector('input[name="region"]:checked').value;
        const layers = Array.from(dialog.querySelectorAll('input[name="layer"]:checked'))
            .map(cb => cb.value);
        
        document.body.removeChild(dialog);
        
        for (const layer of layers) {
            try {
                const response = await fetch(`${this.apiBase}/download/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        layer: layer,
                        region: region,
                        zoom_min: 5,
                        zoom_max: 15
                    })
                });
                
                const result = await response.json();
                this.showNotification(`Téléchargement démarré: ${layer}`, 'success');
            } catch (error) {
                this.showNotification(`Erreur: ${error.message}`, 'error');
            }
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Auto-initialize when map is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.spotsMap) {
        window.offlineMapsManager = new OfflineMapsManager(window.spotsMap);
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OfflineMapsManager;
}