/**
 * IGN Geoservices Integration
 * Official French geographic data and services
 * https://geoservices.ign.fr/
 */

export class IGNGeoservices {
    constructor() {
        // IGN Geoservices base URLs
        this.endpoints = {
            // Base URL for web services
            base: 'https://data.geopf.fr',
            
            // Administrative boundaries
            adminExpress: 'https://data.geopf.fr/annexes/ressources/admin-express/2024/',
            
            // Geocoding service
            geocode: 'https://data.geopf.fr/geocodage/search',
            reverse: 'https://data.geopf.fr/geocodage/reverse',
            
            // Elevation service
            alti: 'https://data.geopf.fr/altimetrie',
            
            // WMS/WMTS services
            wmts: 'https://data.geopf.fr/wmts',
            wms: 'https://data.geopf.fr/wms-r',
            
            // Vector tiles
            vectorTiles: 'https://data.geopf.fr/tms/1.0.0/'
        };
        
        // Available IGN layers
        this.layers = {
            // Cartes (Maps)
            'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2': {
                name: 'Plan IGN v2',
                type: 'wmts',
                format: 'image/png',
                style: 'normal',
                description: 'Cartographie multi-échelles du territoire français'
            },
            
            // Photographies aériennes
            'ORTHOIMAGERY.ORTHOPHOTOS': {
                name: 'Photographies aériennes',
                type: 'wmts', 
                format: 'image/jpeg',
                style: 'normal',
                description: 'Ortho-photographies haute résolution'
            },
            
            // Parcelles cadastrales
            'CADASTRALPARCELS.PARCELLAIRE_EXPRESS': {
                name: 'Parcellaire Express',
                type: 'wmts',
                format: 'image/png',
                style: 'PCI vecteur',
                description: 'Limites des parcelles cadastrales'
            },
            
            // Cartes topographiques
            'GEOGRAPHICALGRIDSYSTEMS.MAPS': {
                name: 'Cartes IGN',
                type: 'wmts',
                format: 'image/jpeg',
                style: 'normal',
                description: 'Cartes topographiques IGN classiques'
            },
            
            // SCAN 25 Touristique
            'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR': {
                name: 'SCAN 25 Touristique',
                type: 'wmts',
                format: 'image/jpeg',
                style: 'normal',
                description: 'Cartes touristiques au 1:25000'
            }
        };
    }
    
    /**
     * Get WMTS tile URL for IGN layers
     */
    getWMTSTileUrl(layer) {
        return `https://data.geopf.fr/wmts?` +
            `SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&` +
            `LAYER=${layer}&STYLE=normal&TILEMATRIXSET=PM&` +
            `TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=${this.layers[layer]?.format || 'image/png'}`;
    }
    
    /**
     * Get department boundaries GeoJSON
     */
    async getDepartmentBoundaries(deptCode) {
        const url = `${this.endpoints.adminExpress}DEPARTEMENT_CARTO.json`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            // Filter for specific department if code provided
            if (deptCode) {
                data.features = data.features.filter(
                    feature => feature.properties.CODE_DEPT === deptCode
                );
            }
            
            return data;
        } catch (error) {
            console.error('Error fetching department boundaries:', error);
            return null;
        }
    }
    
    /**
     * Get commune boundaries for a department
     */
    async getCommuneBoundaries(deptCode) {
        const url = `${this.endpoints.adminExpress}COMMUNE_CARTO_${deptCode}.json`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching commune boundaries:', error);
            return null;
        }
    }
    
    /**
     * Geocode an address using IGN service
     */
    async geocode(query, options = {}) {
        const params = new URLSearchParams({
            q: query,
            limit: options.limit || 5,
            ...options
        });
        
        const url = `${this.endpoints.geocode}?${params}`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            return data.features;
        } catch (error) {
            console.error('Error geocoding address:', error);
            return null;
        }
    }
    
    /**
     * Reverse geocode coordinates
     */
    async reverseGeocode(lat, lon) {
        const params = new URLSearchParams({
            lat: lat,
            lon: lon
        });
        
        const url = `${this.endpoints.reverse}?${params}`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            return data.features[0];
        } catch (error) {
            console.error('Error reverse geocoding:', error);
            return null;
        }
    }
    
    /**
     * Get elevation for coordinates
     */
    async getElevation(lat, lon) {
        const url = `${this.endpoints.alti}/rest/elevation.json?lat=${lat}&lon=${lon}`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            return data.elevations[0];
        } catch (error) {
            console.error('Error fetching elevation:', error);
            return null;
        }
    }
    
    /**
     * Create Leaflet layers for IGN services
     */
    createLeafletLayers() {
        const layers = {};
        
        // Plan IGN v2 (detailed maps)
        layers['IGN Plan'] = L.tileLayer(
            this.getWMTSTileUrl('GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2'), {
                attribution: '© IGN-F/Geoportail',
                maxZoom: 18,
                minZoom: 0
            }
        );
        
        // Photographies aériennes (satellite)
        layers['IGN Satellite'] = L.tileLayer(
            this.getWMTSTileUrl('ORTHOIMAGERY.ORTHOPHOTOS'), {
                attribution: '© IGN-F/Geoportail',
                maxZoom: 20,
                minZoom: 0
            }
        );
        
        // Cartes IGN classiques
        layers['IGN Cartes'] = L.tileLayer(
            this.getWMTSTileUrl('GEOGRAPHICALGRIDSYSTEMS.MAPS'), {
                attribution: '© IGN-F/Geoportail',
                maxZoom: 18,
                minZoom: 0
            }
        );
        
        // SCAN 25 Touristique
        layers['IGN Tourisme'] = L.tileLayer(
            this.getWMTSTileUrl('GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR'), {
                attribution: '© IGN-F/Geoportail',
                maxZoom: 16,
                minZoom: 0
            }
        );
        
        // Cadastre
        layers['IGN Cadastre'] = L.tileLayer(
            this.getWMTSTileUrl('CADASTRALPARCELS.PARCELLAIRE_EXPRESS'), {
                attribution: '© IGN-F/Geoportail',
                maxZoom: 20,
                minZoom: 0,
                opacity: 0.7
            }
        );
        
        return layers;
    }
    
    /**
     * Load and display department boundaries on map
     */
    async addDepartmentBoundaries(map, departments) {
        const colors = {
            '09': '#2563eb', // Ariège
            '12': '#059669', // Aveyron
            '31': '#dc2626', // Haute-Garonne
            '32': '#7c3aed', // Gers
            '46': '#ea580c', // Lot
            '65': '#0891b2', // Hautes-Pyrénées
            '81': '#84cc16', // Tarn
            '82': '#f59e0b'  // Tarn-et-Garonne
        };
        
        for (const deptCode of departments) {
            const boundaries = await this.getDepartmentBoundaries(deptCode);
            
            if (boundaries) {
                L.geoJSON(boundaries, {
                    style: {
                        color: colors[deptCode] || '#666',
                        weight: 3,
                        opacity: 0.8,
                        fillOpacity: 0.1
                    },
                    onEachFeature: (feature, layer) => {
                        layer.bindTooltip(feature.properties.NOM_DEPT, {
                            permanent: false,
                            direction: 'center'
                        });
                    }
                }).addTo(map);
            }
        }
    }
}

export default IGNGeoservices;
