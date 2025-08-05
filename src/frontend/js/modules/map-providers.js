/**
 * Premium Map Providers Configuration
 * High-quality map tiles from the best providers
 */

export class PremiumMapProviders {
    constructor() {
        this.providers = {};
        this.apiKeys = {
            // Add your API keys here
            mapbox: 'YOUR_MAPBOX_TOKEN', // Get free at mapbox.com
            maptiler: 'YOUR_MAPTILER_KEY', // Get free at maptiler.com
            thunderforest: 'YOUR_THUNDERFOREST_KEY', // Get at thunderforest.com
            stadiamaps: 'YOUR_STADIA_KEY', // Optional - works without key for testing
            here: 'YOUR_HERE_API_KEY', // Get at developer.here.com
        };
    }

    /**
     * Get all premium map providers
     * @returns {Object} Map providers with their tile layers
     */
    getProviders() {
        // MAPBOX - Best overall quality and customization
        // Free tier: 50,000 map loads/month
        if (this.apiKeys.mapbox && this.apiKeys.mapbox !== 'YOUR_MAPBOX_TOKEN') {
            this.providers['Mapbox Satellite'] = L.tileLayer(
                `https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=${this.apiKeys.mapbox}`, {
                    attribution: '© Mapbox © OpenStreetMap',
                    maxZoom: 22,
                    tileSize: 512,
                    zoomOffset: -1
                }
            );

            this.providers['Mapbox Outdoors'] = L.tileLayer(
                `https://api.mapbox.com/styles/v1/mapbox/outdoors-v12/tiles/{z}/{x}/{y}?access_token=${this.apiKeys.mapbox}`, {
                    attribution: '© Mapbox © OpenStreetMap',
                    maxZoom: 22,
                    tileSize: 512,
                    zoomOffset: -1
                }
            );

            this.providers['Mapbox Streets'] = L.tileLayer(
                `https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{z}/{x}/{y}?access_token=${this.apiKeys.mapbox}`, {
                    attribution: '© Mapbox © OpenStreetMap',
                    maxZoom: 22,
                    tileSize: 512,
                    zoomOffset: -1
                }
            );
        }

        // MAPTILER - Excellent European coverage
        // Free tier: 100,000 requests/month
        if (this.apiKeys.maptiler && this.apiKeys.maptiler !== 'YOUR_MAPTILER_KEY') {
            this.providers['MapTiler Satellite'] = L.tileLayer(
                `https://api.maptiler.com/maps/hybrid/{z}/{x}/{y}.jpg?key=${this.apiKeys.maptiler}`, {
                    attribution: '© MapTiler © OpenStreetMap contributors',
                    maxZoom: 20,
                    tileSize: 512,
                    zoomOffset: -1
                }
            );

            this.providers['MapTiler Outdoor'] = L.tileLayer(
                `https://api.maptiler.com/maps/outdoor-v2/{z}/{x}/{y}.png?key=${this.apiKeys.maptiler}`, {
                    attribution: '© MapTiler © OpenStreetMap contributors',
                    maxZoom: 20,
                    tileSize: 512,
                    zoomOffset: -1
                }
            );

            this.providers['MapTiler Topo'] = L.tileLayer(
                `https://api.maptiler.com/maps/topo-v2/{z}/{x}/{y}.png?key=${this.apiKeys.maptiler}`, {
                    attribution: '© MapTiler © OpenStreetMap contributors',
                    maxZoom: 20,
                    tileSize: 512,
                    zoomOffset: -1
                }
            );
        }

        // THUNDERFOREST - Specialized outdoor maps
        // Free tier: 150,000 tiles/month
        if (this.apiKeys.thunderforest && this.apiKeys.thunderforest !== 'YOUR_THUNDERFOREST_KEY') {
            this.providers['Thunderforest Outdoors'] = L.tileLayer(
                `https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=${this.apiKeys.thunderforest}`, {
                    attribution: '© Thunderforest © OpenStreetMap contributors',
                    maxZoom: 22
                }
            );

            this.providers['Thunderforest Landscape'] = L.tileLayer(
                `https://tile.thunderforest.com/landscape/{z}/{x}/{y}.png?apikey=${this.apiKeys.thunderforest}`, {
                    attribution: '© Thunderforest © OpenStreetMap contributors',
                    maxZoom: 22
                }
            );

            this.providers['Thunderforest Cycle'] = L.tileLayer(
                `https://tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=${this.apiKeys.thunderforest}`, {
                    attribution: '© Thunderforest © OpenStreetMap contributors',
                    maxZoom: 22
                }
            );
        }

        // ESRI/ArcGIS - Professional grade, no API key needed for basic use
        this.providers['ESRI World Imagery'] = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                maxZoom: 19
            }
        );

        this.providers['ESRI World Topo'] = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community',
                maxZoom: 19
            }
        );

        this.providers['ESRI NatGeo'] = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC',
                maxZoom: 16
            }
        );

        // STADIA MAPS - Modern, fast, good free tier
        this.providers['Stadia Dark'] = L.tileLayer(
            'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
                maxZoom: 20
            }
        );

        this.providers['Stadia Bright'] = L.tileLayer(
            'https://tiles.stadiamaps.com/tiles/osm_bright/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
                maxZoom: 20
            }
        );

        this.providers['Stadia Outdoors'] = L.tileLayer(
            'https://tiles.stadiamaps.com/tiles/outdoors/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
                maxZoom: 20
            }
        );

        // CARTO - Great for data visualization
        this.providers['CARTO Positron'] = L.tileLayer(
            'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }
        );

        this.providers['CARTO Dark Matter'] = L.tileLayer(
            'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }
        );

        this.providers['CARTO Voyager'] = L.tileLayer(
            'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }
        );

        // OpenTopoMap - Excellent topographic detail
        this.providers['OpenTopoMap'] = L.tileLayer(
            'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
                maxZoom: 17
            }
        );

        // CyclOSM - Cycling focused
        this.providers['CyclOSM'] = L.tileLayer(
            'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png', {
                attribution: '<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 20
            }
        );

        // Geoportail France - Official French maps (best for France!)
        const ignApiKey = window.IGN_API_KEY || 'essentiels'; // Use environment key or fallback to essentiels
        
        // Main layers
        this.providers['IGN Plan v2'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">Geoportail France</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 0,
                maxZoom: 18
            }
        );

        this.providers['IGN Satellite'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">Geoportail France</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 0,
                maxZoom: 19
            }
        );
        
        // SCAN Régional - Regional topographic maps at 1:250,000 scale
        this.providers['IGN SCAN Regional'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-REGIONAL&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">IGN SCAN Régional</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 6,
                maxZoom: 13
            }
        );
        
        // Additional IGN layers
        this.providers['IGN Scan 25'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">Geoportail France</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 0,
                maxZoom: 16
            }
        );
        
        this.providers['IGN Cadastre'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">Geoportail France</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 0,
                maxZoom: 20
            }
        );
        
        // Ancient Forests layer
        this.providers['IGN Ancient Forests'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=LANDCOVER.FORESTINVENTORY.V2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">Geoportail France</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 0,
                maxZoom: 16,
                opacity: 0.7
            }
        );
        
        // Hydrography layer
        this.providers['IGN Hydrography'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=HYDROGRAPHY.HYDROGRAPHY&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">Geoportail France</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 6,
                maxZoom: 18,
                opacity: 0.8
            }
        );
        
        // Natural Habitats layer (INPN-CARHAB)
        this.providers['IGN Natural Habitats'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/environnement/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=PROTECTEDAREAS.ZNIEFF1&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">INPN - Inventaire National du Patrimoine Naturel</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 0,
                maxZoom: 16,
                opacity: 0.7
            }
        );
        
        // Protected Areas layer
        this.providers['IGN Protected Areas'] = L.tileLayer(
            `https://wxs.ign.fr/${ignApiKey}/environnement/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=PROTECTEDAREAS.APB&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png`, {
                attribution: '<a target="_blank" href="https://www.geoportail.gouv.fr/">INPN - Protected Areas</a>',
                bounds: [[-75, -180], [81, 180]],
                minZoom: 0,
                maxZoom: 16,
                opacity: 0.6
            }
        );

        // Sentinel-2 cloudless - True color satellite without clouds
        this.providers['Sentinel-2'] = L.tileLayer(
            'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg', {
                attribution: '<a href="https://s2maps.eu" target="_blank">Sentinel-2 cloudless - https://s2maps.eu</a> by <a href="https://eox.at/" target="_blank">EOX IT Services GmbH</a> (Contains modified Copernicus Sentinel data 2020)',
                maxZoom: 18
            }
        );

        return this.providers;
    }

    /**
     * Get recommended providers that don't require API keys
     */
    getFreeProviders() {
        return {
            'ESRI World Imagery': this.providers['ESRI World Imagery'],
            'ESRI World Topo': this.providers['ESRI World Topo'],
            'CARTO Positron': this.providers['CARTO Positron'],
            'CARTO Dark Matter': this.providers['CARTO Dark Matter'],
            'OpenTopoMap': this.providers['OpenTopoMap'],
            'CyclOSM': this.providers['CyclOSM'],
            'IGN Satellite': this.providers['IGN Satellite'],
            'Sentinel-2': this.providers['Sentinel-2'],
            'Stadia Outdoors': this.providers['Stadia Outdoors']
        };
    }
}

export default PremiumMapProviders;
