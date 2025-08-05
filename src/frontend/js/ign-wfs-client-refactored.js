/**
 * IGN WFS Client - Refactored Main Module
 * Orchestrates WFS functionality using modular components
 */

import { IGNWFSApi } from './ign-wfs-api.js';
import { IGNWFSVisualization } from './ign-wfs-visualization.js';
import { IGN_WFS_CONFIG } from './ign-wfs-config.js';
import { createBoundsBuffer } from './ign-wfs-utils.js';

export class IGNWFSClient {
    constructor(apiBaseUrl = 'http://localhost:8000/api/ign') {
        this.api = new IGNWFSApi(apiBaseUrl);
        this.visualization = new IGNWFSVisualization(this.api);
        this.autoRefreshInterval = null;
        this.autoRefreshDelay = 5 * 60 * 1000; // 5 minutes
    }
    
    /**
     * Get API instance for direct access
     */
    getApi() {
        return this.api;
    }
    
    /**
     * Get visualization instance for direct access
     */
    getVisualization() {
        return this.visualization;
    }
    
    /**
     * Initialize WFS client
     */
    async initialize() {
        try {
            const capabilities = await this.api.getCapabilities();
            console.log('IGN WFS Client initialized with capabilities:', capabilities);
            return true;
        } catch (error) {
            console.error('Failed to initialize IGN WFS Client:', error);
            return false;
        }
    }
    
    /**
     * Main method to visualize spot environment
     */
    async visualizeSpotEnvironment(map, spotId, coordinates) {
        return this.visualization.visualizeSpotEnvironment(map, spotId, coordinates);
    }
    
    /**
     * Query transport network
     */
    async queryTransportNetwork(lat, lon, radius = 1000, transportType = 'all') {
        return this.api.queryTransportNetwork(lat, lon, radius, transportType);
    }
    
    /**
     * Query hydrography
     */
    async queryHydrography(lat, lon, radius = 2000, featureType = 'all') {
        return this.api.queryHydrography(lat, lon, radius, featureType);
    }
    
    /**
     * Query administrative boundaries
     */
    async queryAdministrativeBoundaries(lat, lon, radius = 5000, level = 'commune') {
        const bbox = createBoundsBuffer(lat, lon, radius);
        return this.api.queryAdministrativeBoundaries(bbox, level);
    }
    
    /**
     * Get comprehensive area analysis
     */
    async getAreaAnalysis(lat, lon, radius = 2000) {
        try {
            const [transport, hydrography, boundaries] = await Promise.all([
                this.queryTransportNetwork(lat, lon, radius),
                this.queryHydrography(lat, lon, radius),
                this.queryAdministrativeBoundaries(lat, lon, radius)
            ]);
            
            return {
                success: true,
                center: { lat, lon },
                radius,
                transport,
                hydrography,
                administrative: boundaries,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('Failed to get area analysis:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Enable auto-refresh for a spot
     */
    enableAutoRefresh(map, spotId, coordinates, interval = null) {
        this.disableAutoRefresh(); // Clear any existing interval
        
        const refreshInterval = interval || this.autoRefreshDelay;
        
        this.autoRefreshInterval = setInterval(async () => {
            console.log('Auto-refreshing WFS data...');
            await this._refreshAnalysis(spotId, map, coordinates);
        }, refreshInterval);
        
        console.log(`Auto-refresh enabled (every ${refreshInterval / 1000}s)`);
    }
    
    /**
     * Disable auto-refresh
     */
    disableAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('Auto-refresh disabled');
        }
    }
    
    /**
     * Refresh analysis for a spot
     */
    async _refreshAnalysis(spotId, map, coordinates) {
        try {
            // Clear cache for this spot
            const cacheKey = `spot_analysis_${spotId}_1500`;
            this.api.cache.delete(cacheKey);
            
            // Re-visualize
            await this.visualizeSpotEnvironment(map, spotId, coordinates);
            console.log('Analysis refreshed successfully');
        } catch (error) {
            console.error('Failed to refresh analysis:', error);
        }
    }
    
    /**
     * Clear all caches
     */
    clearCache() {
        this.api.clearCache();
    }
    
    /**
     * Get cache statistics
     */
    getCacheStats() {
        return this.api.getCacheStats();
    }
    
    /**
     * Check service status
     */
    async checkStatus() {
        try {
            await this.api._testConnectivity();
            return {
                online: this.api.isOnline,
                lastError: this.api.lastError,
                cacheStats: this.getCacheStats()
            };
        } catch (error) {
            return {
                online: false,
                error: error.message
            };
        }
    }
    
    /**
     * Export analysis data
     */
    exportAnalysisData(analysis) {
        const exportData = {
            ...analysis,
            exportDate: new Date().toISOString(),
            version: '2.0'
        };
        
        const blob = new Blob(
            [JSON.stringify(exportData, null, 2)], 
            { type: 'application/json' }
        );
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ign_analysis_${analysis.center.lat}_${analysis.center.lon}_${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }
}

// Export singleton instance for backward compatibility
const ignWFSClient = new IGNWFSClient();

// Make it globally available for legacy code
if (typeof window !== 'undefined') {
    window.IGNWFSClient = IGNWFSClient;
    window.ignWFSClient = ignWFSClient;
}

export default ignWFSClient;