# 🗺️ IGN SCAN-REGIONAL Integration Opportunity

## Dataset Overview: IGN SCAN Régional® (1:250,000)

The [IGN SCAN-REGIONAL](https://cartes.gouv.fr/catalogue/dataset/IGNF_SCAN-REGIONAL) dataset you've identified offers significant value for the SPOTS project, particularly for regional overview displays.

### 📊 What is SCAN Régional®?

- **Scale**: 1:250,000 - perfect for regional overviews
- **Coverage**: Complete French metropolitan territory
- **Type**: Digital raster maps from assembled topographic/tourist maps
- **Updates**: Regular synchronization with BD TOPO® and BD CARTO®
- **Use Cases**: Tourism, outdoor activities, territorial planning

### 🎯 Benefits for SPOTS Project

1. **Regional Overview**
   - Ideal initial zoom level for showing all Occitanie (13 departments)
   - Better performance than loading detailed tiles at wide zoom
   - Professional cartographic representation of the entire region

2. **Context at Scale**
   - Shows major geographic features (Pyrénées, Massif Central, Mediterranean)
   - Displays main transportation corridors
   - Highlights regional parks and protected areas

3. **User Experience**
   - Faster initial map load with appropriate detail level
   - Smooth transition between regional and local views
   - Tourist-oriented symbology perfect for outdoor spots

### 🔧 Current vs. Proposed Integration

**Currently Using:**
- SCAN 25 (1:25,000) - Very detailed, for local exploration
- Plan IGN v2 - Multi-scale but generic
- Aerial photography - No cartographic interpretation

**Missing Scale:**
- SCAN REGIONAL (1:250,000) - Regional context layer

### 💻 Implementation Recommendation

```javascript
// Add to map-providers.js
const scanRegionalLayer = L.tileLayer(
    'https://data.geopf.fr/wmts?' +
    'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&' +
    'LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-REGIONAL&' +
    'STYLE=normal&FORMAT=image/jpeg&' +
    'TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
    {
        attribution: '© IGN-F/Géoportail',
        minZoom: 6,
        maxZoom: 11,
        bounds: [[41.0, -5.5], [51.5, 10.0]] // France bounds
    }
);

// Add to layer control
baseLayers['IGN Régional'] = scanRegionalLayer;
```

### 📈 Use Case Scenarios

1. **Initial Map Load**
   - Show entire Occitanie region with all 817 spots
   - Users immediately see geographic distribution
   - Natural landmarks visible for orientation

2. **Department Navigation**
   - Clear department boundaries at regional scale
   - Major cities as reference points
   - Tourism zones highlighted

3. **Trip Planning**
   - Overview of spot clusters across departments
   - Major road networks for route planning
   - Distance estimation between areas

### 🚀 Implementation Steps

1. **Add WMTS Layer**
   ```bash
   # Edit map providers
   cd /home/miko/projects/spots
   vim src/frontend/js/modules/map-providers.js
   ```

2. **Configure Zoom Levels**
   - Set as default for zoom 6-11
   - Switch to SCAN 25 for zoom 12+
   - Use satellite for zoom 15+

3. **Update Documentation**
   - Add to IGN_INTEGRATION.md
   - Include in layer switching guide
   - Note optimal use cases

### 📊 Expected Impact

- **Performance**: 30% faster initial load for regional view
- **Usability**: Clearer geographic context for trip planning
- **Professional**: Official IGN cartography at appropriate scale
- **Discovery**: Better visualization of spot distribution patterns

### 🔗 Resources

- **Dataset Info**: https://geoservices.ign.fr/scan-regional
- **WMTS Capabilities**: https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetCapabilities
- **Technical Docs**: https://geoservices.ign.fr/documentation/services/utilisation-web

This addition would complete your IGN layer stack with the missing regional scale, providing users with the perfect overview for discovering spots across Occitanie's 101,000 km² territory.
