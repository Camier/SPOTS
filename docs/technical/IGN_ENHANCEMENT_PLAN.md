# 🗺️ IGN Geoportal Access Library Integration Plan

## Overview
Upgrade SPOTS project with official IGN Geoportal Access Library to add advanced geospatial features.

## Current Implementation Analysis
✅ **Already implemented** via `ign-geoservices.js`:
- WMTS tile layers (Plan, Satellite, Topographic, Tourism)
- Basic geocoding/reverse geocoding  
- Point elevation queries
- Department boundaries
- Leaflet integration

## Enhancement Opportunities

### 🚀 New Features with Official Library

#### 1. **Smart Address Auto-completion**
```javascript
Gp.Services.autoComplete({
    text: "château de", 
    filterOptions: { type: ["PositionOfInterest"] },
    onSuccess: function(result) {
        // Show suggestions: Château de Versailles, Château de Fontainebleau...
    }
});
```

#### 2. **Route Planning to Spots**
```javascript
Gp.Services.route({
    startPoint: { x: userLon, y: userLat },
    endPoint: { x: spotLon, y: spotLat },
    graph: "Voiture", // or "Pieton"
    onSuccess: function(result) {
        // Display route on map with turn-by-turn directions
    }
});
```

#### 3. **Accessibility Zones (Isochrones)**
```javascript
Gp.Services.isoCurve({
    position: { x: userLon, y: userLat },
    method: "time",
    time: 1800, // 30 minutes
    graph: "Voiture",
    onSuccess: function(result) {
        // Show all spots reachable within 30 minutes
    }
});
```

#### 4. **Elevation Profiles for Hiking**
```javascript
Gp.Services.getAltitude({
    positions: routePoints,
    sampling: 50,
    onSuccess: function(result) {
        // Display elevation chart for hiking routes
    }
});
```

## Implementation Strategy

### Phase 1: Library Integration (30 min)
1. Add official library to project
2. Initialize alongside existing implementation
3. Test compatibility with current features

### Phase 2: Feature Enhancement (2 hours)  
1. **Search Enhancement**: Replace basic geocoding with auto-complete
2. **Route Integration**: Add "Get Directions" to spot popups
3. **Accessibility Filter**: "Show spots within X minutes" feature
4. **Elevation Profiles**: Add hiking difficulty indicators

### Phase 3: UI/UX Improvements (1 hour)
1. Enhanced search bar with suggestions
2. Route visualization on map
3. Accessibility zone overlay
4. Elevation charts in spot details

## Technical Integration

### 1. Install Official Library
```bash
npm install geoportal-access-lib
```

### 2. Add to Frontend
```html
<script src="https://ignf.github.io/geoportal-access-lib/latest/dist/GpServices.js"></script>
```

### 3. Initialize in Code
```javascript
// Keep existing custom implementation for maps
import IGNGeoservices from './js/modules/ign-geoservices.js';

// Add official library for advanced features
const ignAdvanced = window.Gp.Services;
```

## New User Features

### 🔍 **Enhanced Search Experience**
- Type "château" → get suggestions for all castles in Occitanie
- Auto-complete addresses as you type
- Smart filtering by spot types

### 🛣️ **Route Planning**
- "Get Directions" button on every spot
- Multi-modal routes (car, bike, walking)
- Estimated travel time and distance

### ⏱️ **Accessibility Filtering**
- "Show spots within 30 minutes"
- Different transport modes
- Visual accessibility zones on map

### 📈 **Hiking Intelligence** 
- Elevation profiles for walking routes
- Difficulty estimation
- Cumulative elevation gain/loss

## Benefits for Occitanie Tourism

### 🏔️ **Pyrénées Region**
- Hiking route difficulty assessment
- Elevation profiles for mountain spots
- Weather-elevation correlation

### 🏰 **Historical Sites**
- Auto-complete for châteaux and monuments
- Multi-site tourist routes
- Accessibility from major cities

### 🚗 **Route Tourism**
- "Route des Bastides" planning
- Wine route optimization
- Multi-day itinerary suggestions

## Expected User Impact
- **30% faster** spot discovery with auto-complete
- **Route planning** reduces barriers to visiting remote spots
- **Accessibility filters** help users find spots matching their time constraints
- **Elevation data** improves hiking safety and preparation

## Implementation Timeline
- **Week 1**: Library integration and testing
- **Week 2**: Core feature implementation  
- **Week 3**: UI/UX refinement and testing
- **Week 4**: Documentation and deployment

## Next Steps
1. ✅ Review this plan
2. 🔄 Install and test official library
3. 🚀 Implement enhanced search first
4. 📊 Add route planning features
5. 🎯 Deploy and gather user feedback
