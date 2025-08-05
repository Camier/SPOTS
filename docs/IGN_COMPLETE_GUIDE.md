# 🇫🇷 IGN Services Integration Guide

## Complete Guide to French Geographic Data Services for SPOTS

### Table of Contents
1. [IGN Overview](#ign-overview)
2. [Géoplateforme Services](#géoplateforme-services)
3. [Data Products Catalog](#data-products-catalog)
4. [Implementation Examples](#implementation-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## 🏛️ IGN Overview

The **Institut national de l'information géographique et forestière (IGN)** is France's national mapping agency, providing authoritative geographic data for the entire French territory.

### Key Advantages for SPOTS
- **Official Data**: Government-certified accuracy
- **Complete Coverage**: All of France including overseas territories
- **Regular Updates**: Synchronized with ground surveys
- **Free Access**: Most services available without fees
- **French-Optimized**: Designed for French geography and use cases

### Service Evolution
- **Legacy**: Géoportail (being phased out)
- **Current**: Géoplateforme (unified platform)
- **Future**: Enhanced APIs and real-time data

---

## 🌐 Géoplateforme Services

### Authentication

Most services require an API key:

```bash
# Register at: https://geoservices.ign.fr/
# Get your key from: Mon compte > Mes clés

export IGN_API_KEY="your-key-here"
```

### Core Services Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Géoplateforme                      │
├─────────────────┬─────────────────┬─────────────────┤
│   Map Services  │  Data Services  │   Processing    │
├─────────────────┼─────────────────┼─────────────────┤
│ • WMTS         │ • Geocoding     │ • Isochrone     │
│ • WMS          │ • Altimetry     │ • Route         │
│ • WFS          │ • Download      │ • Analysis      │
└─────────────────┴─────────────────┴─────────────────┘
```

### 1. WMTS (Web Map Tile Service)

#### Configuration
```javascript
const wmtsUrl = 'https://data.geopf.fr/wmts';
const wmtsParams = {
  SERVICE: 'WMTS',
  REQUEST: 'GetTile',
  VERSION: '1.0.0',
  LAYER: 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
  STYLE: 'normal',
  FORMAT: 'image/png',
  TILEMATRIXSET: 'PM',
  TILEMATRIX: '{z}',
  TILEROW: '{y}',
  TILECOL: '{x}'
};
```

#### Available Layers
| Layer ID | Description | Best Zoom | Use Case |
|----------|-------------|-----------|----------|
| PLANIGNV2 | Vector plan | 0-18 | General navigation |
| MAPS.SCAN25TOUR | 1:25,000 tourist | 11-16 | Hiking detail |
| MAPS.SCAN-REGIONAL | 1:250,000 regional | 6-11 | Regional overview |
| ORTHOPHOTOS | Aerial imagery | 0-20 | Terrain analysis |
| CADASTRALPARCELS | Property boundaries | 14-20 | Land ownership |

### 2. Geocoding Service

#### Forward Geocoding (Address → Coordinates)
```python
import requests

def geocode_address(address):
    url = "https://data.geopf.fr/geocodage/search"
    params = {
        'q': address,
        'limit': 10,
        'returntruegeometry': 'true',
        'type': 'housenumber,street,municipality'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['features']:
        feature = data['features'][0]
        return {
            'coordinates': feature['geometry']['coordinates'],
            'label': feature['properties']['label'],
            'score': feature['properties']['score'],
            'type': feature['properties']['type']
        }
```

#### Reverse Geocoding (Coordinates → Address)
```python
def reverse_geocode(lat, lon):
    url = "https://data.geopf.fr/geocodage/reverse"
    params = {
        'lon': lon,
        'lat': lat,
        'distance': 200  # Search radius in meters
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

### 3. Altimetry Service

#### Point Elevation
```python
def get_elevation(lat, lon):
    url = "https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json"
    params = {
        'lon': lon,
        'lat': lat,
        'zonly': 'true'  # Return only Z value
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    return data['elevations'][0]['z']
```

#### Elevation Profile
```python
def get_elevation_profile(coordinates):
    """Get elevation profile along a path"""
    url = "https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevationpath.json"
    
    # Format: lon1,lat1|lon2,lat2|...
    path = '|'.join([f"{lon},{lat}" for lon, lat in coordinates])
    
    params = {
        'resource': 'ign_rge_alti_wld',
        'path': path,
        'sampling': 20  # Points every 20m
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

### 4. Isochrone Service

Calculate areas reachable within time/distance:

```python
def calculate_isochrone(lat, lon, method='time', value=900):
    """
    Calculate isochrone from a point
    method: 'time' (seconds) or 'distance' (meters)
    """
    url = "https://data.geopf.fr/navigation/isochrone"
    
    data = {
        'point': [lon, lat],
        'resource': 'bdtopo-osrm',
        'costType': method,
        'costValue': value,
        'profile': 'pedestrian',  # or 'car'
        'direction': 'departure',
        'holes': False
    }
    
    response = requests.post(url, json=data)
    return response.json()
```

---

## 📚 Data Products Catalog

### Topographic Data (BD TOPO®)

The reference topographic database of France:

```python
# WFS Query for BD TOPO features
def get_bdtopo_features(bbox, layer):
    """
    Get BD TOPO features within bounding box
    bbox: [min_lon, min_lat, max_lon, max_lat]
    layer: e.g., 'BDTOPO_V3:batiment', 'BDTOPO_V3:troncon_de_route'
    """
    url = "https://data.geopf.fr/wfs/ows"
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeName': layer,
        'outputFormat': 'application/json',
        'bbox': ','.join(map(str, bbox)) + ',EPSG:4326'
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

#### Key BD TOPO Layers
- **Buildings**: `BDTOPO_V3:batiment`
- **Roads**: `BDTOPO_V3:troncon_de_route`
- **Hydrography**: `BDTOPO_V3:surface_hydrographique`
- **Vegetation**: `BDTOPO_V3:zone_de_vegetation`
- **Terrain**: `BDTOPO_V3:terrain_de_sport`

### Forest Data (BD FORÊT®)

```python
# Get forest information for a location
def get_forest_data(lat, lon):
    """Get forest type and characteristics"""
    # Use WMS GetFeatureInfo
    url = "https://data.geopf.fr/wms-v/ows"
    params = {
        'SERVICE': 'WMS',
        'VERSION': '1.3.0',
        'REQUEST': 'GetFeatureInfo',
        'LAYERS': 'BDFORET-V2_ESSENCES',
        'QUERY_LAYERS': 'BDFORET-V2_ESSENCES',
        'CRS': 'EPSG:4326',
        'BBOX': f"{lon-0.001},{lat-0.001},{lon+0.001},{lat+0.001}",
        'WIDTH': 101,
        'HEIGHT': 101,
        'I': 50,
        'J': 50,
        'INFO_FORMAT': 'application/json'
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

### Administrative Boundaries (ADMIN EXPRESS)

```python
# Get commune (municipality) for coordinates
def get_commune(lat, lon):
    url = "https://data.geopf.fr/wfs/ows"
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeName': 'ADMINEXPRESS-COG:commune',
        'outputFormat': 'application/json',
        'cql_filter': f'INTERSECTS(the_geom, POINT({lon} {lat}))'
    }
    
    response = requests.get(url, params=params)
    features = response.json()['features']
    
    if features:
        props = features[0]['properties']
        return {
            'code_insee': props['insee_com'],
            'name': props['nom'],
            'department': props['insee_dep'],
            'region': props['insee_reg']
        }
```

---

## 💻 Implementation Examples

### Complete Spot Enrichment

```python
class IGNEnrichmentService:
    """Enrich spots with comprehensive IGN data"""
    
    def __init__(self):
        self.base_url = "https://data.geopf.fr"
    
    async def enrich_spot(self, spot):
        """Add IGN data to a spot"""
        lat, lon = spot['latitude'], spot['longitude']
        
        # Get elevation
        spot['elevation_ign'] = await self.get_elevation(lat, lon)
        
        # Get administrative info
        spot['commune'] = await self.get_commune(lat, lon)
        
        # Get nearby features
        spot['nearby_features'] = await self.get_nearby_features(lat, lon)
        
        # Get forest info if applicable
        if await self.is_in_forest(lat, lon):
            spot['forest_info'] = await self.get_forest_data(lat, lon)
        
        # Calculate accessibility
        spot['accessibility'] = await self.calculate_accessibility(lat, lon)
        
        return spot
    
    async def get_nearby_features(self, lat, lon, radius=1000):
        """Find BD TOPO features within radius"""
        features = {
            'water': [],
            'trails': [],
            'buildings': [],
            'roads': []
        }
        
        # Query each feature type
        bbox = self.calculate_bbox(lat, lon, radius)
        
        # Water features
        water = await self.query_wfs(bbox, 'BDTOPO_V3:surface_hydrographique')
        features['water'] = self.process_features(water, lat, lon)
        
        # Trails and paths
        trails = await self.query_wfs(bbox, 'BDTOPO_V3:sentier')
        features['trails'] = self.process_features(trails, lat, lon)
        
        return features
```

### Leaflet Integration

```javascript
// Add IGN layers to Leaflet map
class IGNMapLayers {
    constructor(map) {
        this.map = map;
        this.apiKey = 'YOUR_IGN_API_KEY';
        this.layers = {};
        this.initializeLayers();
    }
    
    initializeLayers() {
        // Plan IGN V2
        this.layers['IGN Plan'] = L.tileLayer(
            'https://data.geopf.fr/wmts?' +
            'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&' +
            'LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&' +
            'STYLE=normal&FORMAT=image/png&' +
            'TILEMATRIXSET=PM&TILEMATRIX={z}&' +
            'TILEROW={y}&TILECOL={x}',
            {
                attribution: '© IGN-F/Géoportail',
                maxZoom: 18,
                minZoom: 0
            }
        );
        
        // SCAN 25 Tourist
        this.layers['IGN SCAN 25'] = L.tileLayer(
            'https://data.geopf.fr/wmts?' +
            'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&' +
            'LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR&' +
            'STYLE=normal&FORMAT=image/jpeg&' +
            'TILEMATRIXSET=PM&TILEMATRIX={z}&' +
            'TILEROW={y}&TILECOL={x}',
            {
                attribution: '© IGN-F/Géoportail',
                maxZoom: 16,
                minZoom: 11
            }
        );
        
        // Orthophoto
        this.layers['IGN Satellite'] = L.tileLayer(
            'https://data.geopf.fr/wmts?' +
            'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&' +
            'LAYER=ORTHOIMAGERY.ORTHOPHOTOS&' +
            'STYLE=normal&FORMAT=image/jpeg&' +
            'TILEMATRIXSET=PM&TILEMATRIX={z}&' +
            'TILEROW={y}&TILECOL={x}',
            {
                attribution: '© IGN-F/Géoportail',
                maxZoom: 20,
                minZoom: 0
            }
        );
    }
    
    // Add elevation profile display
    async showElevationProfile(coordinates) {
        const profile = await this.getElevationProfile(coordinates);
        
        // Create elevation chart
        const elevationData = profile.elevations.map(p => ({
            distance: p.distance,
            elevation: p.z
        }));
        
        // Display using Chart.js or similar
        this.displayChart(elevationData);
    }
}
```

---

## 📋 Best Practices

### 1. Caching Strategy
```python
# Cache IGN responses to reduce API calls
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_elevation(lat, lon):
    # Round to 3 decimals for cache efficiency
    lat = round(lat, 3)
    lon = round(lon, 3)
    return get_elevation(lat, lon)
```

### 2. Rate Limiting
```python
# Respect IGN rate limits
from asyncio import Semaphore
import asyncio

class IGNRateLimiter:
    def __init__(self, max_concurrent=5, requests_per_second=10):
        self.semaphore = Semaphore(max_concurrent)
        self.rate_limit = requests_per_second
        self.request_times = []
    
    async def acquire(self):
        async with self.semaphore:
            # Ensure rate limit
            now = asyncio.get_event_loop().time()
            self.request_times = [t for t in self.request_times if now - t < 1]
            
            if len(self.request_times) >= self.rate_limit:
                sleep_time = 1 - (now - self.request_times[0])
                await asyncio.sleep(sleep_time)
            
            self.request_times.append(now)
```

### 3. Error Handling
```python
# Robust error handling for IGN services
class IGNServiceError(Exception):
    pass

async def safe_ign_request(url, params, retries=3):
    for attempt in range(retries):
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.get(url, params=params, timeout=10)
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited
                await asyncio.sleep(2 ** attempt)
            else:
                raise IGNServiceError(f"IGN API error: {response.status_code}")
                
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise IGNServiceError(f"IGN request failed: {str(e)}")
            await asyncio.sleep(1)
```

---

## 🔧 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Use server-side proxy for API calls
   - Configure proper CORS headers

2. **Authentication Failed**
   ```javascript
   // Check API key format
   headers: {
     'Authorization': 'Bearer ' + IGN_API_KEY
   }
   ```

3. **Tile Loading Issues**
   - Verify layer names (case-sensitive)
   - Check zoom level constraints
   - Ensure proper attribution

4. **Coordinate Systems**
   ```python
   # Convert between coordinate systems
   from pyproj import Transformer
   
   # WGS84 to Lambert 93
   transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154")
   x, y = transformer.transform(lat, lon)
   ```

### Performance Optimization

1. **Use Vector Tiles When Available**
   ```javascript
   // Prefer vector tiles for better performance
   'https://data.geopf.fr/tms/1.0.0/PLAN.IGN/{z}/{x}/{y}.pbf'
   ```

2. **Implement Progressive Loading**
   ```javascript
   // Load detailed data only at higher zoom levels
   map.on('zoomend', function() {
     if (map.getZoom() > 14) {
         loadDetailedIGNData();
     }
   });
   ```

3. **Bundle Requests**
   ```python
   # Bundle multiple elevation requests
   def get_elevations_batch(coordinates):
       # Single request for multiple points
       path = '|'.join([f"{lon},{lat}" for lat, lon in coordinates])
       return get_elevation_profile_batch(path)
   ```

---

## 📚 Additional Resources

### Official Documentation
- **IGN Géoservices**: https://geoservices.ign.fr/
- **API Reference**: https://geoservices.ign.fr/documentation/services
- **Data Specifications**: https://geoservices.ign.fr/documentation/donnees

### Developer Tools
- **API Console**: https://geoservices.ign.fr/console
- **QGIS Plugin**: https://plugins.qgis.org/plugins/ign-plugin/
- **OpenLayers Examples**: https://geoservices.ign.fr/documentation/exemples

### Support
- **Technical Support**: support.geoservices@ign.fr
- **Forum**: https://geoservices.ign.fr/forum
- **Status Page**: https://status.geoservices.ign.fr/

---

This guide provides comprehensive coverage of IGN services integration for the SPOTS project, enabling full utilization of France's official geographic data infrastructure.
