/**
 * Main Map Application
 * Production-ready interactive map for SPOTS project
 */

import { MapProviders } from './modules/map-providers-simple.js';
import { WeatherService } from './modules/weather-service-simple.js';
import { IGNGeoservices } from './modules/ign-geoservices.js';
import { SunShadowCalculator } from './modules/sun-shadow-calculator.js';

class MainMapApp {
    constructor() {
        this.map = null;
        this.markers = new L.MarkerClusterGroup({
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: true
        });
        this.spots = [];
        this.currentFilters = {
            types: [],
            difficulty: [],
            distance: 200,
            weatherOnly: false
        };
        this.userLocation = null;
        this.weatherService = new WeatherService();
        this.ignService = new IGNGeoservices();
        this.sunCalculator = null;
        this.currentBaseLayer = null;
        this.overlays = {};
        
        // API configuration
        this.API_BASE = 'http://localhost:8000/api';
        
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        try {
            this.showLoading(true);
            
            // Initialize map
            this.initMap();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load initial data
            await this.loadSpots();
            
            // Initialize additional features
            this.initializeGeolocation();
            this.initializeLayers();
            this.initializeSearch();
            
            // Initialize sun/shadow calculator
            this.sunCalculator = new SunShadowCalculator(this.map);
            
            this.showLoading(false);
        } catch (error) {
            console.error('Initialization error:', error);
            this.showError('Erreur lors du chargement de la carte');
            this.showLoading(false);
        }
    }

    initMap() {
        // Initialize map centered on Occitanie
        this.map = L.map('map', {
            center: [43.8927, 1.8827], // Center of Occitanie
            zoom: 8,
            zoomControl: false,
            preferCanvas: true
        });

        // Add zoom control in custom position
        L.control.zoom({
            position: 'topright'
        }).addTo(this.map);

        // Add default IGN layer
        const ignLayer = MapProviders.providers.ign.layer();
        ignLayer.addTo(this.map);
        this.currentBaseLayer = ignLayer;

        // Add marker cluster group
        this.map.addLayer(this.markers);

        // Add scale control
        L.control.scale({
            imperial: false,
            position: 'bottomleft'
        }).addTo(this.map);

        // Make map globally accessible for debugging
        window._mainMap = this.map;
    }

    setupEventListeners() {
        // Header controls
        document.getElementById('geolocateBtn').addEventListener('click', () => this.geolocate());
        document.getElementById('layersBtn').addEventListener('click', () => this.toggleLayersPanel());
        document.getElementById('filtersBtn').addEventListener('click', () => this.togglePanel('filtersPanel'));
        document.getElementById('weatherBtn').addEventListener('click', () => this.toggleWeather());
        document.getElementById('addSpotBtn').addEventListener('click', () => this.showAddSpotModal());
        
        // Search
        document.getElementById('searchBtn').addEventListener('click', () => this.performSearch());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });

        // Filter controls
        document.getElementById('distanceRange').addEventListener('input', (e) => {
            document.getElementById('distanceValue').textContent = e.target.value + ' km';
        });

        // Modal close buttons
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('.modal').style.display = 'none';
            });
        });

        // Add spot form
        document.getElementById('addSpotForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitNewSpot();
        });

        // Map click for adding spots
        this.map.on('click', (e) => {
            if (document.getElementById('addSpotModal').style.display === 'block') {
                this.setSpotPosition(e.latlng);
            }
        });

        // Cluster toggle
        document.getElementById('clustersToggle')?.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.enableClustering();
            } else {
                this.disableClustering();
            }
        });
    }

    async loadSpots() {
        try {
            const response = await fetch(`${this.API_BASE}/spots`);
            if (!response.ok) throw new Error('Failed to load spots');
            
            this.spots = await response.json();
            this.displaySpots();
            this.updateSpotCounter();
            
        } catch (error) {
            console.error('Error loading spots:', error);
            // For now, create some demo spots if API fails
            this.createDemoSpots();
        }
    }

    displaySpots() {
        this.markers.clearLayers();
        
        const filteredSpots = this.filterSpots(this.spots);
        
        filteredSpots.forEach(spot => {
            const marker = this.createSpotMarker(spot);
            this.markers.addLayer(marker);
        });
    }

    createSpotMarker(spot) {
        const icons = {
            randonnee: '🥾',
            baignade: '🏊',
            point_de_vue: '👁️',
            patrimoine: '🏛️',
            grotte: '🕳️',
            cascade: '💦',
            default: '📍'
        };

        const icon = L.divIcon({
            html: `<div class="custom-marker">${icons[spot.type] || icons.default}</div>`,
            className: 'spot-marker',
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        });

        const marker = L.marker([spot.latitude, spot.longitude], { icon });
        
        // Create popup content
        const popupContent = `
            <div class="spot-popup">
                <h3>${spot.name}</h3>
                <p class="spot-type">${icons[spot.type]} ${this.getTypeLabel(spot.type)}</p>
                ${spot.description ? `<p>${spot.description}</p>` : ''}
                <button class="btn-primary btn-small" onclick="app.showSpotDetails(${spot.id})">
                    Plus d'infos →
                </button>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        marker.spotData = spot;
        
        return marker;
    }

    filterSpots(spots) {
        return spots.filter(spot => {
            // Type filter
            if (this.currentFilters.types.length > 0 && 
                !this.currentFilters.types.includes(spot.type)) {
                return false;
            }
            
            // Difficulty filter
            if (this.currentFilters.difficulty.length > 0 && 
                spot.difficulty && 
                !this.currentFilters.difficulty.includes(spot.difficulty)) {
                return false;
            }
            
            // Distance filter
            if (this.userLocation && this.currentFilters.distance < 200) {
                const distance = this.calculateDistance(
                    this.userLocation.lat,
                    this.userLocation.lng,
                    spot.latitude,
                    spot.longitude
                );
                if (distance > this.currentFilters.distance) {
                    return false;
                }
            }
            
            return true;
        });
    }

    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    getTypeLabel(type) {
        const labels = {
            randonnee: 'Randonnée',
            baignade: 'Baignade',
            point_de_vue: 'Point de vue',
            patrimoine: 'Patrimoine',
            grotte: 'Grotte',
            cascade: 'Cascade'
        };
        return labels[type] || type;
    }

    updateSpotCounter() {
        const counter = document.getElementById('spotCounter');
        const count = this.spots.length;
        counter.textContent = `${count} spot${count > 1 ? 's' : ''} chargé${count > 1 ? 's' : ''}`;
    }

    // Geolocation
    initializeGeolocation() {
        if ('geolocation' in navigator) {
            // Check for existing location permission
            navigator.permissions.query({ name: 'geolocation' }).then(result => {
                if (result.state === 'granted') {
                    this.geolocate(false);
                }
            });
        }
    }

    async geolocate(showAlert = true) {
        if (!navigator.geolocation) {
            if (showAlert) alert('La géolocalisation n\'est pas disponible');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                this.userLocation = { lat: latitude, lng: longitude };
                
                // Add/update user marker
                if (this.userMarker) {
                    this.userMarker.setLatLng([latitude, longitude]);
                } else {
                    this.userMarker = L.marker([latitude, longitude], {
                        icon: L.divIcon({
                            html: '<div class="user-location-marker">📍</div>',
                            className: 'user-marker',
                            iconSize: [30, 30]
                        })
                    }).addTo(this.map);
                    this.userMarker.bindPopup('Vous êtes ici');
                }
                
                if (showAlert) {
                    this.map.setView([latitude, longitude], 11);
                }
            },
            (error) => {
                if (showAlert) {
                    alert('Impossible d\'obtenir votre position');
                }
                console.error('Geolocation error:', error);
            }
        );
    }

    // Layers management
    initializeLayers() {
        const baseLayersContainer = document.getElementById('baseLayers');
        const ignLayersContainer = document.getElementById('ignLayers');
        
        if (!baseLayersContainer) {
            console.error('Base layers container not found');
            return;
        }
        
        // Create layer buttons
        const layers = [
            { key: 'ign', name: 'IGN Plan', icon: '🗺️' },
            { key: 'osm', name: 'OSM', icon: '🌍' },
            { key: 'satellite', name: 'Satellite', icon: '🛰️' },
            { key: 'terrain', name: 'Terrain', icon: '⛰️' }
        ];
        
        layers.forEach(layer => {
            const button = document.createElement('button');
            button.className = 'layer-btn' + (layer.key === 'ign' ? ' active' : '');
            button.setAttribute('data-layer', layer.key);
            button.innerHTML = `${layer.icon} ${layer.name}`;
            button.addEventListener('click', () => {
                this.switchBaseLayer(layer.key);
                // Update active state
                document.querySelectorAll('.layer-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                button.classList.add('active');
            });
            baseLayersContainer.appendChild(button);
        });
        
        // IGN specific overlays with improved forest layer
        if (ignLayersContainer) {
            const ignOverlays = [
                { id: 'forest', name: '🌲 Forêts', layer: 'LANDCOVER.FORESTINVENTORY.V2' },
                { id: 'cadastre', name: '📐 Cadastre', layer: 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS' },
                { id: 'elevation', name: '📏 Altitude', layer: 'ELEVATION.SLOPES' }
            ];
            
            ignOverlays.forEach(overlay => {
                const label = document.createElement('label');
                label.className = 'layer-option';
                label.innerHTML = `
                    <input type="checkbox" id="${overlay.id}Overlay" value="${overlay.id}">
                    <span>${overlay.name}</span>
                `;
                label.querySelector('input').addEventListener('change', (e) => {
                    this.toggleIGNOverlay(overlay.id, overlay.layer, e.target.checked);
                });
                ignLayersContainer.appendChild(label);
            });
            
            // Add heatmap toggle
            const heatmapLabel = document.createElement('label');
            heatmapLabel.className = 'layer-option';
            heatmapLabel.innerHTML = `
                <input type="checkbox" id="heatmapToggle">
                <span>🔥 Zone de chaleur</span>
            `;
            heatmapLabel.querySelector('input').addEventListener('change', (e) => {
                this.toggleHeatmap(e.target.checked);
            });
            ignLayersContainer.appendChild(heatmapLabel);
        }
        
        // Add sun control
        this.addSunControl();
    }

    switchBaseLayer(providerKey) {
        if (this.currentBaseLayer) {
            this.map.removeLayer(this.currentBaseLayer);
        }
        
        let newLayer;
        switch(providerKey) {
            case 'ign':
                newLayer = MapProviders.providers.ign.layer();
                break;
            case 'osm':
                newLayer = MapProviders.providers.osm.layer();
                break;
            case 'satellite':
                newLayer = MapProviders.providers.satellite.layer();
                break;
            case 'terrain':
                newLayer = MapProviders.providers.terrain.layer();
                break;
            default:
                const provider = MapProviders.providers[providerKey];
                if (provider) {
                    newLayer = provider.layer();
                }
        }
        
        if (newLayer) {
            this.currentBaseLayer = newLayer;
            this.currentBaseLayer.addTo(this.map);
        }
    }
    
    toggleLayersPanel() {
        this.togglePanel('layersPanel');
    }
    
    togglePanel(panelId) {
        const panel = document.getElementById(panelId);
        if (panel) {
            panel.classList.toggle('active');
        }
    }

    toggleIGNOverlay(id, layerName, enabled) {
        if (enabled) {
            if (!this.overlays[id]) {
                // Special handling for different overlay types
                const opacity = id === 'forest' ? 0.65 : 0.7;
                const style = id === 'forest' ? 'bdparcellaire' : 'normal';
                
                this.overlays[id] = L.tileLayer(
                    `https://data.geopf.fr/wmts?` +
                    `SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&` +
                    `LAYER=${layerName}&STYLE=${style}&` +
                    `TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&` +
                    `FORMAT=image/png`,
                    {
                        attribution: '© IGN',
                        opacity: opacity,
                        maxZoom: 18
                    }
                );
            }
            this.overlays[id].addTo(this.map);
        } else {
            if (this.overlays[id]) {
                this.map.removeLayer(this.overlays[id]);
            }
        }
    }
    
    // Heatmap functionality
    toggleHeatmap(enabled) {
        if (enabled) {
            if (!this.heatmapLayer) {
                // Create heatmap from spot data
                const heatData = this.spots.map(spot => [
                    spot.latitude,
                    spot.longitude,
                    spot.popularity || 0.5
                ]).filter(data => data[0] && data[1]); // Filter out invalid coordinates
                
                // Check if we have the heatmap plugin
                if (typeof L.heatLayer === 'undefined') {
                    console.warn('Leaflet.heat plugin not loaded, creating simple circles');
                    // Fallback to simple circles
                    this.heatmapLayer = L.layerGroup();
                    heatData.forEach(([lat, lng, intensity]) => {
                        L.circle([lat, lng], {
                            radius: 1000 * (1 + intensity),
                            fillColor: 'red',
                            fillOpacity: 0.3 * intensity,
                            stroke: false
                        }).addTo(this.heatmapLayer);
                    });
                } else {
                    this.heatmapLayer = L.heatLayer(heatData, {
                        radius: 25,
                        blur: 15,
                        maxZoom: 15,
                        gradient: {
                            0.0: 'blue',
                            0.3: 'cyan',
                            0.5: 'lime',
                            0.7: 'yellow',
                            1.0: 'red'
                        }
                    });
                }
            }
            this.map.addLayer(this.heatmapLayer);
        } else {
            if (this.heatmapLayer) {
                this.map.removeLayer(this.heatmapLayer);
            }
        }
    }
    
    // Sun control
    addSunControl() {
        const SunControl = L.Control.extend({
            options: {
                position: 'topright'
            },
            
            onAdd: (map) => {
                const container = L.DomUtil.create('div', 'leaflet-control leaflet-bar');
                const button = L.DomUtil.create('a', '', container);
                button.href = '#';
                button.title = 'Calculateur Soleil/Ombre';
                button.innerHTML = '☀️';
                button.style.fontSize = '20px';
                button.style.lineHeight = '30px';
                
                L.DomEvent.disableClickPropagation(container);
                L.DomEvent.on(button, 'click', (e) => {
                    L.DomEvent.preventDefault(e);
                    this.toggleSunCalculator();
                });
                
                return container;
            }
        });
        
        new SunControl().addTo(this.map);
    }
    
    async toggleSunCalculator() {
        if (!this.sunCalculator) {
            // Initialize sun calculator
            const { SunShadowCalculator } = await import('./modules/sun-shadow-calculator.js');
            this.sunCalculator = new SunShadowCalculator(this.map, this.ignService);
            await this.sunCalculator.init();
        }
        
        if (this.sunCalculatorActive) {
            this.sunCalculator.deactivate();
            this.sunCalculatorActive = false;
        } else {
            this.sunCalculator.activate();
            this.sunCalculatorActive = true;
        }
    }

    // Search functionality
    initializeSearch() {
        // Add geocoder control (hidden by default)
        this.geocoder = L.Control.Geocoder.nominatim({
            geocodingQueryParams: {
                countrycodes: 'fr',
                viewbox: '-1.8,42.3,4.9,45.0', // Occitanie bounding box
                bounded: 1
            }
        });
    }

    async performSearch() {
        const query = document.getElementById('searchInput').value.trim();
        if (!query) return;
        
        // Search in spots
        const matchingSpots = this.spots.filter(spot => 
            spot.name.toLowerCase().includes(query.toLowerCase()) ||
            (spot.description && spot.description.toLowerCase().includes(query.toLowerCase()))
        );
        
        if (matchingSpots.length > 0) {
            // Zoom to first matching spot
            const spot = matchingSpots[0];
            this.map.setView([spot.latitude, spot.longitude], 14);
            
            // Open popup
            this.markers.eachLayer(layer => {
                if (layer.spotData && layer.spotData.id === spot.id) {
                    layer.openPopup();
                }
            });
        } else {
            // Try geocoding
            this.geocoder.geocode(query, (results) => {
                if (results.length > 0) {
                    const result = results[0];
                    this.map.setView(result.center, 12);
                    L.popup()
                        .setLatLng(result.center)
                        .setContent(result.name)
                        .openOn(this.map);
                } else {
                    alert('Aucun résultat trouvé');
                }
            });
        }
    }

    // Weather integration
    async toggleWeather() {
        this.togglePanel('weatherPanel');
        
        const content = document.getElementById('weatherContent');
        content.innerHTML = '<div class="loading">Chargement de la météo...</div>';
        
        try {
            // Get weather for map center
            const center = this.map.getCenter();
            const weather = await this.weatherService.getWeatherData(center.lat, center.lng);
            
            content.innerHTML = this.renderWeatherInfo(weather);
        } catch (error) {
            console.error('Weather error:', error);
            content.innerHTML = '<div class="error">Impossible de charger la météo</div>';
        }
    }

    renderWeatherInfo(weather) {
        const current = weather.current_weather;
        const forecast = weather.daily;
        
        return `
            <div class="weather-current">
                <h4>Météo actuelle</h4>
                <div class="weather-temp">${Math.round(current.temperature)}°C</div>
                <p>Vent: ${current.windspeed} km/h</p>
            </div>
            
            <div class="weather-forecast">
                <h4>Prévisions</h4>
                ${forecast.time.slice(0, 4).map((date, i) => `
                    <div class="forecast-day">
                        <div>${new Date(date).toLocaleDateString('fr', { weekday: 'short' })}</div>
                        <div>${Math.round(forecast.temperature_2m_max[i])}°</div>
                        <div>${Math.round(forecast.temperature_2m_min[i])}°</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Panel management
    togglePanel(panelId) {
        const panel = document.getElementById(panelId);
        const isActive = panel.classList.contains('active');
        
        // Close all panels
        document.querySelectorAll('.sidebar-panel').forEach(p => {
            p.classList.remove('active');
        });
        
        // Toggle requested panel
        if (!isActive) {
            panel.classList.add('active');
        }
    }

    // Add spot functionality
    showAddSpotModal() {
        document.getElementById('addSpotModal').style.display = 'block';
        document.getElementById('spotPosition').textContent = 'Cliquez sur la carte pour définir la position';
        this.newSpotPosition = null;
    }

    setSpotPosition(latlng) {
        this.newSpotPosition = latlng;
        document.getElementById('spotPosition').textContent = 
            `Position: ${latlng.lat.toFixed(6)}, ${latlng.lng.toFixed(6)}`;
        
        // Add temporary marker
        if (this.tempMarker) {
            this.tempMarker.setLatLng(latlng);
        } else {
            this.tempMarker = L.marker(latlng, {
                icon: L.divIcon({
                    html: '<div class="temp-marker">📍</div>',
                    className: 'temp-marker-icon',
                    iconSize: [30, 30]
                })
            }).addTo(this.map);
        }
    }

    async submitNewSpot() {
        if (!this.newSpotPosition) {
            alert('Veuillez définir la position du spot sur la carte');
            return;
        }
        
        const formData = {
            name: document.getElementById('spotName').value,
            type: document.getElementById('spotType').value,
            description: document.getElementById('spotDescription').value,
            latitude: this.newSpotPosition.lat,
            longitude: this.newSpotPosition.lng,
            difficulty: document.getElementById('spotDifficulty').value,
            department: await this.getDepartmentFromCoords(
                this.newSpotPosition.lat, 
                this.newSpotPosition.lng
            )
        };
        
        try {
            const response = await fetch(`${this.API_BASE}/spots`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                const newSpot = await response.json();
                this.spots.push(newSpot);
                this.displaySpots();
                this.updateSpotCounter();
                
                // Close modal and cleanup
                document.getElementById('addSpotModal').style.display = 'none';
                document.getElementById('addSpotForm').reset();
                if (this.tempMarker) {
                    this.map.removeLayer(this.tempMarker);
                    this.tempMarker = null;
                }
                
                // Zoom to new spot
                this.map.setView([newSpot.latitude, newSpot.longitude], 14);
                
                alert('Spot ajouté avec succès !');
            } else {
                throw new Error('Failed to add spot');
            }
        } catch (error) {
            console.error('Error adding spot:', error);
            alert('Erreur lors de l\'ajout du spot');
        }
    }

    async getDepartmentFromCoords(lat, lng) {
        // Use reverse geocoding to get department
        // For now, return a default based on rough coordinates
        if (lat > 44.5) return '12'; // Aveyron
        if (lat < 42.8) return '66'; // Pyrénées-Orientales
        if (lng < 0.5) return '65'; // Hautes-Pyrénées
        if (lng > 3.5) return '30'; // Gard
        return '31'; // Haute-Garonne (default)
    }

    // Spot details
    async showSpotDetails(spotId) {
        const spot = this.spots.find(s => s.id === spotId);
        if (!spot) return;
        
        const modal = document.getElementById('spotModal');
        const details = document.getElementById('spotDetails');
        
        details.innerHTML = `
            <div class="spot-detail-header">
                <h2>${spot.name}</h2>
                <span class="spot-type-badge">${this.getTypeLabel(spot.type)}</span>
            </div>
            
            <div class="spot-detail-section">
                <h4>📍 Localisation</h4>
                <p>Coordonnées: ${spot.latitude.toFixed(6)}, ${spot.longitude.toFixed(6)}</p>
                <p>Département: ${spot.department}</p>
            </div>
            
            ${spot.description ? `
                <div class="spot-detail-section">
                    <h4>📝 Description</h4>
                    <p>${spot.description}</p>
                </div>
            ` : ''}
            
            <div class="spot-detail-section">
                <h4>🌤️ Météo actuelle</h4>
                <div id="spotWeather" class="loading">Chargement...</div>
            </div>
            
            <div class="spot-actions">
                <button class="btn-primary" onclick="app.navigateToSpot(${spot.latitude}, ${spot.longitude})">
                    🧭 Y aller
                </button>
                <button class="btn-secondary" onclick="app.shareSpot(${spot.id})">
                    📤 Partager
                </button>
            </div>
        `;
        
        modal.style.display = 'block';
        
        // Load weather for this spot
        this.loadSpotWeather(spot.latitude, spot.longitude);
    }

    async loadSpotWeather(lat, lng) {
        try {
            const weather = await this.weatherService.getWeatherData(lat, lng);
            const weatherDiv = document.getElementById('spotWeather');
            
            weatherDiv.innerHTML = `
                <p>🌡️ ${Math.round(weather.current_weather.temperature)}°C</p>
                <p>💨 Vent: ${weather.current_weather.windspeed} km/h</p>
            `;
        } catch (error) {
            document.getElementById('spotWeather').innerHTML = 
                '<p>Météo non disponible</p>';
        }
    }

    navigateToSpot(lat, lng) {
        // Open navigation in new tab (Google Maps or native app)
        const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
        window.open(url, '_blank');
    }

    shareSpot(spotId) {
        const spot = this.spots.find(s => s.id === spotId);
        if (!spot) return;
        
        const url = `${window.location.origin}${window.location.pathname}#spot=${spotId}`;
        const text = `Découvrez ce spot secret : ${spot.name}`;
        
        if (navigator.share) {
            navigator.share({
                title: spot.name,
                text: text,
                url: url
            });
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(url).then(() => {
                alert('Lien copié dans le presse-papier !');
            });
        }
    }

    // Filters
    applyFilters() {
        // Collect filter values
        this.currentFilters.types = Array.from(
            document.querySelectorAll('#typeFilters input:checked')
        ).map(input => input.value);
        
        this.currentFilters.difficulty = Array.from(
            document.querySelectorAll('#difficultyFilters input:checked')
        ).map(input => input.value);
        
        this.currentFilters.distance = parseInt(
            document.getElementById('distanceRange').value
        );
        
        this.currentFilters.weatherOnly = 
            document.getElementById('weatherFilter').checked;
        
        // Apply filters and refresh display
        this.displaySpots();
        
        // Close panel
        this.togglePanel('filtersPanel');
    }

    resetFilters() {
        // Reset all checkboxes
        document.querySelectorAll('.filter-chip input').forEach(input => {
            input.checked = true;
        });
        
        // Reset range
        document.getElementById('distanceRange').value = 200;
        document.getElementById('distanceValue').textContent = '200 km';
        
        // Reset weather filter
        document.getElementById('weatherFilter').checked = false;
        
        // Reset internal state
        this.currentFilters = {
            types: [],
            difficulty: [],
            distance: 200,
            weatherOnly: false
        };
        
        // Refresh display
        this.displaySpots();
    }

    // Clustering control
    enableClustering() {
        if (!this.map.hasLayer(this.markers)) {
            this.map.addLayer(this.markers);
            // Re-add all markers to cluster group
            this.displaySpots();
        }
    }

    disableClustering() {
        if (this.map.hasLayer(this.markers)) {
            this.map.removeLayer(this.markers);
            // Add markers directly to map
            const filteredSpots = this.filterSpots(this.spots);
            filteredSpots.forEach(spot => {
                const marker = this.createSpotMarker(spot);
                marker.addTo(this.map);
            });
        }
    }

    // Utility methods
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.classList.toggle('active', show);
    }

    showError(message) {
        // Could implement a toast notification system
        alert(message);
    }

    // Demo data creation
    createDemoSpots() {
        // Create some demo spots for testing
        this.spots = [
            {
                id: 1,
                name: "Lac de Saint-Ferréol",
                type: "baignade",
                latitude: 43.4486,
                longitude: 2.0197,
                description: "Magnifique lac artificiel avec plage aménagée",
                difficulty: "facile",
                department: "31"
            },
            {
                id: 2,
                name: "Pic du Canigou",
                type: "randonnee",
                latitude: 42.5194,
                longitude: 2.4569,
                description: "Montagne sacrée des Catalans, vue panoramique",
                difficulty: "difficile",
                department: "66"
            },
            {
                id: 3,
                name: "Gorges du Tarn",
                type: "point_de_vue",
                latitude: 44.3167,
                longitude: 3.2833,
                description: "Spectaculaires gorges calcaires",
                difficulty: "moyen",
                department: "48"
            },
            {
                id: 4,
                name: "Grotte de Niaux",
                type: "grotte",
                latitude: 42.8203,
                longitude: 1.5936,
                description: "Grotte préhistorique avec peintures rupestres",
                difficulty: "facile",
                department: "09"
            },
            {
                id: 5,
                name: "Cascade d'Ars",
                type: "cascade",
                latitude: 42.7833,
                longitude: 1.3667,
                description: "Impressionnante cascade de 246m en trois paliers",
                difficulty: "moyen",
                department: "09"
            }
        ];
        
        this.displaySpots();
        this.updateSpotCounter();
    }

    useMyLocation() {
        if (this.userLocation) {
            this.setSpotPosition(L.latLng(this.userLocation.lat, this.userLocation.lng));
        } else {
            this.geolocate(false);
            // Try again after geolocation
            setTimeout(() => {
                if (this.userLocation) {
                    this.setSpotPosition(L.latLng(this.userLocation.lat, this.userLocation.lng));
                }
            }, 2000);
        }
    }
}

// Global functions for onclick handlers
window.app = null;
window.togglePanel = (panelId) => window.app?.togglePanel(panelId);
window.applyFilters = () => window.app?.applyFilters();
window.resetFilters = () => window.app?.resetFilters();
window.useMyLocation = () => window.app?.useMyLocation();

// Initialize app
window.app = new MainMapApp();

// Export for debugging
export { MainMapApp };