/**
 * IGN WFS API Module
 * Handles all API calls to the backend WFS endpoints
 */

import { IGN_WFS_CONFIG } from './ign-wfs-config.js';
import { createCacheKey, isCacheValid, createBoundsBuffer } from './ign-wfs-utils.js';

export class IGNWFSApi {
    constructor(apiBaseUrl = 'http://localhost:8000/api/ign') {
        this.apiBaseUrl = apiBaseUrl;
        this.cache = new Map();
        this.isOnline = true;
        this.lastError = null;
        
        // Test connectivity on initialization
        this._testConnectivity();
    }
    
    /**
     * Test WFS service connectivity
     */
    async _testConnectivity() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`${this.apiBaseUrl}${IGN_WFS_CONFIG.endpoints.capabilities}`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            this.isOnline = response.ok;
            
            if (!this.isOnline) {
                console.warn('⚠️ IGN WFS service returned status:', response.status);
            } else {
                console.log('✅ IGN WFS service is online');
            }
        } catch (error) {
            this.isOnline = false;
            this.lastError = error;
            console.warn('⚠️ IGN WFS service unavailable:', error.message);
        }
    }
    
    /**
     * Safe fetch with timeout and retry logic
     */
    async _safeFetch(url, options = {}, attempt = 1) {
        const controller = new AbortController();
        const timeoutId = setTimeout(
            () => controller.abort(), 
            IGN_WFS_CONFIG.request.timeout
        );
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            // Retry logic
            if (attempt < IGN_WFS_CONFIG.request.retryAttempts && 
                (error.name === 'AbortError' || error.message.includes('NetworkError'))) {
                console.log(`Retry attempt ${attempt + 1}...`);
                await new Promise(resolve => 
                    setTimeout(resolve, IGN_WFS_CONFIG.request.retryDelay * attempt)
                );
                return this._safeFetch(url, options, attempt + 1);
            }
            
            throw error;
        }
    }
    
    /**
     * Get WFS capabilities
     */
    async getCapabilities() {
        const cacheKey = 'capabilities';
        const cached = this.cache.get(cacheKey);
        
        if (isCacheValid(cached)) {
            return cached.data;
        }
        
        try {
            const data = await this._safeFetch(
                `${this.apiBaseUrl}${IGN_WFS_CONFIG.endpoints.capabilities}`
            );
            
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
            
            return data;
        } catch (error) {
            console.error('Failed to get capabilities:', error);
            throw error;
        }
    }
    
    /**
     * Get WFS analysis for a specific spot
     */
    async getSpotWFSAnalysis(spotId, radius = 1500) {
        const cacheKey = createCacheKey('spot_analysis', spotId, radius);
        const cached = this.cache.get(cacheKey);
        
        if (isCacheValid(cached)) {
            return cached.data;
        }
        
        try {
            const url = IGN_WFS_CONFIG.endpoints.spotAnalysis.replace('{spotId}', spotId);
            const data = await this._safeFetch(
                `${this.apiBaseUrl}${url}?radius=${radius}`
            );
            
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
            
            return data;
        } catch (error) {
            console.error('Failed to get spot analysis:', error);
            throw error;
        }
    }
    
    /**
     * Query transport network around a point
     */
    async queryTransportNetwork(lat, lon, radius = 1000, transportType = 'all') {
        const cacheKey = createCacheKey('transport', lat, lon, radius, transportType);
        const cached = this.cache.get(cacheKey);
        
        if (isCacheValid(cached)) {
            return cached.data;
        }
        
        try {
            const params = new URLSearchParams({
                lat,
                lon,
                radius,
                type: transportType
            });
            
            const data = await this._safeFetch(
                `${this.apiBaseUrl}${IGN_WFS_CONFIG.endpoints.transport}?${params}`
            );
            
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
            
            return data;
        } catch (error) {
            console.error('Failed to query transport network:', error);
            throw error;
        }
    }
    
    /**
     * Query hydrography features around a point
     */
    async queryHydrography(lat, lon, radius = 2000, featureType = 'all') {
        const cacheKey = createCacheKey('hydrography', lat, lon, radius, featureType);
        const cached = this.cache.get(cacheKey);
        
        if (isCacheValid(cached)) {
            return cached.data;
        }
        
        try {
            const params = new URLSearchParams({
                lat,
                lon,
                radius,
                type: featureType
            });
            
            const data = await this._safeFetch(
                `${this.apiBaseUrl}${IGN_WFS_CONFIG.endpoints.hydrography}?${params}`
            );
            
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
            
            return data;
        } catch (error) {
            console.error('Failed to query hydrography:', error);
            throw error;
        }
    }
    
    /**
     * Query administrative boundaries
     */
    async queryAdministrativeBoundaries(bbox, level = 'commune') {
        const cacheKey = createCacheKey(
            'administrative', 
            bbox.south, bbox.north, bbox.west, bbox.east, 
            level
        );
        const cached = this.cache.get(cacheKey);
        
        if (isCacheValid(cached)) {
            return cached.data;
        }
        
        try {
            const params = new URLSearchParams({
                bbox: `${bbox.south},${bbox.west},${bbox.north},${bbox.east}`,
                level
            });
            
            const data = await this._safeFetch(
                `${this.apiBaseUrl}${IGN_WFS_CONFIG.endpoints.administrative}?${params}`
            );
            
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
            
            return data;
        } catch (error) {
            console.error('Failed to query administrative boundaries:', error);
            throw error;
        }
    }
    
    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
        console.log('WFS cache cleared');
    }
    
    /**
     * Get cache statistics
     */
    getCacheStats() {
        const now = Date.now();
        let validCount = 0;
        let expiredCount = 0;
        
        this.cache.forEach(entry => {
            if (isCacheValid(entry)) {
                validCount++;
            } else {
                expiredCount++;
            }
        });
        
        return {
            total: this.cache.size,
            valid: validCount,
            expired: expiredCount
        };
    }
}

export default IGNWFSApi;