# 🎨 IGN Artistic Styles Integration Guide

## Overview
The [geoservice-style](https://github.com/Viglino/geoservice-style) repository provides 20+ beautiful custom styles for IGN vector tiles, transforming standard maps into artistic visualizations.

## Available Styles

### 🎨 Monochrome Collection
- **Mono Red** (#912626) - Dramatic red-tinted maps
- **Mono Green** (#6d8e30) - Nature-focused green theme
- **Mono Blue** (#265791) - Classic blue cartography
- **Mono Purple** (#583c77) - Elegant purple styling
- **Mono Orange** (#c26518) - Warm orange tones
- **Mono Yellow** (#ffff00) - Bright yellow highlights
- **Mono Black** (#111111) - High contrast black
- **Mono Gray** (#333333) - Subtle grayscale

### 🖼️ Artistic Styles
- **Cyanotype** - Ancient photographic blue print style
- **Cassini** - 18th century French map aesthetics
- **Retro** - Vintage road atlas appearance
- **Guidebook** - Early 20th century tourist guide style
- **Coffee** - Warm coffee-colored palette
- **Mondrian** - Geometric art inspired by Piet Mondrian

### 🏗️ Thematic Maps
- **Roads** - Pedestrian-friendly street focus
- **ERP** - Public establishment highlighting
- **MapArt** - Artistic building visualization

### 🎃 Seasonal Themes
- **Halloween** - Spooky map with ghosts and cauldrons
- **Christmas** - Festive holiday themed map

## Integration Methods

### Method 1: Mapbox GL JS (Vector Tiles)
```javascript
// Full vector tile support with custom styles
const map = new mapboxgl.Map({
    container: 'map',
    style: 'https://viglino.github.io/geoservice-style/cyanotype/cyanotype.json',
    center: [1.8, 43.8],
    zoom: 8
});
```

### Method 2: Raster Tile Proxy (Leaflet Compatible)
```javascript
// Convert vector styles to raster tiles for Leaflet
const styleUrl = 'https://viglino.github.io/geoservice-style/cassini/cassini.json';
const rasterUrl = `https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?style=${encodeURIComponent(styleUrl)}`;

L.tileLayer(rasterUrl, {
    attribution: '© IGN, Style by Viglino',
    maxZoom: 18
}).addTo(map);
```

### Method 3: IGN Raster Services with CSS Filters
```javascript
// Apply CSS filters to approximate artistic styles
const ignLayer = L.tileLayer('https://data.geopf.fr/wmts?...', {
    className: 'artistic-filter-cyanotype'
});

// CSS
.artistic-filter-cyanotype {
    filter: sepia(100%) hue-rotate(180deg) saturate(2) contrast(1.5);
}
```

## Implementation for SPOTS

### 1. Created Files
- `regional-map-artistic.html` - Full Mapbox GL implementation
- This guide - Integration documentation

### 2. Style Selector UI
```html
<select id="map-style">
    <optgroup label="Monochrome">
        <option value="mono_blue">🔵 Bleu</option>
        <!-- More options... -->
    </optgroup>
    <optgroup label="Artistique">
        <option value="cyanotype">📷 Cyanotype</option>
        <!-- More options... -->
    </optgroup>
</select>
```

### 3. Dynamic Style Switching
```javascript
function changeMapStyle(styleName) {
    const styleUrl = `https://viglino.github.io/geoservice-style/${styleName}/${styleName}.json`;
    map.setStyle(styleUrl);
}
```

## Benefits for SPOTS Project

1. **Visual Variety** - 20+ unique map styles to choose from
2. **Thematic Matching** - Match map style to activity (e.g., blue for waterfalls)
3. **Seasonal Updates** - Halloween/Christmas themes for holidays
4. **Accessibility** - High contrast options (mono black/white)
5. **Artistic Appeal** - Beautiful maps for screenshots/sharing

## Performance Considerations

- Vector tiles are more efficient than raster
- Style switching requires full map reload
- Consider caching frequently used styles
- Markers need re-adding after style change

## Next Steps

1. Test `regional-map-artistic.html` with local server
2. Choose default artistic style for production
3. Add style persistence to localStorage
4. Create style preview thumbnails
5. Consider style-based marker customization

## Resources

- [Live Demo](https://viglino.github.io/geoservice-style/)
- [GitHub Repository](https://github.com/Viglino/geoservice-style)
- [IGN Vector Tiles Documentation](https://geoservices.ign.fr/documentation/services/api-et-services-ogc/tuiles-vectorielles-tmswmts)

---

*Note: These styles work with IGN's Géoservice vector tiles. For production use, ensure proper API key configuration if required.*