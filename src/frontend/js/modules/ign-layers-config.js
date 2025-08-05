/**
 * IGN Layers Configuration
 * Complete list of available IGN/Geoportail layers
 */

export const IGN_LAYERS = {
    // Cartes de base
    plan_ign: {
        name: 'Plan IGN V2',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Cartes de base',
        attribution: '© IGN',
        maxZoom: 18,
        default: true
    },
    
    satellite: {
        name: 'Orthophotographies',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg',
        category: 'Cartes de base',
        attribution: '© IGN',
        maxZoom: 19
    },
    
    scan25: {
        name: 'Carte TOP 25',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg',
        category: 'Cartes de base',
        attribution: '© IGN',
        maxZoom: 16
    },
    
    scan_express: {
        name: 'SCAN Express',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-EXPRESS.STANDARD&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg',
        category: 'Cartes de base',
        attribution: '© IGN',
        maxZoom: 18
    },
    
    // Cartes thématiques
    forest: {
        name: 'Forêts (BD Forêt)',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=LANDCOVER.FORESTINVENTORY.V2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Nature',
        attribution: '© IGN',
        opacity: 0.7,
        maxZoom: 16
    },
    
    geology: {
        name: 'Carte géologique',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOLOGIE.GEOL&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Nature',
        attribution: '© BRGM',
        opacity: 0.6,
        maxZoom: 14
    },
    
    hydrography: {
        name: 'Réseau hydrographique',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=HYDROGRAPHIE&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Nature',
        attribution: '© IGN',
        opacity: 0.8,
        maxZoom: 18
    },
    
    protected_areas: {
        name: 'Espaces protégés',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=PROTECTEDAREAS.MNHN.RESERVES-NATURELLES&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Nature',
        attribution: '© MNHN',
        opacity: 0.6,
        maxZoom: 16
    },
    
    // Cartes historiques
    cassini: {
        name: 'Carte de Cassini (XVIIIe)',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.CASSINI&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg',
        category: 'Historique',
        attribution: '© IGN',
        maxZoom: 15
    },
    
    etat_major: {
        name: 'État-Major (1820-1866)',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg',
        category: 'Historique',
        attribution: '© IGN',
        maxZoom: 15
    },
    
    // Relief et altitude
    elevation: {
        name: 'Courbes de niveau',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ELEVATION.CONTOUR.LINE&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Relief',
        attribution: '© IGN',
        opacity: 0.5,
        maxZoom: 17
    },
    
    slopes: {
        name: 'Carte des pentes',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ELEVATION.SLOPES&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Relief',
        attribution: '© IGN',
        opacity: 0.6,
        maxZoom: 15
    },
    
    hillshade: {
        name: 'Ombrage du relief',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ELEVATION.HILLSHADE&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Relief',
        attribution: '© IGN',
        opacity: 0.4,
        maxZoom: 15
    },
    
    // Données administratives
    cadastre: {
        name: 'Parcelles cadastrales',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Administratif',
        attribution: '© DGFiP',
        opacity: 0.6,
        minZoom: 14,
        maxZoom: 20
    },
    
    communes: {
        name: 'Limites communales',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=LIMITES_ADMINISTRATIVES_EXPRESS.LATEST&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Administratif',
        attribution: '© IGN',
        opacity: 0.7,
        maxZoom: 18
    },
    
    // Randonnée et tourisme
    hiking_trails: {
        name: 'Sentiers de randonnée',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=TRACES.SENTIERS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Tourisme',
        attribution: '© IGN',
        opacity: 0.9,
        maxZoom: 17
    },
    
    tourism: {
        name: 'Points d\'intérêt touristiques',
        url: 'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=TOURISME&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png',
        category: 'Tourisme',
        attribution: '© IGN',
        opacity: 0.8,
        maxZoom: 17
    }
};

// Preset layer combinations
export const LAYER_PRESETS = {
    hiking: {
        name: '🥾 Randonnée',
        layers: ['scan25', 'hiking_trails', 'elevation'],
        description: 'Idéal pour préparer vos randonnées'
    },
    
    exploration: {
        name: '🔍 Exploration',
        layers: ['satellite', 'forest', 'hydrography'],
        description: 'Pour découvrir des spots cachés'
    },
    
    heritage: {
        name: '🏛️ Patrimoine',
        layers: ['plan_ign', 'cassini', 'cadastre'],
        description: 'Comparer passé et présent'
    },
    
    nature: {
        name: '🌳 Nature',
        layers: ['satellite', 'forest', 'protected_areas'],
        description: 'Zones naturelles et forêts'
    },
    
    geology: {
        name: '⛰️ Géologie',
        layers: ['plan_ign', 'geology', 'slopes'],
        description: 'Comprendre le terrain'
    },
    
    water: {
        name: '💧 Points d\'eau',
        layers: ['scan25', 'hydrography', 'elevation'],
        description: 'Cascades, sources et rivières'
    }
};

// Export layer creation function
export function createLeafletLayer(layerConfig) {
    const options = {
        attribution: layerConfig.attribution,
        maxZoom: layerConfig.maxZoom || 18,
        tileSize: 256
    };
    
    if (layerConfig.minZoom) options.minZoom = layerConfig.minZoom;
    if (layerConfig.opacity) options.opacity = layerConfig.opacity;
    
    return L.tileLayer(layerConfig.url, options);
}