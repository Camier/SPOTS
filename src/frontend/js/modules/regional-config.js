/**
 * Regional Map Configuration
 * Equal focus on all departments in Occitanie region
 */

export const REGIONAL_CONFIG = {
    // Regional center (geographic center of covered departments)
    center: [43.8, 1.8],
    defaultZoom: 8,
    
    // Departments with their centers and characteristics
    departments: {
        'ariege': {
            name: 'Ariège',
            code: '09',
            center: [42.9, 1.6],
            capital: 'Foix',
            highlights: ['Pyrénées', 'Grottes', 'Lacs de montagne', 'Châteaux cathares'],
            color: '#2563eb'
        },
        'aveyron': {
            name: 'Aveyron',
            code: '12', 
            center: [44.35, 2.57],
            capital: 'Rodez',
            highlights: ['Gorges du Tarn', 'Aubrac', 'Millau', 'Villages perchés'],
            color: '#059669'
        },
        'haute-garonne': {
            name: 'Haute-Garonne',
            code: '31',
            center: [43.3, 1.1],
            capital: 'Toulouse',
            highlights: ['Pyrénées', 'Canal du Midi', 'Garonne', 'Forêts'],
            color: '#dc2626'
        },
        'gers': {
            name: 'Gers',
            code: '32',
            center: [43.65, 0.58],
            capital: 'Auch',
            highlights: ['Bastides', 'Vignobles', 'Collines', 'Patrimoine gascon'],
            color: '#7c3aed'
        },
        'lot': {
            name: 'Lot',
            code: '46',
            center: [44.6, 1.6],
            capital: 'Cahors',
            highlights: ['Causses', 'Vallée du Lot', 'Grottes', 'Villages médiévaux'],
            color: '#ea580c'
        },
        'hautes-pyrenees': {
            name: 'Hautes-Pyrénées',
            code: '65',
            center: [43.0, 0.15],
            capital: 'Tarbes',
            highlights: ['Pic du Midi', 'Cirques', 'Thermes', 'Cols mythiques'],
            color: '#0891b2'
        },
        'tarn': {
            name: 'Tarn',
            code: '81',
            center: [43.9, 2.2],
            capital: 'Albi',
            highlights: ['Montagne Noire', 'Vignobles', 'Bastides', 'Gorges'],
            color: '#84cc16'
        },
        'tarn-et-garonne': {
            name: 'Tarn-et-Garonne',
            code: '82',
            center: [44.0, 1.35],
            capital: 'Montauban',
            highlights: ['Gorges de l\'Aveyron', 'Canal', 'Vergers', 'Coteaux'],
            color: '#f59e0b'
        }
    },
    
    // Activity zones (not centered on any particular city)
    zones: {
        'pyrenees': {
            name: 'Zone Pyrénées',
            bounds: [[42.5, 0.0], [43.2, 2.0]],
            activities: ['Randonnée', 'Ski', 'Escalade', 'Thermalisme']
        },
        'causses': {
            name: 'Causses et Gorges',
            bounds: [[43.9, 1.3], [44.8, 2.8]],
            activities: ['Spéléologie', 'Canyoning', 'VTT', 'Parapente']
        },
        'plaines': {
            name: 'Plaines et Coteaux',
            bounds: [[43.2, 0.5], [44.2, 2.0]],
            activities: ['Cyclisme', 'Œnotourisme', 'Patrimoine', 'Randonnée douce']
        },
        'montagne-noire': {
            name: 'Montagne Noire',
            bounds: [[43.3, 2.0], [43.7, 2.5]],
            activities: ['Forêt', 'VTT', 'Trail', 'Lacs']
        }
    },
    
    // Quick navigation presets
    presets: [
        { name: 'Vue Régionale', center: [43.8, 1.8], zoom: 8 },
        { name: 'Pyrénées', center: [42.8, 0.5], zoom: 9 },
        { name: 'Causses du Lot', center: [44.5, 1.7], zoom: 10 },
        { name: 'Montagne Noire', center: [43.5, 2.25], zoom: 10 },
        { name: 'Gorges du Tarn', center: [44.3, 3.2], zoom: 10 },
        { name: 'Aubrac', center: [44.6, 2.9], zoom: 10 }
    ],
    
    // Weather stations distributed across the region
    weatherStations: [
        { name: 'Albi', lat: 43.9, lon: 2.15 },
        { name: 'Rodez', lat: 44.35, lon: 2.57 },
        { name: 'Foix', lat: 42.96, lon: 1.61 },
        { name: 'Cahors', lat: 44.45, lon: 1.44 },
        { name: 'Auch', lat: 43.65, lon: 0.59 },
        { name: 'Millau', lat: 44.1, lon: 3.08 },
        { name: 'Tarbes', lat: 43.23, lon: 0.07 },
        { name: 'Saint-Gaudens', lat: 43.11, lon: 0.72 },
        { name: 'Castres', lat: 43.6, lon: 2.24 },
        { name: 'Montauban', lat: 44.02, lon: 1.35 }
    ]
};

// Department boundary check
export function getDepartmentFromCoords(lat, lon) {
    // Simplified boundary check - in production would use proper GeoJSON
    if (lat < 43.2 && lon < 2.0) return 'ariege';
    if (lat > 44.2 && lon > 2.2) return 'aveyron';
    if (lat > 44.3 && lon < 2.0) return 'lot';
    if (lat > 43.7 && lon > 1.8 && lon < 2.5) return 'tarn';
    if (lat < 43.5 && lon < 0.5) return 'hautes-pyrenees';
    if (lat > 43.5 && lon < 1.0) return 'gers';
    if (lat > 43.8 && lon > 1.0 && lon < 1.7) return 'tarn-et-garonne';
    return 'haute-garonne'; // Default fallback
}

// Get spots by department
export function filterSpotsByDepartment(spots, departmentCode) {
    return spots.filter(spot => {
        const dept = getDepartmentFromCoords(spot.latitude, spot.longitude);
        return REGIONAL_CONFIG.departments[dept]?.code === departmentCode;
    });
}

// Get regional statistics
export function getRegionalStats(spots) {
    const stats = {};
    
    Object.keys(REGIONAL_CONFIG.departments).forEach(deptKey => {
        stats[deptKey] = {
            name: REGIONAL_CONFIG.departments[deptKey].name,
            count: 0,
            percentage: 0
        };
    });
    
    spots.forEach(spot => {
        const dept = getDepartmentFromCoords(spot.latitude, spot.longitude);
        if (stats[dept]) {
            stats[dept].count++;
        }
    });
    
    // Calculate percentages
    const total = spots.length;
    Object.keys(stats).forEach(dept => {
        stats[dept].percentage = ((stats[dept].count / total) * 100).toFixed(1);
    });
    
    return stats;
}

export default REGIONAL_CONFIG;
