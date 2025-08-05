/**
 * API Data Loader Module
 * Loads spots data from the backend API instead of static JSON
 */

export class ApiDataLoader {
    constructor(apiBaseUrl = 'http://localhost:8000') {
        this.apiBaseUrl = apiBaseUrl;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Load quality spots from API
     * @param {Object} options - Filter options
     * @returns {Promise<Object>} Spots data with metadata
     */
    async loadQualitySpots(options = {}) {
        const params = new URLSearchParams({
            min_confidence: options.minConfidence || 0.7,
            exclude_unknown: options.excludeUnknown !== false,
            limit: options.limit || 500
        });

        return this.fetchWithCache(`/api/spots/quality?${params}`);
    }

    /**
     * Load all spots with pagination
     * @param {Object} options - Pagination and filter options
     * @returns {Promise<Object>} Spots data with pagination info
     */
    async loadAllSpots(options = {}) {
        const params = new URLSearchParams({
            limit: options.limit || 100,
            offset: options.offset || 0
        });

        if (options.type) params.append('type', options.type);
        if (options.minConfidence) params.append('min_confidence', options.minConfidence);

        return this.fetchWithCache(`/api/spots?${params}`);
    }

    /**
     * Load spots by department
     * @param {string} deptCode - Department code (09, 31, etc.)
     * @param {Object} options - Pagination options
     * @returns {Promise<Object>} Department spots data
     */
    async loadDepartmentSpots(deptCode, options = {}) {
        const params = new URLSearchParams({
            limit: options.limit || 100,
            offset: options.offset || 0
        });

        return this.fetchWithCache(`/api/spots/department/${deptCode}?${params}`);
    }

    /**
     * Get single spot by ID
     * @param {number} spotId - Spot ID
     * @returns {Promise<Object>} Spot details
     */
    async getSpot(spotId) {
        return this.fetchWithCache(`/api/spots/${spotId}`);
    }

    /**
     * Search spots by query
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @returns {Promise<Object>} Search results
     */
    async searchSpots(query, options = {}) {
        const params = new URLSearchParams({
            q: query,
            limit: options.limit || 50
        });

        // Don't cache search results
        return this.fetchFromApi(`/api/spots/search?${params}`, false);
    }

    /**
     * Get regional statistics
     * @returns {Promise<Object>} Statistics data
     */
    async getStats() {
        return this.fetchWithCache('/api/stats', 10 * 60 * 1000); // Cache for 10 minutes
    }

    /**
     * Convert API spots to app format
     * @param {Array} spots - Raw spots from API
     * @returns {Array} Formatted spots for the app
     */
    formatSpotsForApp(spots) {
        return spots.map(spot => ({
            id: spot.id,
            name: spot.name,
            lat: spot.latitude,
            lng: spot.longitude,
            type: spot.type,
            description: spot.description,
            weatherSensitive: spot.weather_sensitive,
            confidenceScore: spot.confidence_score,
            elevation: spot.elevation,
            address: spot.address,
            department: spot.department,
            // Add UI properties
            icon: this.getIconForType(spot.type),
            qualityScore: spot.quality_score,
            hasDescription: spot.has_description,
            hasElevation: spot.has_elevation
        }));
    }

    /**
     * Get icon for spot type
     * @private
     */
    getIconForType(type) {
        const iconMap = {
            'waterfall': '🏔️💧',
            'cave': '🕳️',
            'spring': '♨️',
            'ruins': '🏛️',
            'lake': '🏊',
            'viewpoint': '👀',
            'unknown': '📍'
        };
        return iconMap[type] || iconMap['unknown'];
    }

    /**
     * Fetch with caching support
     * @private
     */
    async fetchWithCache(endpoint, customTimeout) {
        const cacheKey = endpoint;
        const cached = this.cache.get(cacheKey);
        
        if (cached && Date.now() - cached.timestamp < (customTimeout || this.cacheTimeout)) {
            console.log(`ApiDataLoader: Using cached data for ${endpoint}`);
            return cached.data;
        }

        const data = await this.fetchFromApi(endpoint);
        this.cache.set(cacheKey, {
            data,
            timestamp: Date.now()
        });

        return data;
    }

    /**
     * Fetch from API
     * @private
     */
    async fetchFromApi(endpoint, useCache = true) {
        try {
            console.log(`ApiDataLoader: Fetching ${endpoint}`);
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('ApiDataLoader: API request failed:', error);
            throw error;
        }
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
        console.log('ApiDataLoader: Cache cleared');
    }
}

// Export singleton instance
export default new ApiDataLoader();