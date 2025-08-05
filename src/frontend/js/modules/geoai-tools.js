/**
 * GeoAI Tools Module
 * Advanced spatial analysis and measurement tools
 */

export class GeoAITools {
    constructor(map) {
        this.map = map;
        this.activeTools = new Set();
        this.measurements = [];
        this.drawnItems = new L.FeatureGroup();
        this.map.addLayer(this.drawnItems);
        
        // Tool states
        this.tools = {
            measure: {
                polyline: null,
                markers: [],
                distances: []
            },
            elevation: {
                points: [],
                chart: null
            },
            routing: {
                start: null,
                end: null,
                route: null
            },
            spatial: {
                analysisArea: null,
                results: null
            }
        };
    }
    
    // Distance measurement tool
    enableMeasurement() {
        this.disableAllTools();
        this.activeTools.add('measure');
        
        this.map.getContainer().style.cursor = 'crosshair';
        this.map.on('click', this.measureClick, this);
        
        // Show measurement instructions
        this.showTooltip('Cliquez pour placer des points. Double-clic pour terminer.');
    }
    
    measureClick(e) {
        const tools = this.tools.measure;
        
        // Add marker
        const marker = L.marker(e.latlng, {
            icon: L.divIcon({
                className: 'measure-marker',
                html: `<div style="background: white; border: 2px solid #3498db; width: 10px; height: 10px; border-radius: 50%;"></div>`,
                iconSize: [10, 10]
            })
        }).addTo(this.drawnItems);
        
        tools.markers.push(marker);
        
        // Update polyline
        if (tools.markers.length > 1) {
            const latlngs = tools.markers.map(m => m.getLatLng());
            
            if (tools.polyline) {
                tools.polyline.setLatLngs(latlngs);
            } else {
                tools.polyline = L.polyline(latlngs, {
                    color: '#3498db',
                    weight: 3,
                    opacity: 0.8,
                    dashArray: '5, 10'
                }).addTo(this.drawnItems);
            }
            
            // Calculate total distance
            let totalDistance = 0;
            for (let i = 1; i < latlngs.length; i++) {
                totalDistance += latlngs[i-1].distanceTo(latlngs[i]);
            }
            
            // Show distance
            marker.bindPopup(`Distance totale: ${this.formatDistance(totalDistance)}`).openPopup();
        }
        
        this.map.on('dblclick', () => {
            this.disableMeasurement();
        });
    }
    
    disableMeasurement() {
        this.map.off('click', this.measureClick);
        this.map.getContainer().style.cursor = '';
        this.activeTools.delete('measure');
    }
    
    // Elevation profile tool
    async enableElevationProfile() {
        this.disableAllTools();
        this.activeTools.add('elevation');
        
        this.map.getContainer().style.cursor = 'crosshair';
        this.showTooltip('Cliquez pour définir le début et la fin du profil');
        
        const points = [];
        
        const clickHandler = async (e) => {
            points.push(e.latlng);
            
            L.marker(e.latlng, {
                icon: L.divIcon({
                    className: 'elevation-marker',
                    html: `<div style="background: #e74c3c; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px;">${points.length === 1 ? 'Départ' : 'Arrivée'}</div>`,
                    iconSize: [60, 20]
                })
            }).addTo(this.drawnItems);
            
            if (points.length === 2) {
                this.map.off('click', clickHandler);
                this.map.getContainer().style.cursor = '';
                
                // Draw line
                L.polyline(points, {
                    color: '#e74c3c',
                    weight: 4,
                    opacity: 0.8
                }).addTo(this.drawnItems);
                
                // Get elevation data
                await this.showElevationProfile(points[0], points[1]);
            }
        };
        
        this.map.on('click', clickHandler);
    }
    
    async showElevationProfile(start, end) {
        // Simulate elevation data (in real app, would call IGN elevation API)
        const distance = start.distanceTo(end);
        const steps = Math.min(100, Math.floor(distance / 100));
        
        const profile = [];
        for (let i = 0; i <= steps; i++) {
            const ratio = i / steps;
            const lat = start.lat + (end.lat - start.lat) * ratio;
            const lng = start.lng + (end.lng - start.lng) * ratio;
            
            // Simulate elevation based on location
            const elevation = 200 + Math.sin(lat * 50) * 100 + Math.cos(lng * 50) * 50 + Math.random() * 20;
            
            profile.push({
                distance: (distance * ratio) / 1000, // km
                elevation: Math.round(elevation)
            });
        }
        
        // Show profile in popup
        this.showElevationChart(profile);
    }
    
    showElevationChart(profile) {
        // Create simple elevation display
        const maxElev = Math.max(...profile.map(p => p.elevation));
        const minElev = Math.min(...profile.map(p => p.elevation));
        const range = maxElev - minElev;
        
        let chartHtml = `
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
                <h3 style="margin: 0 0 15px 0;">📊 Profil d'altitude</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span>Distance: ${profile[profile.length-1].distance.toFixed(1)} km</span>
                    <span>Dénivelé: ${range.toFixed(0)} m</span>
                </div>
                <div style="height: 150px; position: relative; border: 1px solid #ddd; background: #f9f9f9;">
        `;
        
        // Simple ASCII-style chart
        profile.forEach((point, i) => {
            const x = (i / profile.length) * 100;
            const y = ((point.elevation - minElev) / range) * 100;
            chartHtml += `<div style="position: absolute; bottom: ${y}%; left: ${x}%; width: 2px; height: 2px; background: #3498db;"></div>`;
        });
        
        chartHtml += `
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 12px;">
                    <span>${minElev.toFixed(0)}m</span>
                    <span>${maxElev.toFixed(0)}m</span>
                </div>
            </div>
        `;
        
        const popup = L.popup({
            maxWidth: 400,
            maxHeight: 300
        })
        .setLatLng(this.map.getCenter())
        .setContent(chartHtml)
        .openOn(this.map);
    }
    
    // Routing tool
    enableRouting() {
        this.disableAllTools();
        this.activeTools.add('routing');
        
        this.map.getContainer().style.cursor = 'crosshair';
        this.showTooltip('Cliquez pour définir le départ, puis l\'arrivée');
        
        let start = null;
        
        const clickHandler = async (e) => {
            if (!start) {
                start = e.latlng;
                L.marker(start, {
                    icon: L.divIcon({
                        className: 'routing-marker',
                        html: '<div style="background: #27ae60; color: white; padding: 4px 8px; border-radius: 4px;">🚶 Départ</div>',
                        iconSize: [80, 25]
                    })
                }).addTo(this.drawnItems);
                
                this.showTooltip('Cliquez pour définir l\'arrivée');
            } else {
                const end = e.latlng;
                L.marker(end, {
                    icon: L.divIcon({
                        className: 'routing-marker',
                        html: '<div style="background: #e74c3c; color: white; padding: 4px 8px; border-radius: 4px;">🏁 Arrivée</div>',
                        iconSize: [80, 25]
                    })
                }).addTo(this.drawnItems);
                
                this.map.off('click', clickHandler);
                this.map.getContainer().style.cursor = '';
                
                // Calculate simple route
                await this.calculateRoute(start, end);
            }
        };
        
        this.map.on('click', clickHandler);
    }
    
    async calculateRoute(start, end) {
        // Simulate route (in real app, would use IGN routing API)
        const route = [start];
        
        // Add some intermediate points
        const steps = 10;
        for (let i = 1; i < steps; i++) {
            const ratio = i / steps;
            const lat = start.lat + (end.lat - start.lat) * ratio;
            const lng = start.lng + (end.lng - start.lng) * ratio;
            
            // Add some randomness to simulate real path
            const offsetLat = (Math.random() - 0.5) * 0.002;
            const offsetLng = (Math.random() - 0.5) * 0.002;
            
            route.push(L.latLng(lat + offsetLat, lng + offsetLng));
        }
        route.push(end);
        
        // Draw route
        const routeLine = L.polyline(route, {
            color: '#27ae60',
            weight: 4,
            opacity: 0.8
        }).addTo(this.drawnItems);
        
        // Calculate stats
        let totalDistance = 0;
        for (let i = 1; i < route.length; i++) {
            totalDistance += route[i-1].distanceTo(route[i]);
        }
        
        // Show route info
        const popup = L.popup()
            .setLatLng(end)
            .setContent(`
                <div style="padding: 10px;">
                    <h4 style="margin: 0 0 10px 0;">🚶 Itinéraire</h4>
                    <p><strong>Distance:</strong> ${this.formatDistance(totalDistance)}</p>
                    <p><strong>Temps estimé:</strong> ${Math.round(totalDistance / 80)} min</p>
                    <p><strong>Difficulté:</strong> Modérée</p>
                </div>
            `)
            .openOn(this.map);
    }
    
    // Spatial analysis tool
    enableSpatialAnalysis() {
        this.disableAllTools();
        this.activeTools.add('spatial');
        
        this.showTooltip('Dessinez une zone pour analyser les spots');
        
        // Enable drawing rectangle
        const drawControl = new L.Control.Draw({
            draw: {
                polygon: false,
                polyline: false,
                circle: false,
                marker: false,
                circlemarker: false,
                rectangle: {
                    shapeOptions: {
                        color: '#9b59b6',
                        weight: 2,
                        opacity: 0.8,
                        fillOpacity: 0.2
                    }
                }
            }
        });
        
        this.map.addControl(drawControl);
        
        this.map.on('draw:created', (e) => {
            const layer = e.layer;
            this.drawnItems.addLayer(layer);
            
            // Analyze spots in area
            this.analyzeArea(layer.getBounds());
            
            // Remove draw control
            this.map.removeControl(drawControl);
        });
    }
    
    analyzeArea(bounds) {
        // Get all markers in bounds
        const spotsInArea = [];
        
        this.map.eachLayer((layer) => {
            if (layer instanceof L.Marker && layer.spotData) {
                const latlng = layer.getLatLng();
                if (bounds.contains(latlng)) {
                    spotsInArea.push(layer.spotData);
                }
            }
        });
        
        // Analyze
        const analysis = {
            total: spotsInArea.length,
            byType: {},
            avgBeauty: 0,
            avgDifficulty: 0
        };
        
        let beautySum = 0;
        let difficultySum = 0;
        let beautyCount = 0;
        let difficultyCount = 0;
        
        spotsInArea.forEach(spot => {
            // Count by type
            analysis.byType[spot.type] = (analysis.byType[spot.type] || 0) + 1;
            
            // Average ratings
            if (spot.beauty_rating) {
                beautySum += spot.beauty_rating;
                beautyCount++;
            }
            if (spot.difficulty) {
                difficultySum += spot.difficulty;
                difficultyCount++;
            }
        });
        
        if (beautyCount > 0) analysis.avgBeauty = (beautySum / beautyCount).toFixed(1);
        if (difficultyCount > 0) analysis.avgDifficulty = (difficultySum / difficultyCount).toFixed(1);
        
        // Show results
        this.showAnalysisResults(analysis, bounds.getCenter());
    }
    
    showAnalysisResults(analysis, center) {
        let content = `
            <div style="padding: 15px; min-width: 250px;">
                <h3 style="margin: 0 0 15px 0;">🔍 Analyse spatiale</h3>
                <p><strong>Spots trouvés:</strong> ${analysis.total}</p>
        `;
        
        if (analysis.total > 0) {
            content += '<p><strong>Par type:</strong></p><ul style="margin: 5px 0; padding-left: 20px;">';
            for (const [type, count] of Object.entries(analysis.byType)) {
                content += `<li>${type}: ${count}</li>`;
            }
            content += '</ul>';
            
            if (analysis.avgBeauty > 0) {
                content += `<p><strong>Beauté moyenne:</strong> ${'⭐'.repeat(Math.round(analysis.avgBeauty))}</p>`;
            }
            if (analysis.avgDifficulty > 0) {
                content += `<p><strong>Difficulté moyenne:</strong> ${analysis.avgDifficulty}/5</p>`;
            }
        }
        
        content += '</div>';
        
        L.popup()
            .setLatLng(center)
            .setContent(content)
            .openOn(this.map);
    }
    
    // 3D View simulation
    enable3DView() {
        this.showTooltip('Vue 3D en cours de développement. Utilisez l\'ombrage du relief en attendant!');
        
        // Suggest enabling hillshade layer
        setTimeout(() => {
            const hillshadeCheckbox = document.querySelector('#layer-hillshade');
            if (hillshadeCheckbox && !hillshadeCheckbox.checked) {
                hillshadeCheckbox.click();
                this.showTooltip('Couche d\'ombrage activée pour simuler le relief');
            }
        }, 1000);
    }
    
    // Utility methods
    disableAllTools() {
        this.activeTools.forEach(tool => {
            switch(tool) {
                case 'measure':
                    this.disableMeasurement();
                    break;
            }
        });
        
        this.drawnItems.clearLayers();
        this.map.getContainer().style.cursor = '';
    }
    
    formatDistance(meters) {
        if (meters < 1000) {
            return `${Math.round(meters)} m`;
        }
        return `${(meters / 1000).toFixed(2)} km`;
    }
    
    showTooltip(message) {
        // Remove existing tooltip
        const existing = document.querySelector('.geoai-tooltip');
        if (existing) existing.remove();
        
        const tooltip = document.createElement('div');
        tooltip.className = 'geoai-tooltip';
        tooltip.style.cssText = `
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 14px;
            z-index: 10000;
            animation: fadeIn 0.3s;
        `;
        tooltip.textContent = message;
        document.body.appendChild(tooltip);
        
        // Auto remove after 5 seconds
        setTimeout(() => tooltip.remove(), 5000);
    }
}

// CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
`;
document.head.appendChild(style);