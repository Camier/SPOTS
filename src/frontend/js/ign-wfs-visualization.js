/**
 * IGN WFS Visualization Module
 * Handles map visualization and layer management
 */

import { IGN_WFS_CONFIG } from './ign-wfs-config.js';
import { 
    getTransportStyle, 
    getHydrographyStyle,
    formatDistance,
    createLeafletBounds,
    processTransportFeatures,
    processHydrographyFeatures,
    createFeatureSummary
} from './ign-wfs-utils.js';

export class IGNWFSVisualization {
    constructor(api) {
        this.api = api;
        this.activeLayers = new Map();
        this.layerControl = null;
    }
    
    /**
     * Visualize complete spot environment
     */
    async visualizeSpotEnvironment(map, spotId, coordinates) {
        const [lat, lon] = coordinates;
        
        try {
            // Clear existing layers
            this.clearAllLayers();
            
            // Add analysis radius circle
            const radius = 1500;
            const radiusCircle = L.circle([lat, lon], {
                radius: radius,
                ...IGN_WFS_CONFIG.layerStyles.analysisOverlay.radius
            }).addTo(map);
            
            this.activeLayers.set('radius', radiusCircle);
            
            // Get WFS analysis
            const analysis = await this.api.getSpotWFSAnalysis(spotId, radius);
            
            if (!analysis || !analysis.success) {
                console.warn('No WFS analysis available');
                return;
            }
            
            // Visualize transport network
            if (analysis.transport && analysis.transport.features) {
                this.visualizeTransportLayer(map, analysis.transport.features, lat, lon);
            }
            
            // Visualize hydrography
            if (analysis.hydrography && analysis.hydrography.features) {
                this.visualizeHydrographyLayer(map, analysis.hydrography.features, lat, lon);
            }
            
            // Add layer control
            this.addLayerControl(map);
            
            // Fit map to show all features
            const allBounds = [];
            this.activeLayers.forEach(layer => {
                if (layer.getBounds) {
                    allBounds.push(layer.getBounds());
                }
            });
            
            if (allBounds.length > 0) {
                const combinedBounds = allBounds.reduce((acc, bounds) => acc.extend(bounds));
                map.fitBounds(combinedBounds, { padding: [50, 50] });
            }
            
            return analysis;
            
        } catch (error) {
            console.error('Failed to visualize environment:', error);
            this.showError(map, 'Unable to load IGN data');
            return null;
        }
    }
    
    /**
     * Visualize transport network layer
     */
    visualizeTransportLayer(map, features, centerLat, centerLon) {
        const transportGroup = L.featureGroup();
        const processedFeatures = processTransportFeatures(features, centerLat, centerLon);
        
        processedFeatures.forEach(feature => {
            const layer = L.geoJSON(feature, {
                style: getTransportStyle(feature.properties),
                onEachFeature: (feat, lyr) => {
                    const props = feat.properties;
                    const popup = IGN_WFS_CONFIG.popupTemplates.transport(props);
                    lyr.bindPopup(popup);
                    
                    // Add distance to popup
                    if (props.distance) {
                        lyr.bindPopup(popup + `<p><strong>Distance:</strong> ${formatDistance(props.distance)}</p>`);
                    }
                }
            });
            
            transportGroup.addLayer(layer);
        });
        
        transportGroup.addTo(map);
        this.activeLayers.set('transport', transportGroup);
        
        // Create summary
        const summary = createFeatureSummary(processedFeatures, 'transport');
        console.log('Transport network summary:', summary);
    }
    
    /**
     * Visualize hydrography layer
     */
    visualizeHydrographyLayer(map, features, centerLat, centerLon) {
        const hydroGroup = L.featureGroup();
        const processedFeatures = processHydrographyFeatures(features, centerLat, centerLon);
        
        processedFeatures.forEach(feature => {
            const style = getHydrographyStyle(feature);
            let layer;
            
            if (feature.geometry.type === 'Point') {
                // Create circle marker for points
                const coords = feature.geometry.coordinates;
                layer = L.circleMarker([coords[1], coords[0]], style);
            } else {
                // Create regular GeoJSON layer
                layer = L.geoJSON(feature, { style });
            }
            
            // Add popup
            const props = feature.properties;
            const popup = IGN_WFS_CONFIG.popupTemplates.hydrography(props);
            layer.bindPopup(popup + `<p><strong>Distance:</strong> ${formatDistance(props.distance)}</p>`);
            
            hydroGroup.addLayer(layer);
        });
        
        hydroGroup.addTo(map);
        this.activeLayers.set('hydrography', hydroGroup);
        
        // Create summary
        const summary = createFeatureSummary(processedFeatures, 'hydrography');
        console.log('Hydrography summary:', summary);
    }
    
    /**
     * Visualize administrative boundaries
     */
    async visualizeAdministrativeBoundaries(map, bbox, level = 'commune') {
        try {
            const data = await this.api.queryAdministrativeBoundaries(bbox, level);
            
            if (!data || !data.features) {
                console.warn('No administrative data available');
                return;
            }
            
            const adminGroup = L.featureGroup();
            const style = IGN_WFS_CONFIG.layerStyles.administrative[level];
            
            data.features.forEach(feature => {
                const layer = L.geoJSON(feature, {
                    style,
                    onEachFeature: (feat, lyr) => {
                        const popup = IGN_WFS_CONFIG.popupTemplates.administrative(feat.properties);
                        lyr.bindPopup(popup);
                    }
                });
                
                adminGroup.addLayer(layer);
            });
            
            adminGroup.addTo(map);
            this.activeLayers.set(`admin_${level}`, adminGroup);
            
        } catch (error) {
            console.error('Failed to visualize administrative boundaries:', error);
        }
    }
    
    /**
     * Add layer control to map
     */
    addLayerControl(map) {
        // Remove existing control
        if (this.layerControl) {
            map.removeControl(this.layerControl);
        }
        
        const overlays = {};
        
        if (this.activeLayers.has('transport')) {
            overlays['🚗 Transport Network'] = this.activeLayers.get('transport');
        }
        if (this.activeLayers.has('hydrography')) {
            overlays['💧 Hydrography'] = this.activeLayers.get('hydrography');
        }
        if (this.activeLayers.has('admin_commune')) {
            overlays['🏘️ Communes'] = this.activeLayers.get('admin_commune');
        }
        if (this.activeLayers.has('radius')) {
            overlays['📍 Analysis Radius'] = this.activeLayers.get('radius');
        }
        
        if (Object.keys(overlays).length > 0) {
            this.layerControl = L.control.layers(null, overlays, {
                position: 'topright',
                collapsed: false
            }).addTo(map);
        }
    }
    
    /**
     * Clear all active layers
     */
    clearAllLayers() {
        this.activeLayers.forEach((layer, key) => {
            if (layer && layer.remove) {
                layer.remove();
            }
        });
        this.activeLayers.clear();
    }
    
    /**
     * Show error message on map
     */
    showError(map, message) {
        const errorControl = L.control({ position: 'topright' });
        
        errorControl.onAdd = function() {
            const div = L.DomUtil.create('div', 'ign-error-message');
            div.innerHTML = `
                <div style="background: #ff5252; color: white; padding: 10px; border-radius: 4px;">
                    <strong>⚠️ ${message}</strong>
                </div>
            `;
            return div;
        };
        
        errorControl.addTo(map);
        
        // Remove after 5 seconds
        setTimeout(() => {
            map.removeControl(errorControl);
        }, 5000);
    }
    
    /**
     * Create feature summary panel
     */
    createSummaryPanel(map, analysis) {
        const summaryControl = L.control({ position: 'bottomleft' });
        
        summaryControl.onAdd = function() {
            const div = L.DomUtil.create('div', 'ign-summary-panel');
            
            let html = '<div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">';
            html += '<h4 style="margin: 0 0 10px 0;">📊 Analyse IGN</h4>';
            
            if (analysis.transport && analysis.transport.summary) {
                const transport = analysis.transport.summary;
                html += `
                    <div style="margin-bottom: 10px;">
                        <strong>🚗 Transport:</strong><br>
                        ${transport.total} éléments trouvés<br>
                        ${transport.nearest ? `Plus proche: ${transport.nearest.name} (${formatDistance(transport.nearest.distance)})` : ''}
                    </div>
                `;
            }
            
            if (analysis.hydrography && analysis.hydrography.summary) {
                const hydro = analysis.hydrography.summary;
                html += `
                    <div>
                        <strong>💧 Hydrographie:</strong><br>
                        ${hydro.total} éléments trouvés<br>
                        ${hydro.nearest ? `Plus proche: ${hydro.nearest.name} (${formatDistance(hydro.nearest.distance)})` : ''}
                    </div>
                `;
            }
            
            html += '</div>';
            div.innerHTML = html;
            
            return div;
        };
        
        summaryControl.addTo(map);
        this.activeLayers.set('summary', summaryControl);
    }
}

export default IGNWFSVisualization;