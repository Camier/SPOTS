/**
 * Sun & Shadow Plugin for Leaflet
 * Lightweight integration for the optimized map
 */

// Import as module or use global SunCalc
const SunCalc = window.SunCalc || await import('suncalc');

export function addSunShadowControls(map) {
    let isActive = false;
    let shadowLayer = L.layerGroup();
    let currentTime = new Date();
    
    // Create control button
    const SunControl = L.Control.extend({
        options: {
            position: 'topright'
        },

        onAdd: function(map) {
            const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            const button = L.DomUtil.create('a', '', container);
            
            button.href = '#';
            button.title = 'Calculateur Soleil/Ombre';
            button.innerHTML = '☀️';
            button.style.fontSize = '20px';
            button.style.lineHeight = '30px';
            button.style.width = '30px';
            button.style.height = '30px';
            button.style.textAlign = 'center';
            
            L.DomEvent.on(button, 'click', function(e) {
                L.DomEvent.preventDefault(e);
                toggleSunShadow();
            });
            
            return container;
        }
    });
    
    // Add control to map
    map.addControl(new SunControl());
    
    // Sun info panel
    let infoPanel = null;
    
    function createInfoPanel() {
        const InfoPanel = L.Control.extend({
            options: {
                position: 'topright'
            },
            
            onAdd: function(map) {
                const div = L.DomUtil.create('div', 'sun-info-panel');
                div.innerHTML = `
                    <div style="
                        background: white;
                        padding: 10px;
                        border-radius: 5px;
                        box-shadow: 0 1px 5px rgba(0,0,0,0.3);
                        margin-top: 10px;
                        font-size: 12px;
                    ">
                        <div><strong>Position Soleil</strong></div>
                        <div id="sun-info-time">--:--</div>
                        <div id="sun-info-position">Alt: --° | Az: --°</div>
                        <div style="margin-top: 5px;">
                            <input type="range" id="sun-time-mini" 
                                min="0" max="1440" step="15" 
                                style="width: 150px;">
                        </div>
                        <div style="margin-top: 5px; display: flex; gap: 3px;">
                            <button onclick="setSunTime('sunrise')" style="flex: 1; font-size: 11px;">Lever</button>
                            <button onclick="setSunTime('noon')" style="flex: 1; font-size: 11px;">Midi</button>
                            <button onclick="setSunTime('sunset')" style="flex: 1; font-size: 11px;">Coucher</button>
                        </div>
                    </div>
                `;
                
                L.DomEvent.disableClickPropagation(div);
                L.DomEvent.disableScrollPropagation(div);
                
                return div;
            }
        });
        
        infoPanel = new InfoPanel();
        map.addControl(infoPanel);
        
        // Set up time slider
        const slider = document.getElementById('sun-time-mini');
        const currentMinutes = currentTime.getHours() * 60 + currentTime.getMinutes();
        slider.value = currentMinutes;
        
        slider.addEventListener('input', function(e) {
            const minutes = parseInt(e.target.value);
            currentTime.setHours(Math.floor(minutes / 60));
            currentTime.setMinutes(minutes % 60);
            updateSunDisplay();
        });
    }
    
    function updateSunDisplay() {
        const center = map.getCenter();
        const sunPos = SunCalc.getPosition(currentTime, center.lat, center.lng);
        
        const altitude = (sunPos.altitude * 180 / Math.PI).toFixed(1);
        const azimuth = ((sunPos.azimuth * 180 / Math.PI + 180) % 360).toFixed(1);
        
        document.getElementById('sun-info-time').textContent = 
            currentTime.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        document.getElementById('sun-info-position').textContent = 
            `Alt: ${altitude}° | Az: ${azimuth}°`;
        
        // Update shadow visualization
        updateShadows(parseFloat(altitude), parseFloat(azimuth));
    }
    
    function updateShadows(altitude, azimuth) {
        shadowLayer.clearLayers();
        
        if (altitude <= 0) return; // Sun below horizon
        
        // Simple shadow visualization
        const shadowOpacity = Math.max(0.1, 0.4 * (1 - altitude / 90));
        const shadowLength = Math.min(100, 50 / Math.tan(altitude * Math.PI / 180));
        
        // Get visible spots on map
        map.eachLayer(function(layer) {
            if (layer instanceof L.Marker && layer.getLatLng) {
                const pos = layer.getLatLng();
                
                // Create shadow polygon
                const shadowAzimuthRad = (azimuth + 180) * Math.PI / 180;
                const shadowEnd = L.latLng(
                    pos.lat + shadowLength * 0.00001 * Math.cos(shadowAzimuthRad),
                    pos.lng + shadowLength * 0.00001 * Math.sin(shadowAzimuthRad)
                );
                
                const shadow = L.polygon([
                    [pos.lat, pos.lng],
                    [pos.lat + 0.0001, pos.lng],
                    [shadowEnd.lat + 0.0001, shadowEnd.lng],
                    [shadowEnd.lat, shadowEnd.lng]
                ], {
                    color: 'transparent',
                    fillColor: '#000033',
                    fillOpacity: shadowOpacity,
                    interactive: false
                });
                
                shadowLayer.addLayer(shadow);
            }
        });
    }
    
    // Global function for button clicks
    window.setSunTime = function(type) {
        const center = map.getCenter();
        const times = SunCalc.getTimes(new Date(), center.lat, center.lng);
        
        switch(type) {
            case 'sunrise':
                currentTime = new Date(times.sunrise);
                break;
            case 'noon':
                currentTime = new Date(times.solarNoon);
                break;
            case 'sunset':
                currentTime = new Date(times.sunset);
                break;
        }
        
        const minutes = currentTime.getHours() * 60 + currentTime.getMinutes();
        document.getElementById('sun-time-mini').value = minutes;
        updateSunDisplay();
    };
    
    function toggleSunShadow() {
        isActive = !isActive;
        
        if (isActive) {
            shadowLayer.addTo(map);
            createInfoPanel();
            updateSunDisplay();
            
            // Update on map move
            map.on('moveend', updateSunDisplay);
        } else {
            shadowLayer.remove();
            if (infoPanel) {
                map.removeControl(infoPanel);
                infoPanel = null;
            }
            map.off('moveend', updateSunDisplay);
        }
    }
    
    return {
        toggle: toggleSunShadow,
        update: updateSunDisplay,
        isActive: () => isActive
    };
}

// Auto-init if map exists
if (window.spotMap) {
    window.sunShadowControl = addSunShadowControls(window.spotMap);
}