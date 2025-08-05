/**
 * Hidden Spots Loader Module
 * Loads community-discovered hidden outdoor spots into the weather app
 */

export class HiddenSpotsLoader {
    constructor() {
        this.hiddenSpots = [];
        this.isLoaded = false;
        this.loadError = null;
    }

    /**
     * Load hidden spots from scraped data
     * @returns {Promise<Array>} Array of hidden spot objects
     */
    async loadHiddenSpots() {
        try {
            console.log('HiddenSpotsLoader: Loading community-discovered spots...');
            
            const response = await fetch('/data/hidden_spots_for_app.json');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Validate data structure
            if (!data.hidden_spots || !Array.isArray(data.hidden_spots)) {
                throw new Error('Invalid hidden spots data format');
            }
            
            // Process and enrich spots
            this.hiddenSpots = data.hidden_spots.map(spot => this.enrichSpot(spot));
            
            this.isLoaded = true;
            console.log(`HiddenSpotsLoader: Loaded ${this.hiddenSpots.length} hidden spots`);
            
            // Log metadata if available
            if (data.metadata) {
                console.log('HiddenSpotsLoader: Metadata:', data.metadata);
            }
            
            return this.hiddenSpots;
            
        } catch (error) {
            console.error('HiddenSpotsLoader: Failed to load hidden spots:', error);
            this.loadError = error;
            
            // Return empty array on error
            return [];
        }
    }

    /**
     * Enrich spot data with additional properties
     * @param {Object} spot - Raw spot data
     * @returns {Object} Enriched spot object
     */
    enrichSpot(spot) {
        // Add icon based on type
        const iconMap = {
            'waterfall': '🏔️💧',
            'cascade': '🏔️💧',
            'lake': '🏊',
            'spring': '♨️',
            'cave': '🕳️',
            'grotte': '🕳️',
            'beach': '🏖️',
            'plage': '🏖️',
            'coastal_feature': '🌊',
            'mountain_feature': '⛰️',
            'other': '📍'
        };
        
        const spotType = spot.type || 'other';
        spot.icon = iconMap[spotType.toLowerCase()] || iconMap['other'];
        
        // Add secrecy indicator
        if (spot.secrecy_level === 'very_hidden') {
            spot.secretIcon = '🤫';
            spot.secretLabel = 'Très secret';
        } else if (spot.secrecy_level === 'hidden') {
            spot.secretIcon = '🤐';
            spot.secretLabel = 'Peu connu';
        }
        
        // Format activities
        if (spot.activities && spot.activities.length > 0) {
            spot.formattedActivities = spot.activities.map(activity => {
                const activityLabels = {
                    'baignade': '🏊 Baignade',
                    'randonnee': '🥾 Randonnée',
                    'escalade': '🧗 Escalade',
                    'kayak': '🛶 Kayak',
                    'vtt': '🚴 VTT',
                    'bivouac': '🏕️ Bivouac',
                    'ski': '⛷️ Ski'
                };
                return activityLabels[activity] || activity;
            });
        }
        
        // Add discovery info
        spot.discoveryInfo = `Découvert par la communauté (${spot.mentions || 1} mention${spot.mentions > 1 ? 's' : ''})`;
        
        // Ensure required fields
        spot.nom = spot.nom || 'Lieu secret';
        spot.lat = parseFloat(spot.lat) || 0;
        spot.lon = parseFloat(spot.lon) || 0;
        spot.description = spot.description || 'Spot découvert par la communauté';
        
        // Add weather suitability placeholder
        spot.weatherDependent = true;
        spot.bestConditions = this.determineBestConditions(spot);
        
        return spot;
    }

    /**
     * Determine best weather conditions for spot
     * @param {Object} spot - Spot object
     * @returns {Object} Best conditions info
     */
    determineBestConditions(spot) {
        const conditions = {
            temperature: { min: 15, max: 30 },
            precipitation: { max: 5 },
            wind: { max: 20 },
            season: 'toute année'
        };
        
        // Adjust based on activities
        if (spot.activities) {
            if (spot.activities.includes('baignade')) {
                conditions.temperature.min = 20;
                conditions.season = 'été';
            }
            if (spot.activities.includes('ski')) {
                conditions.temperature.max = 5;
                conditions.season = 'hiver';
            }
            if (spot.activities.includes('escalade')) {
                conditions.precipitation.max = 0;
                conditions.wind.max = 15;
            }
        }
        
        return conditions;
    }

    /**
     * Filter spots by activity type
     * @param {string} activity - Activity type to filter by
     * @returns {Array} Filtered spots
     */
    filterByActivity(activity) {
        if (!activity || activity === 'all') {
            return this.hiddenSpots;
        }
        
        return this.hiddenSpots.filter(spot => 
            spot.activities && spot.activities.includes(activity)
        );
    }

    /**
     * Filter spots by secrecy level
     * @param {string} level - Secrecy level (hidden, very_hidden)
     * @returns {Array} Filtered spots
     */
    filterBySecrecy(level) {
        if (!level || level === 'all') {
            return this.hiddenSpots;
        }
        
        return this.hiddenSpots.filter(spot => 
            spot.secrecy_level === level
        );
    }

    /**
     * Find spots near a location
     * @param {number} lat - Latitude
     * @param {number} lon - Longitude
     * @param {number} radiusKm - Search radius in kilometers
     * @returns {Array} Spots within radius
     */
    findNearbySpots(lat, lon, radiusKm = 50) {
        return this.hiddenSpots.filter(spot => {
            const distance = this.calculateDistance(lat, lon, spot.lat, spot.lon);
            return distance <= radiusKm;
        }).sort((a, b) => {
            const distA = this.calculateDistance(lat, lon, a.lat, a.lon);
            const distB = this.calculateDistance(lat, lon, b.lat, b.lon);
            return distA - distB;
        });
    }

    /**
     * Calculate distance between two points
     * @param {number} lat1 - Latitude 1
     * @param {number} lon1 - Longitude 1
     * @param {number} lat2 - Latitude 2
     * @param {number} lon2 - Longitude 2
     * @returns {number} Distance in kilometers
     */
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in kilometers
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    /**
     * Get random hidden spots
     * @param {number} count - Number of spots to return
     * @returns {Array} Random selection of spots
     */
    getRandomSpots(count = 5) {
        const shuffled = [...this.hiddenSpots].sort(() => 0.5 - Math.random());
        return shuffled.slice(0, count);
    }

    /**
     * Get spots suitable for current weather
     * @param {Object} weatherData - Current weather conditions
     * @returns {Array} Weather-suitable spots
     */
    getSpotsForWeather(weatherData) {
        if (!weatherData) return this.hiddenSpots;
        
        const { temp_max, precipitation, wind_speed } = weatherData;
        
        return this.hiddenSpots.filter(spot => {
            const conditions = spot.bestConditions;
            
            // Check temperature
            if (temp_max < conditions.temperature.min || 
                temp_max > conditions.temperature.max) {
                return false;
            }
            
            // Check precipitation
            if (precipitation > conditions.precipitation.max) {
                return false;
            }
            
            // Check wind
            if (wind_speed > conditions.wind.max) {
                return false;
            }
            
            return true;
        });
    }

    /**
     * Create marker data for map display
     * @param {Object} spot - Spot object
     * @returns {Object} Marker configuration
     */
    createMarkerData(spot) {
        return {
            lat: spot.lat,
            lon: spot.lon,
            icon: spot.icon,
            title: spot.nom,
            popup: this.createPopupContent(spot),
            className: `hidden-spot-marker ${spot.secrecy_level}`,
            data: spot
        };
    }

    /**
     * Create popup content for spot
     * @param {Object} spot - Spot object
     * @returns {string} HTML popup content
     */
    createPopupContent(spot) {
        let html = `
            <div class="hidden-spot-popup">
                <h3>${spot.icon} ${spot.nom}</h3>
                <p class="secrecy">${spot.secretIcon || ''} ${spot.secretLabel || 'Spot communautaire'}</p>
                <p class="description">${spot.description}</p>
        `;
        
        if (spot.formattedActivities && spot.formattedActivities.length > 0) {
            html += `
                <div class="activities">
                    <strong>Activités:</strong><br>
                    ${spot.formattedActivities.join(', ')}
                </div>
            `;
        }
        
        if (spot.difficulty && spot.difficulty !== 'unknown') {
            html += `<p class="difficulty"><strong>Difficulté:</strong> ${spot.difficulty}</p>`;
        }
        
        html += `
                <p class="discovery-info">${spot.discoveryInfo}</p>
                <div class="actions">
                    <button onclick="app.centerOnActivity('${spot.nom}')">Centrer</button>
                    <button onclick="app.addToRoute(${JSON.stringify(spot).replace(/"/g, '&quot;')})">Ajouter au parcours</button>
                </div>
            </div>
        `;
        
        return html;
    }
}

// Export for use in main app
export default HiddenSpotsLoader;