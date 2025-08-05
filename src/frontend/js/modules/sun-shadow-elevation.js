/**
 * Enhanced Sun & Shadow Calculator with IGN Elevation Integration
 * Calculates realistic shadows based on actual terrain elevation
 */

export class ElevationShadowCalculator {
    constructor(ignApiKey = null) {
        this.apiKey = ignApiKey;
        this.elevationCache = new Map();
        this.cacheTimeout = 3600000; // 1 hour
        
        // IGN Elevation API endpoint
        this.elevationEndpoint = 'https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json';
    }

    /**
     * Get elevation for a single point
     */
    async getElevation(lat, lon) {
        const cacheKey = `${lat.toFixed(6)},${lon.toFixed(6)}`;
        
        // Check cache
        if (this.elevationCache.has(cacheKey)) {
            const cached = this.elevationCache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.elevation;
            }
        }

        try {
            const params = new URLSearchParams({
                lon: lon,
                lat: lat,
                zonly: 'true'
            });

            const response = await fetch(`${this.elevationEndpoint}?${params}`);
            const data = await response.json();
            
            const elevation = data.elevations?.[0] || 0;
            
            // Cache result
            this.elevationCache.set(cacheKey, {
                elevation: elevation,
                timestamp: Date.now()
            });
            
            return elevation;
        } catch (error) {
            console.error('Error fetching elevation:', error);
            return 0;
        }
    }

    /**
     * Get elevation profile along a line
     */
    async getElevationProfile(points) {
        const elevations = [];
        
        // Batch requests for efficiency
        const promises = points.map(point => 
            this.getElevation(point.lat, point.lng)
        );
        
        const results = await Promise.all(promises);
        
        return points.map((point, index) => ({
            ...point,
            elevation: results[index]
        }));
    }

    /**
     * Calculate shadow cast by terrain
     */
    async calculateTerrainShadow(centerPoint, sunAltitude, sunAzimuth, radius = 1000) {
        // Convert angles to radians
        const altRad = sunAltitude * Math.PI / 180;
        const azRad = sunAzimuth * Math.PI / 180;
        
        // Get center elevation
        const centerElevation = await this.getElevation(centerPoint.lat, centerPoint.lng);
        
        // Sample points in sun direction to check for blocking terrain
        const samples = 20;
        const shadowPoints = [];
        
        for (let i = 1; i <= samples; i++) {
            const distance = (radius / samples) * i;
            
            // Calculate point position in sun direction
            const lat = centerPoint.lat + (distance / 111000) * Math.cos(azRad);
            const lng = centerPoint.lng + (distance / (111000 * Math.cos(centerPoint.lat * Math.PI / 180))) * Math.sin(azRad);
            
            const elevation = await this.getElevation(lat, lng);
            
            // Calculate if this point blocks the sun
            const heightDiff = elevation - centerElevation;
            const angleToPoint = Math.atan(heightDiff / distance);
            
            if (angleToPoint > altRad) {
                // This terrain blocks the sun
                shadowPoints.push({
                    lat: lat,
                    lng: lng,
                    elevation: elevation,
                    shadowLength: distance * Math.tan(angleToPoint - altRad)
                });
            }
        }
        
        return shadowPoints;
    }

    /**
     * Calculate viewshed (what can be seen from a point)
     */
    async calculateViewshed(viewPoint, radius = 5000, samples = 36) {
        const viewElevation = await this.getElevation(viewPoint.lat, viewPoint.lng);
        const visiblePoints = [];
        
        // Sample in all directions
        for (let angle = 0; angle < 360; angle += 360 / samples) {
            const angleRad = angle * Math.PI / 180;
            let maxAngle = -90; // Start with looking straight down
            
            // Sample along this direction
            for (let dist = 100; dist <= radius; dist += 100) {
                const lat = viewPoint.lat + (dist / 111000) * Math.cos(angleRad);
                const lng = viewPoint.lng + (dist / (111000 * Math.cos(viewPoint.lat * Math.PI / 180))) * Math.sin(angleRad);
                
                const targetElevation = await this.getElevation(lat, lng);
                const heightDiff = targetElevation - viewElevation;
                const viewAngle = Math.atan(heightDiff / dist) * 180 / Math.PI;
                
                if (viewAngle > maxAngle) {
                    // This point is visible
                    maxAngle = viewAngle;
                    visiblePoints.push({
                        lat: lat,
                        lng: lng,
                        elevation: targetElevation,
                        distance: dist,
                        angle: angle,
                        visible: true
                    });
                } else {
                    // This point is hidden
                    visiblePoints.push({
                        lat: lat,
                        lng: lng,
                        elevation: targetElevation,
                        distance: dist,
                        angle: angle,
                        visible: false
                    });
                }
            }
        }
        
        return visiblePoints;
    }

    /**
     * Find optimal viewpoints for photography
     */
    async findOptimalViewpoints(targetPoint, searchRadius = 1000) {
        const targetElevation = await this.getElevation(targetPoint.lat, targetPoint.lng);
        const viewpoints = [];
        
        // Grid search around target
        const gridSize = 10;
        const stepSize = searchRadius / gridSize;
        
        for (let i = -gridSize; i <= gridSize; i++) {
            for (let j = -gridSize; j <= gridSize; j++) {
                if (i === 0 && j === 0) continue; // Skip target point
                
                const lat = targetPoint.lat + (i * stepSize / 111000);
                const lng = targetPoint.lng + (j * stepSize / (111000 * Math.cos(targetPoint.lat * Math.PI / 180)));
                const distance = Math.sqrt(i * i + j * j) * stepSize;
                
                const viewElevation = await this.getElevation(lat, lng);
                const heightDiff = viewElevation - targetElevation;
                const viewAngle = Math.atan(heightDiff / distance) * 180 / Math.PI;
                
                viewpoints.push({
                    lat: lat,
                    lng: lng,
                    elevation: viewElevation,
                    distance: distance,
                    viewAngle: viewAngle,
                    quality: this.calculateViewpointQuality(viewAngle, distance, heightDiff)
                });
            }
        }
        
        // Sort by quality
        viewpoints.sort((a, b) => b.quality - a.quality);
        
        return viewpoints.slice(0, 10); // Return top 10 viewpoints
    }

    /**
     * Calculate viewpoint quality score
     */
    calculateViewpointQuality(viewAngle, distance, heightDiff) {
        // Ideal viewing angle is slightly elevated (5-15 degrees)
        const angleScore = viewAngle > 5 && viewAngle < 15 ? 1 : 
                          viewAngle > 0 && viewAngle < 30 ? 0.7 : 0.3;
        
        // Prefer moderate distances (200-800m)
        const distanceScore = distance > 200 && distance < 800 ? 1 :
                             distance > 100 && distance < 1500 ? 0.7 : 0.3;
        
        // Prefer some elevation difference
        const elevationScore = Math.abs(heightDiff) > 10 && Math.abs(heightDiff) < 100 ? 1 :
                              Math.abs(heightDiff) > 5 && Math.abs(heightDiff) < 200 ? 0.7 : 0.3;
        
        return (angleScore + distanceScore + elevationScore) / 3;
    }

    /**
     * Calculate sun exposure duration for a point
     */
    async calculateSunExposure(point, date = new Date()) {
        const elevation = await this.getElevation(point.lat, point.lng);
        const SunCalc = window.SunCalc;
        
        const times = SunCalc.getTimes(date, point.lat, point.lng);
        const sunriseTime = times.sunrise.getTime();
        const sunsetTime = times.sunset.getTime();
        
        let sunExposureMinutes = 0;
        const checkInterval = 15; // Check every 15 minutes
        
        for (let time = sunriseTime; time < sunsetTime; time += checkInterval * 60000) {
            const checkDate = new Date(time);
            const sunPos = SunCalc.getPosition(checkDate, point.lat, point.lng);
            const sunAltitude = sunPos.altitude * 180 / Math.PI;
            const sunAzimuth = (sunPos.azimuth * 180 / Math.PI + 180) % 360;
            
            if (sunAltitude > 0) {
                // Check if terrain blocks the sun
                const shadows = await this.calculateTerrainShadow(
                    point, 
                    sunAltitude, 
                    sunAzimuth, 
                    2000
                );
                
                if (shadows.length === 0) {
                    sunExposureMinutes += checkInterval;
                }
            }
        }
        
        return {
            totalHours: sunExposureMinutes / 60,
            percentage: (sunExposureMinutes / ((sunsetTime - sunriseTime) / 60000)) * 100,
            firstSun: null, // TODO: Calculate first sun time
            lastSun: null   // TODO: Calculate last sun time
        };
    }
}

// Export for use in main app
export default ElevationShadowCalculator;