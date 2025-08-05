/**
 * IGN WFS Utility Functions
 * Common helper functions for WFS operations
 */

import { IGN_WFS_CONFIG } from './ign-wfs-config.js';

/**
 * Get appropriate style for transport features
 */
export function getTransportStyle(properties) {
    const nature = (properties.nature || '').toLowerCase();
    const styles = IGN_WFS_CONFIG.layerStyles.transport;
    
    if (nature.includes('route') || nature.includes('autoroute')) {
        return styles.road;
    } else if (nature.includes('sentier') || nature.includes('chemin')) {
        return styles.path;
    } else if (nature.includes('piste')) {
        return styles.trail;
    }
    
    return styles.default;
}

/**
 * Get appropriate style for hydrography features
 */
export function getHydrographyStyle(feature) {
    const properties = feature.properties || {};
    const geometry = feature.geometry || {};
    const nature = (properties.nature || '').toLowerCase();
    const styles = IGN_WFS_CONFIG.layerStyles.hydrography;
    
    if (geometry.type === 'Point') {
        return styles.spring;
    } else if (nature.includes('fleuve') || nature.includes('rivière')) {
        return styles.river;
    } else if (nature.includes('ruisseau')) {
        return styles.stream;
    } else if (geometry.type === 'Polygon' || geometry.type === 'MultiPolygon') {
        return styles.lake;
    }
    
    return styles.default;
}

/**
 * Create cache key from parameters
 */
export function createCacheKey(...args) {
    return args.join('_');
}

/**
 * Check if cache entry is valid
 */
export function isCacheValid(entry) {
    if (!entry) return false;
    return Date.now() - entry.timestamp < IGN_WFS_CONFIG.cache.timeout;
}

/**
 * Format distance for display
 */
export function formatDistance(meters) {
    if (meters < 1000) {
        return `${Math.round(meters)}m`;
    }
    return `${(meters / 1000).toFixed(1)}km`;
}

/**
 * Calculate distance between two points (Haversine formula)
 */
export function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c;
}

/**
 * Create bounds buffer around a point
 */
export function createBoundsBuffer(lat, lon, radiusMeters) {
    // Rough approximation: 1 degree latitude ≈ 111km
    const latDelta = radiusMeters / 111000;
    // Longitude varies with latitude
    const lonDelta = radiusMeters / (111000 * Math.cos(lat * Math.PI / 180));
    
    return {
        south: lat - latDelta,
        north: lat + latDelta,
        west: lon - lonDelta,
        east: lon + lonDelta
    };
}

/**
 * Create Leaflet bounds from bbox
 */
export function createLeafletBounds(bbox) {
    return [
        [bbox.south, bbox.west],
        [bbox.north, bbox.east]
    ];
}

/**
 * Process transport network features
 */
export function processTransportFeatures(features, centerLat, centerLon) {
    return features.map(feature => {
        const coords = feature.geometry.coordinates;
        let distance = Infinity;
        
        // Calculate minimum distance to feature
        if (feature.geometry.type === 'LineString') {
            for (const coord of coords) {
                const d = calculateDistance(centerLat, centerLon, coord[1], coord[0]);
                distance = Math.min(distance, d);
            }
        } else if (feature.geometry.type === 'MultiLineString') {
            for (const line of coords) {
                for (const coord of line) {
                    const d = calculateDistance(centerLat, centerLon, coord[1], coord[0]);
                    distance = Math.min(distance, d);
                }
            }
        }
        
        return {
            ...feature,
            properties: {
                ...feature.properties,
                distance: Math.round(distance)
            }
        };
    }).sort((a, b) => a.properties.distance - b.properties.distance);
}

/**
 * Process hydrography features
 */
export function processHydrographyFeatures(features, centerLat, centerLon) {
    return features.map(feature => {
        const coords = feature.geometry.coordinates;
        let distance = Infinity;
        
        // Calculate distance based on geometry type
        if (feature.geometry.type === 'Point') {
            distance = calculateDistance(centerLat, centerLon, coords[1], coords[0]);
        } else if (feature.geometry.type === 'LineString') {
            for (const coord of coords) {
                const d = calculateDistance(centerLat, centerLon, coord[1], coord[0]);
                distance = Math.min(distance, d);
            }
        } else if (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon') {
            // For polygons, use the first coordinate as approximation
            const firstCoord = feature.geometry.type === 'Polygon' ? coords[0][0] : coords[0][0][0];
            distance = calculateDistance(centerLat, centerLon, firstCoord[1], firstCoord[0]);
        }
        
        return {
            ...feature,
            properties: {
                ...feature.properties,
                distance: Math.round(distance)
            }
        };
    }).sort((a, b) => a.properties.distance - b.properties.distance);
}

/**
 * Create summary statistics from features
 */
export function createFeatureSummary(features, type) {
    const summary = {
        total: features.length,
        byType: {},
        nearest: null,
        withinKm: {
            1: 0,
            2: 0,
            5: 0
        }
    };
    
    features.forEach(feature => {
        const nature = feature.properties.nature || 'unknown';
        summary.byType[nature] = (summary.byType[nature] || 0) + 1;
        
        const distance = feature.properties.distance;
        if (distance <= 1000) summary.withinKm[1]++;
        if (distance <= 2000) summary.withinKm[2]++;
        if (distance <= 5000) summary.withinKm[5]++;
        
        if (!summary.nearest || distance < summary.nearest.distance) {
            summary.nearest = {
                name: feature.properties.toponyme || feature.properties.nom || nature,
                type: nature,
                distance: distance
            };
        }
    });
    
    return summary;
}

export default {
    getTransportStyle,
    getHydrographyStyle,
    createCacheKey,
    isCacheValid,
    formatDistance,
    calculateDistance,
    createBoundsBuffer,
    createLeafletBounds,
    processTransportFeatures,
    processHydrographyFeatures,
    createFeatureSummary
};