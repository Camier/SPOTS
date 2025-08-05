/**
 * Map Visualization Module  
 * Handles weather markers, activity markers, and clustering
 */

export class MapVisualization {
    constructor(map, weatherConditions, options = {}) {
        this.map = map;
        this.weatherConditions = weatherConditions;
        this.options = {
            clusterRadius: options.clusterRadius || 50,
            maxClusterRadius: options.maxClusterRadius || 80,
            showCoverageOnHover: options.showCoverageOnHover !== false,
            ...options
        };
        
        // Layer groups
        this.weatherMarkersGroup = L.layerGroup().addTo(this.map);
        this.activityMarkersGroup = L.layerGroup().addTo(this.map);
        this.customSpotsGroup = L.layerGroup().addTo(this.map);
        
        // Marker clusters
        this.weatherCluster = null;
        this.activityCluster = null;
        
        this.initializeClusters();
    }

    /**
     * Initialize marker clusters
     * @private
     */
    initializeClusters() {
        // Weather markers cluster
        this.weatherCluster = L.markerClusterGroup({
            maxClusterRadius: this.options.clusterRadius,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: this.options.showCoverageOnHover,
            zoomToBoundsOnClick: true,
            iconCreateFunction: (cluster) => this.createWeatherClusterIcon(cluster)
        });
        
        // Activity markers cluster  
        this.activityCluster = L.markerClusterGroup({
            maxClusterRadius: this.options.clusterRadius,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: this.options.showCoverageOnHover,
            zoomToBoundsOnClick: true,
            iconCreateFunction: (cluster) => this.createActivityClusterIcon(cluster)
        });
        
        this.map.addLayer(this.weatherCluster);
        this.map.addLayer(this.activityCluster);
    }

    /**
     * Update weather markers on map
     * @param {Array} weatherData - Weather data array
     * @param {number} dayIndex - Current day index
     * @param {boolean} showOnlyDry - Filter for dry conditions
     */
    updateWeatherMarkers(weatherData, dayIndex = 0, showOnlyDry = false) {
        // Clear existing markers
        this.weatherCluster.clearLayers();
        
        if (!weatherData || !Array.isArray(weatherData)) {
            console.warn('MapVisualization: Invalid weather data provided');
            return;
        }

        const markersToAdd = [];
        
        weatherData.forEach(cityData => {
            if (!cityData.days || !cityData.days[dayIndex]) return;
            
            const dayData = cityData.days[dayIndex];
            const isDry = this.weatherConditions.isDryCondition(dayData.weathercode);
            
            // Apply dry filter
            if (showOnlyDry && !isDry) return;
            
            const marker = this.createWeatherMarker(cityData, dayData, dayIndex);
            if (marker) {
                markersToAdd.push(marker);
            }
        });
        
        // Add markers to cluster in batch for performance
        this.weatherCluster.addLayers(markersToAdd);
        
        console.log(`MapVisualization: Updated ${markersToAdd.length} weather markers`);
    }

    /**
     * Create weather marker
     * @private
     */
    createWeatherMarker(cityData, dayData, dayIndex) {
        const condition = this.weatherConditions.getConditionInfo(dayData.weathercode);
        const isDry = this.weatherConditions.isDryCondition(dayData.weathercode);
        
        // Create custom icon
        const icon = L.divIcon({
            className: 'weather-marker',
            html: `
                <div class="weather-icon ${isDry ? 'dry' : 'wet'}" 
                     style="background-color: ${condition.color};">
                    ${condition.icon}
                    <span class="temp">${Math.round(dayData.temperature_2m_max)}°</span>
                </div>
            `,
            iconSize: [50, 50],
            iconAnchor: [25, 25]
        });
        
        const marker = L.marker([cityData.lat, cityData.lon], { icon });
        
        // Create popup content
        const popupContent = this.createWeatherPopupContent(cityData, dayData, dayIndex);
        marker.bindPopup(popupContent, {
            maxWidth: 300,
            className: 'weather-popup'
        });
        
        return marker;
    }

    /**
     * Create weather popup content
     * @private
     */
    createWeatherPopupContent(cityData, dayData, dayIndex) {
        const condition = this.weatherConditions.getConditionInfo(dayData.weathercode);
        const date = new Date();
        date.setDate(date.getDate() + dayIndex);
        
        return `
            <div class="weather-popup-content">
                <div class="popup-header">
                    <h3>${cityData.nom}</h3>
                    <span class="date">${date.toLocaleDateString('fr-FR')}</span>
                </div>
                <div class="weather-info">
                    <div class="condition">
                        <span class="icon">${condition.icon}</span>
                        <span class="desc">${condition.description}</span>
                    </div>
                    <div class="temps">
                        <span class="max">${Math.round(dayData.temperature_2m_max)}°</span>
                        <span class="min">${Math.round(dayData.temperature_2m_min)}°</span>
                    </div>
                    <div class="details">
                        <div class="wind">
                            🌬️ ${Math.round(dayData.windspeed_10m_max)} km/h
                        </div>
                        <div class="rain">
                            💧 ${dayData.precipitation_sum || 0} mm
                        </div>
                    </div>
                </div>
                <div class="actions">
                    <button onclick="weatherApp.handleCitySelection(${JSON.stringify(cityData)}, ${dayIndex})" 
                            class="btn-primary">
                        📍 Centrer
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Update activity markers on map
     * @param {Array} activities - Activities array
     * @param {Object} filters - Active filters
     */
    updateActivityMarkers(activities, filters = {}) {
        // Clear existing markers
        this.activityCluster.clearLayers();
        
        if (!activities || !Array.isArray(activities)) {
            console.warn('MapVisualization: Invalid activities data provided');
            return;
        }

        const markersToAdd = [];
        
        activities.forEach(activity => {
            // Apply filters
            if (this.shouldFilterActivity(activity, filters)) return;
            
            const marker = this.createActivityMarker(activity);
            if (marker) {
                markersToAdd.push(marker);
            }
        });
        
        // Add markers to cluster in batch
        this.activityCluster.addLayers(markersToAdd);
        
        console.log(`MapVisualization: Updated ${markersToAdd.length} activity markers`);
    }

    /**
     * Check if activity should be filtered out
     * @private
     */
    shouldFilterActivity(activity, filters) {
        if (filters.types && filters.types.length > 0) {
            return !filters.types.includes(activity.type);
        }
        return false;
    }

    /**
     * Create activity marker
     * @private
     */
    createActivityMarker(activity) {
        const icon = this.getActivityIcon(activity.type);
        
        const marker = L.marker([activity.lat, activity.lon], {
            icon: L.divIcon({
                className: 'activity-marker',
                html: `
                    <div class="activity-icon" data-type="${activity.type}">
                        ${icon}
                    </div>
                `,
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            })
        });
        
        // Create popup content
        const popupContent = this.createActivityPopupContent(activity);
        marker.bindPopup(popupContent, {
            maxWidth: 300,
            className: 'activity-popup'
        });
        
        return marker;
    }

    /**
     * Create activity popup content
     * @private
     */
    createActivityPopupContent(activity) {
        return `
            <div class="activity-popup-content">
                <div class="popup-header">
                    <h3>${this.getActivityIcon(activity.type)} ${activity.nom}</h3>
                    <span class="type">${activity.type}</span>
                </div>
                <p class="description">${activity.description}</p>
                <div class="actions">
                    <button onclick="weatherApp.centerOnActivity('${activity.nom}')" 
                            class="btn-primary">
                        📍 Centrer
                    </button>
                    <button onclick="weatherApp.addToRoute(${JSON.stringify(activity).replace(/"/g, '&quot;')})" 
                            class="btn-secondary">
                        ➕ Route
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Get activity icon based on type
     * @param {string} type - Activity type
     * @returns {string} Icon emoji
     */
    getActivityIcon(type) {
        const iconMap = {
            'plage': '🏖️',
            'randonnee': '🥾',
            'velo': '🚴',
            'escalade': '🧗',
            'voile': '⛵',
            'surf': '🏄',
            'kayak': '🛶',
            'parapente': '🪂',
            'ski': '⛷️',
            'observation': '🔭',
            'photographie': '📸',
            'peche': '🎣',
            'camping': '⛺',
            'baignade': '🏊',
            'default': '📍'
        };
        
        return iconMap[type] || iconMap.default;
    }

    /**
     * Create weather cluster icon
     * @private
     */
    createWeatherClusterIcon(cluster) {
        const childCount = cluster.getChildCount();
        let className = 'weather-cluster-';
        
        if (childCount < 10) {
            className += 'small';
        } else if (childCount < 100) {
            className += 'medium';
        } else {
            className += 'large';
        }
        
        return L.divIcon({
            html: `<div><span>${childCount}</span></div>`,
            className: `marker-cluster ${className}`,
            iconSize: [40, 40]
        });
    }

    /**
     * Create activity cluster icon
     * @private
     */
    createActivityClusterIcon(cluster) {
        const childCount = cluster.getChildCount();
        let className = 'activity-cluster-';
        
        if (childCount < 10) {
            className += 'small';
        } else if (childCount < 100) {
            className += 'medium';
        } else {
            className += 'large';
        }
        
        return L.divIcon({
            html: `<div><span>${childCount}</span></div>`,
            className: `marker-cluster ${className}`,
            iconSize: [40, 40]
        });
    }

    /**
     * Update custom spots on map
     * @param {Array} spots - Custom spots array
     */
    updateCustomSpots(spots) {
        this.customSpotsGroup.clearLayers();
        
        if (!spots || !Array.isArray(spots)) return;
        
        spots.forEach(spot => {
            const marker = this.createCustomSpotMarker(spot);
            if (marker) {
                this.customSpotsGroup.addLayer(marker);
            }
        });
    }

    /**
     * Create custom spot marker
     * @private
     */
    createCustomSpotMarker(spot) {
        const icon = L.divIcon({
            className: 'custom-spot-marker',
            html: `
                <div class="custom-spot-icon" data-type="${spot.type}">
                    ${this.getActivityIcon(spot.type)}
                </div>
            `,
            iconSize: [35, 35],
            iconAnchor: [17, 17]
        });
        
        const marker = L.marker([spot.lat, spot.lng], { icon });
        
        // Add click handler
        marker.on('click', () => {
            this.emit('customSpotClicked', { spot });
        });
        
        return marker;
    }

    /**
     * Fit map to show custom spots
     */
    fitToCustomSpots() {
        const spots = [];
        this.customSpotsGroup.eachLayer(layer => {
            spots.push(layer.getLatLng());
        });
        
        if (spots.length > 0) {
            const group = new L.featureGroup(this.customSpotsGroup.getLayers());
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    /**
     * Simple event emitter
     * @param {string} event - Event name  
     * @param {Object} data - Event data
     */
    emit(event, data = {}) {
        const customEvent = new CustomEvent(`mapVisualization:${event}`, {
            detail: { ...data, timestamp: Date.now() }
        });
        document.dispatchEvent(customEvent);
    }

    /**
     * Listen to visualization events
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    on(event, handler) {
        document.addEventListener(`mapVisualization:${event}`, handler);
    }

    /**
     * Cleanup visualization layers
     */
    destroy() {
        this.weatherCluster.clearLayers();
        this.activityCluster.clearLayers();
        this.customSpotsGroup.clearLayers();
        
        this.map.removeLayer(this.weatherCluster);
        this.map.removeLayer(this.activityCluster);
        this.map.removeLayer(this.customSpotsGroup);
    }
}

export default MapVisualization;