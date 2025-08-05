# 🇫🇷 IGN Geoservices Integration

## Official French Geographic Data Integration

The application now integrates with **IGN (Institut national de l'information géographique et forestière)** - France's official mapping and geographic data provider.

### 🗺️ Available IGN Services

1. **Official Base Maps**
   - **Plan IGN v2**: Multi-scale cartography of French territory
   - **Photographies aériennes**: High-resolution aerial photography
   - **Cartes topographiques**: Classic IGN topographic maps
   - **SCAN 25 Touristique**: Tourist maps at 1:25,000 scale
   - **Parcellaire Express**: Cadastral parcel boundaries

2. **Geographic Services**
   - **Geocoding**: Convert addresses to coordinates
   - **Reverse Geocoding**: Get addresses from coordinates
   - **Elevation API**: Get altitude for any point
   - **Administrative Boundaries**: Official department/commune limits

3. **Data Quality**
   - Official government data
   - Regularly updated
   - Highest accuracy available for France
   - Professional-grade cartography

### 📍 Access Points

**IGN Official Map Interface**: http://localhost:8085/ign-official-map.html

### 🔧 Implementation Details

The integration uses IGN's official APIs:
- **WMTS Services**: For map tiles
- **Geocoding API**: For address search
- **Altimetry Service**: For elevation data
- **Admin Express**: For administrative boundaries

### 🎯 Benefits

1. **Accuracy**: Official government data ensures highest precision
2. **Coverage**: Complete coverage of all French territory
3. **Updates**: Regular updates from official sources
4. **Legal**: Proper licensing for all uses
5. **Quality**: Professional cartography standards

### 📊 Available Layers

- **Plan IGN**: Best for general navigation
- **Satellite**: Recent aerial photography
- **Topographic**: Elevation and terrain features
- **Tourist**: Hiking trails, points of interest
- **Cadastral**: Property boundaries

### 🔗 API Endpoints

```javascript
// Base services
https://data.geopf.fr/wmts         // Map tiles
https://data.geopf.fr/geocodage    // Geocoding
https://data.geopf.fr/altimetrie   // Elevation
```

### 🚀 Features Enabled

1. **Click for Elevation**: Click anywhere to see altitude
2. **Address Search**: Find locations by address
3. **Department Boundaries**: Official administrative limits
4. **Multi-Layer Support**: Switch between different map types
5. **Reverse Geocoding**: Get address from coordinates

### 📱 Usage Examples

```javascript
// Create IGN layers
const ign = new IGNGeoservices();
const layers = ign.createLeafletLayers();

// Geocode an address
const results = await ign.geocode("Place du Capitole, Toulouse");

// Get elevation
const altitude = await ign.getElevation(43.6047, 1.4442);

// Load department boundaries
await ign.getDepartmentBoundaries('31');
```

### 🌟 Why IGN?

- **Official Source**: Government-backed data
- **French Expertise**: Optimized for French territory
- **Professional Grade**: Used by emergency services, military
- **Complete Coverage**: Every corner of France mapped
- **Historical Data**: Access to historical maps

This integration elevates the application to professional standards, using the same data sources as French government agencies and emergency services.
