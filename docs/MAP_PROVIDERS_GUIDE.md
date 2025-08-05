# Premium Map Providers Setup Guide

## Best Map Providers for Toulouse Spots

### 🇫🇷 Recommended for France (No API Key Required)

1. **IGN (Institut Géographique National) - BEST FOR FRANCE**
   - Official French government maps
   - Extremely detailed and accurate
   - Free to use
   - Includes hiking trails, topographic details

2. **ESRI World Imagery**
   - High-resolution satellite imagery
   - Updated regularly
   - Free for non-commercial use
   - Great clarity for spotting hidden locations

3. **Sentinel-2 Cloudless**
   - Cloud-free satellite composite
   - True color imagery
   - European Space Agency data
   - Perfect for outdoor spot discovery

### 🔑 Premium Providers (Free Tier Available)

1. **MapTiler** (Best for Europe)
   - Sign up at: https://cloud.maptiler.com/
   - Free tier: 100,000 tiles/month
   - Excellent outdoor and topo maps
   - Great satellite imagery

2. **Mapbox** (Best Overall)
   - Sign up at: https://account.mapbox.com/
   - Free tier: 50,000 map loads/month
   - Customizable styles
   - Industry-leading quality

3. **Thunderforest** (Best for Outdoor Activities)
   - Sign up at: https://www.thunderforest.com/
   - Free tier: 150,000 tiles/month
   - Specialized outdoor/landscape maps
   - Cycling and hiking focused

## Quick Setup

1. **For immediate use (no signup):**
   ```javascript
   // These work immediately:
   - IGN Satellite (French official)
   - IGN Plan v2 (French official)
   - ESRI World Imagery
   - Sentinel-2 Cloudless
   - CARTO (all styles)
   - OpenTopoMap
   ```

2. **To add API keys:**
   - Edit `/src/frontend/js/modules/map-providers.js`
   - Replace `YOUR_XXXXX_KEY` with actual keys
   - Refresh the map page

## Map Type Recommendations by Activity

- **Spot Discovery**: IGN Satellite, ESRI World Imagery
- **Hiking/Trails**: IGN Plan v2, OpenTopoMap, Thunderforest Outdoors
- **Cycling**: CyclOSM, Thunderforest Cycle
- **Urban Exploration**: CARTO Voyager, Stadia Bright
- **Night Mode**: CARTO Dark Matter, Stadia Dark

## Performance Tips

- Use `.png` format for better quality but larger size
- Use `.jpg` format for faster loading
- Enable tile caching in your browser
- Consider using a CDN for production
