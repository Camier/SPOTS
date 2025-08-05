/**
 * Simple Map Providers for Main Map
 * Provides basic map tile providers that work without API keys
 */

export const MapProviders = {
    providers: {
        ign: {
            name: 'IGN Plan',
            layer: () => L.tileLayer(
                'https://data.geopf.fr/wmts?' +
                'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&' +
                'LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&' +
                'TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&' +
                'FORMAT=image/png',
                {
                    attribution: '© IGN',
                    maxZoom: 18
                }
            )
        },
        osm: {
            name: 'OpenStreetMap',
            layer: () => L.tileLayer(
                'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                {
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19
                }
            )
        },
        satellite: {
            name: 'Satellite',
            layer: () => L.tileLayer(
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                {
                    attribution: '© Esri',
                    maxZoom: 18
                }
            )
        },
        terrain: {
            name: 'Terrain',
            layer: () => L.tileLayer(
                'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                {
                    attribution: '© OpenTopoMap',
                    maxZoom: 17
                }
            )
        }
    }
};

export default MapProviders;