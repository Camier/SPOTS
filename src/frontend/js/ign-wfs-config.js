/**
 * IGN WFS Configuration Module
 * Contains constants, endpoints, and layer definitions
 */

export const IGN_WFS_CONFIG = {
    // API endpoints
    endpoints: {
        capabilities: '/wfs/capabilities',
        spotAnalysis: '/spots/{spotId}/wfs-analysis',
        transport: '/wfs/transport',
        hydrography: '/wfs/hydrography',
        administrative: '/wfs/administrative'
    },

    // Cache configuration
    cache: {
        timeout: 5 * 60 * 1000, // 5 minutes
        maxItems: 100
    },

    // Request configuration
    request: {
        timeout: 15000, // 15 seconds
        retryAttempts: 2,
        retryDelay: 1000 // 1 second
    },

    // Layer styles
    layerStyles: {
        // Transport network styles
        transport: {
            road: {
                color: '#ff7800',
                weight: 3,
                opacity: 0.8,
                dashArray: null
            },
            path: {
                color: '#8b4513',
                weight: 2,
                opacity: 0.7,
                dashArray: '5, 5'
            },
            trail: {
                color: '#228b22',
                weight: 2,
                opacity: 0.6,
                dashArray: '2, 4'
            },
            default: {
                color: '#666',
                weight: 2,
                opacity: 0.6
            }
        },

        // Hydrography styles
        hydrography: {
            river: {
                color: '#0066cc',
                weight: 3,
                opacity: 0.8
            },
            stream: {
                color: '#4da6ff',
                weight: 2,
                opacity: 0.7
            },
            lake: {
                fillColor: '#4da6ff',
                fillOpacity: 0.3,
                color: '#0066cc',
                weight: 2
            },
            spring: {
                radius: 8,
                fillColor: '#00ccff',
                fillOpacity: 0.8,
                color: '#0066cc',
                weight: 2
            },
            default: {
                color: '#4da6ff',
                weight: 2,
                opacity: 0.7
            }
        },

        // Administrative boundaries
        administrative: {
            commune: {
                fillColor: '#ffeb3b',
                fillOpacity: 0.1,
                color: '#ff9800',
                weight: 2,
                dashArray: '5, 5'
            },
            departement: {
                fillColor: '#ff9800',
                fillOpacity: 0.1,
                color: '#e65100',
                weight: 3
            },
            region: {
                fillColor: '#e65100',
                fillOpacity: 0.1,
                color: '#bf360c',
                weight: 4
            }
        },

        // Analysis overlay
        analysisOverlay: {
            radius: {
                fillColor: '#2196f3',
                fillOpacity: 0.1,
                color: '#1976d2',
                weight: 2,
                dashArray: '10, 5'
            }
        }
    },

    // Feature type mappings
    featureTypes: {
        transport: {
            all: null,
            roads: 'BDTOPO_V3:troncon_de_route',
            paths: 'BDTOPO_V3:sentier_et_escalier',
            railways: 'BDTOPO_V3:troncon_de_voie_ferree'
        },
        hydrography: {
            all: null,
            watercourses: 'BDTOPO_V3:cours_d_eau',
            water_surfaces: 'BDTOPO_V3:surface_hydrographique',
            points: 'BDTOPO_V3:point_d_eau'
        },
        administrative: {
            commune: 'ADMINEXPRESS-COG-CARTO.LATEST:commune',
            departement: 'ADMINEXPRESS-COG-CARTO.LATEST:departement',
            region: 'ADMINEXPRESS-COG-CARTO.LATEST:region'
        }
    },

    // Popup templates
    popupTemplates: {
        transport: (properties) => `
            <div class="ign-popup">
                <h4>${properties.nature || 'Transport'}</h4>
                ${properties.nom ? `<p><strong>Nom:</strong> ${properties.nom}</p>` : ''}
                ${properties.importance ? `<p><strong>Importance:</strong> ${properties.importance}</p>` : ''}
                ${properties.largeur ? `<p><strong>Largeur:</strong> ${properties.largeur}m</p>` : ''}
            </div>
        `,
        hydrography: (properties) => `
            <div class="ign-popup">
                <h4>${properties.nature || 'Hydrographie'}</h4>
                ${properties.toponyme ? `<p><strong>Nom:</strong> ${properties.toponyme}</p>` : ''}
                ${properties.regime ? `<p><strong>Régime:</strong> ${properties.regime}</p>` : ''}
            </div>
        `,
        administrative: (properties) => `
            <div class="ign-popup">
                <h4>${properties.nom || 'Zone administrative'}</h4>
                ${properties.code_insee ? `<p><strong>Code INSEE:</strong> ${properties.code_insee}</p>` : ''}
                ${properties.population ? `<p><strong>Population:</strong> ${properties.population}</p>` : ''}
            </div>
        `
    }
};

export default IGN_WFS_CONFIG;