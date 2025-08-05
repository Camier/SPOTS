/**
 * Filter Controls Module - Lightweight version
 */

export function initializeControls(map, markers, spots) {
    const container = document.getElementById('controls');
    if (!container) return;
    
    // Create filter buttons
    const types = ['all', 'cascade', 'grotte', 'source', 'ruine'];
    const typeLabels = {
        'all': 'Tous',
        'cascade': 'Cascades 💧',
        'grotte': 'Grottes 🕳️',
        'source': 'Sources 💦',
        'ruine': 'Ruines 🏚️'
    };
    
    let activeFilter = 'all';
    
    // Create buttons
    types.forEach(type => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn' + (type === 'all' ? ' active' : '');
        btn.textContent = typeLabels[type];
        btn.dataset.type = type;
        
        btn.addEventListener('click', () => {
            // Update active state
            container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Apply filter
            activeFilter = type;
            filterMarkers(type);
        });
        
        container.appendChild(btn);
    });
    
    // Filter function
    function filterMarkers(type) {
        markers.clearLayers();
        
        const filteredSpots = type === 'all' 
            ? spots 
            : spots.filter(spot => spot.type === type);
        
        // Add filtered markers
        filteredSpots.forEach(spot => {
            const icon = L.divIcon({
                html: `<div style="font-size: 20px;">${getIcon(spot.type)}</div>`,
                iconSize: [20, 20],
                className: 'custom-div-icon'
            });
            
            const marker = L.marker([spot.latitude, spot.longitude], { icon });
            
            marker.bindPopup(`
                <b>${spot.name}</b><br>
                Type: ${spot.type}<br>
                ${spot.description ? spot.description.substring(0, 100) + '...' : ''}
            `, { maxWidth: 200 });
            
            markers.addLayer(marker);
        });
        
        // Update count
        const countEl = document.getElementById('spot-count');
        if (countEl) {
            countEl.textContent = `${filteredSpots.length} spots`;
        }
    }
    
    function getIcon(type) {
        const icons = {
            cascade: '💧',
            grotte: '🕳️',
            source: '💦',
            ruine: '🏚️',
            default: '📍'
        };
        return icons[type] || icons.default;
    }
}