/**
 * Urbex Layer Module for SPOTS Map
 * Handles display of urban exploration locations with safety indicators
 */

export class UrbexLayer {
    constructor(map) {
        this.map = map;
        this.markers = [];
        this.markerGroup = L.layerGroup();
        this.heatmapLayer = null;
        this.filters = {
            category: 'all',
            maxDanger: 4,
            showInactive: false
        };
        
        // Category icons and colors
        this.categoryStyles = {
            abandoned_building: { icon: '🏚️', color: '#8B4513' },
            industrial: { icon: '🏭', color: '#696969' },
            castle: { icon: '🏰', color: '#4B0082' },
            church: { icon: '⛪', color: '#800020' },
            hospital: { icon: '🏥', color: '#DC143C' },
            school: { icon: '🏫', color: '#FF8C00' },
            military: { icon: '🎖️', color: '#556B2F' },
            tunnel: { icon: '🚇', color: '#2F4F4F' },
            mine: { icon: '⛏️', color: '#696969' },
            quarry: { icon: '🪨', color: '#A0522D' },
            theme_park: { icon: '🎡', color: '#FF69B4' },
            hotel: { icon: '🏨', color: '#4169E1' },
            railway: { icon: '🚂', color: '#8B0000' },
            bunker: { icon: '🛡️', color: '#2F4F4F' },
            other: { icon: '❓', color: '#808080' }
        };
        
        // Danger level indicators
        this.dangerColors = {
            1: '#00FF00',  // Low - Green
            2: '#FFFF00',  // Medium - Yellow
            3: '#FF8C00',  // High - Orange
            4: '#FF0000'   // Extreme - Red
        };
    }
    
    async loadUrbexSpots() {
        try {
            const response = await fetch('/api/urbex/spots');
            const spots = await response.json();
            this.displaySpots(spots);
        } catch (error) {
            console.error('Error loading urbex spots:', error);
        }
    }
    
    displaySpots(spots) {
        // Clear existing markers
        this.clearMarkers();
        
        spots.forEach(spot => {
            if (this.shouldDisplaySpot(spot)) {
                const marker = this.createUrbexMarker(spot);
                this.markers.push(marker);
                this.markerGroup.addLayer(marker);
            }
        });
        
        this.markerGroup.addTo(this.map);
    }
    
    createUrbexMarker(spot) {
        const style = this.categoryStyles[spot.category] || this.categoryStyles.other;
        const dangerColor = this.dangerColors[spot.danger_level];
        
        // Create custom icon with danger indicator
        const icon = L.divIcon({
            html: `
                <div class="urbex-marker" style="border-color: ${dangerColor}">
                    <span class="urbex-icon">${style.icon}</span>
                    <span class="danger-indicator" style="background: ${dangerColor}"></span>
                </div>
            `,
            className: 'urbex-marker-wrapper',
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        });
        
        const marker = L.marker([spot.latitude, spot.longitude], { icon });
        
        // Create detailed popup
        const popup = this.createUrbexPopup(spot);
        marker.bindPopup(popup);
        
        // Add click handler
        marker.on('click', () => {
            this.onMarkerClick(spot);
        });
        
        return marker;
    }
    
    createUrbexPopup(spot) {
        const dangerLabel = ['Low', 'Medium', 'High', 'Extreme'][spot.danger_level - 1];
        const accessLabel = ['Easy', 'Moderate', 'Hard', 'Expert'][spot.access_difficulty - 1];
        
        let hazardsList = '';
        if (spot.hazards && spot.hazards.length > 0) {
            hazardsList = `
                <div class="hazards-list">
                    <strong>⚠️ Hazards:</strong>
                    <ul>
                        ${spot.hazards.map(h => `<li>${h}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        let accessNotes = '';
        if (spot.access_notes) {
            accessNotes = `
                <div class="access-notes">
                    <strong>📍 Access:</strong> ${spot.access_notes}
                </div>
            `;
        }
        
        const popupContent = `
            <div class="urbex-popup">
                <h3>${spot.name}</h3>
                <div class="urbex-meta">
                    <span class="category">${this.categoryStyles[spot.category].icon} ${spot.category.replace('_', ' ')}</span>
                    <span class="location">${spot.city || spot.department}</span>
                </div>
                
                <div class="urbex-safety">
                    <div class="danger-level" style="color: ${this.dangerColors[spot.danger_level]}">
                        ⚠️ Danger: ${dangerLabel}
                    </div>
                    <div class="access-difficulty">
                        🚶 Access: ${accessLabel}
                    </div>
                </div>
                
                ${hazardsList}
                ${accessNotes}
                
                <div class="urbex-info">
                    ${spot.year_abandoned ? `<p>📅 Abandoned: ${spot.year_abandoned}</p>` : ''}
                    ${spot.historical_use ? `<p>🏛️ Former: ${spot.historical_use}</p>` : ''}
                    ${spot.security_presence ? '<p>👮 Security present</p>' : ''}
                    ${spot.asbestos_risk ? '<p class="warning">☣️ Asbestos risk!</p>' : ''}
                </div>
                
                <div class="urbex-actions">
                    <button onclick="urbexLayer.showDetails('${spot.id}')">View Details</button>
                    <button onclick="urbexLayer.getDirections(${spot.latitude}, ${spot.longitude})">Directions</button>
                    ${spot.photos ? `<button onclick="urbexLayer.showPhotos('${spot.id}')">Photos</button>` : ''}
                </div>
            </div>
        `;
        
        return popupContent;
    }
    
    shouldDisplaySpot(spot) {
        // Apply filters
        if (this.filters.category !== 'all' && spot.category !== this.filters.category) {
            return false;
        }
        
        if (spot.danger_level > this.filters.maxDanger) {
            return false;
        }
        
        if (!this.filters.showInactive && !spot.is_active) {
            return false;
        }
        
        return true;
    }
    
    setFilter(filterType, value) {
        this.filters[filterType] = value;
        this.loadUrbexSpots(); // Reload with new filters
    }
    
    createHeatmap(spots) {
        // Create heatmap based on popularity
        const heatData = spots.map(spot => [
            spot.latitude,
            spot.longitude,
            spot.popularity_score / 100
        ]);
        
        if (this.heatmapLayer) {
            this.map.removeLayer(this.heatmapLayer);
        }
        
        this.heatmapLayer = L.heatLayer(heatData, {
            radius: 25,
            blur: 15,
            gradient: {
                0.0: 'blue',
                0.5: 'yellow',
                1.0: 'red'
            }
        });
        
        return this.heatmapLayer;
    }
    
    showDetails(spotId) {
        // Open detailed view in side panel
        window.dispatchEvent(new CustomEvent('urbex:showDetails', { 
            detail: { spotId } 
        }));
    }
    
    getDirections(lat, lng) {
        // Open directions in new tab
        const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
        window.open(url, '_blank');
    }
    
    showPhotos(spotId) {
        // Open photo gallery
        window.dispatchEvent(new CustomEvent('urbex:showPhotos', { 
            detail: { spotId } 
        }));
    }
    
    clearMarkers() {
        this.markerGroup.clearLayers();
        this.markers = [];
    }
    
    onMarkerClick(spot) {
        // Custom click handler
        console.log('Urbex spot clicked:', spot);
    }
    
    // Safety check for beginners
    checkBeginnerFriendly(spot) {
        return (
            spot.danger_level <= 2 &&
            spot.access_difficulty <= 2 &&
            !spot.asbestos_risk &&
            spot.is_active
        );
    }
    
    // Get spots suitable for beginners
    getBeginnerSpots(spots) {
        return spots.filter(spot => this.checkBeginnerFriendly(spot));
    }
    
    // Export spots as GeoJSON
    exportAsGeoJSON(spots) {
        const features = spots.map(spot => ({
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [spot.longitude, spot.latitude]
            },
            properties: {
                name: spot.name,
                category: spot.category,
                danger_level: spot.danger_level,
                access_difficulty: spot.access_difficulty,
                year_abandoned: spot.year_abandoned,
                hazards: spot.hazards
            }
        }));
        
        return {
            type: 'FeatureCollection',
            features: features
        };
    }
}

// Add CSS for urbex markers
const style = document.createElement('style');
style.textContent = `
    .urbex-marker-wrapper {
        background: transparent !important;
        border: none !important;
    }
    
    .urbex-marker {
        width: 40px;
        height: 40px;
        background: white;
        border-radius: 50%;
        border: 3px solid;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    
    .urbex-icon {
        font-size: 20px;
    }
    
    .danger-indicator {
        position: absolute;
        bottom: -5px;
        right: -5px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid white;
    }
    
    .urbex-popup {
        min-width: 300px;
    }
    
    .urbex-popup h3 {
        margin: 0 0 10px 0;
        color: #333;
    }
    
    .urbex-meta {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        font-size: 14px;
    }
    
    .urbex-safety {
        display: flex;
        gap: 15px;
        margin: 10px 0;
        padding: 10px;
        background: #f5f5f5;
        border-radius: 5px;
    }
    
    .hazards-list {
        margin: 10px 0;
        padding: 10px;
        background: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    
    .hazards-list ul {
        margin: 5px 0;
        padding-left: 20px;
    }
    
    .access-notes {
        margin: 10px 0;
        padding: 10px;
        background: #e8f4fd;
        border-left: 4px solid #2196F3;
    }
    
    .urbex-info {
        margin: 10px 0;
    }
    
    .urbex-info p {
        margin: 5px 0;
    }
    
    .warning {
        color: #d32f2f;
        font-weight: bold;
    }
    
    .urbex-actions {
        display: flex;
        gap: 10px;
        margin-top: 15px;
    }
    
    .urbex-actions button {
        flex: 1;
        padding: 8px;
        border: none;
        background: #2196F3;
        color: white;
        border-radius: 4px;
        cursor: pointer;
    }
    
    .urbex-actions button:hover {
        background: #1976D2;
    }
`;
document.head.appendChild(style);

export default UrbexLayer;