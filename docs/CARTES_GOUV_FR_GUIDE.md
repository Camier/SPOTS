# 🗺️ Cartes.gouv.fr API Guide

## Overview
Cartes.gouv.fr is France's official public mapping service, part of the Géoplateforme infrastructure launched on November 16, 2023. It provides free access to public maps and territorial data.

## 🔑 Key Information

### Access & Authentication
- **Open Data Services**: No API key required for basic services
- **Rate Limit**: 50 requests per second (returns HTTP 429 if exceeded)
- **Private Data**: Requires special access keys for non-free data

### Available Services
1. **Geocoding Service**
   - Free access without authentication
   - URL: Direct access via Géoplateforme endpoints
   - Limit: 50 req/sec

2. **Map Visualization**
   - Interactive maps for various themes:
     - Topography
     - Ecology
     - Security
     - Land registry (cadastre)
     - Regulations

3. **Data Services**
   - Create, host, and share maps
   - Publish data autonomously
   - Access to public datasets

## 📋 Terms of Use (CGU)

### Important Notes
- **CGU URL**: https://cartes.gouv.fr/cgu
- **Note**: The CGU page requires JavaScript to display properly
- Terms are integrated with broader Géoplateforme service framework

### Key Usage Conditions
1. **Open Data Policy**
   - Most services follow open data principles
   - No special rights required for public data
   - Fair usage enforced via rate limiting

2. **Attribution Requirements**
   - Must attribute IGN/Géoplateforme when using data
   - Follow standard French government data attribution

3. **Commercial Use**
   - Public data can be used for commercial purposes
   - Non-free data requires specific licensing

4. **Technical Requirements**
   - JavaScript required for web interface
   - Standard REST API access available
   - Support for OGC standards

## 🛠️ Integration with Spots Project

### Relevant Services for Occitanie Spots
1. **Geocoding**: Convert place names to coordinates
2. **Base Maps**: IGN topographic maps for visualization
3. **Elevation Data**: Terrain information for outdoor spots
4. **Administrative Boundaries**: Department/region validation

### Implementation Example
```javascript
// Geocoding with Géoplateforme
const geocodeUrl = 'https://wxs.ign.fr/essentiels/geoportail/geocodage/rest/0.1/search';
const params = {
    q: 'Lac de Salagou',
    limit: 5,
    returntruegeometry: true,
    postcode: '34700'  // Hérault
};

// No API key needed for public geocoding
fetch(`${geocodeUrl}?${new URLSearchParams(params)}`)
    .then(response => response.json())
    .then(data => console.log(data));
```

### Rate Limiting Best Practice
```javascript
// Implement rate limiting to stay under 50 req/sec
const rateLimiter = {
    queue: [],
    processing: false,
    maxPerSecond: 40,  // Conservative limit
    
    async addRequest(requestFn) {
        this.queue.push(requestFn);
        if (!this.processing) this.processQueue();
    },
    
    async processQueue() {
        this.processing = true;
        while (this.queue.length > 0) {
            const batch = this.queue.splice(0, this.maxPerSecond);
            await Promise.all(batch.map(fn => fn()));
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        this.processing = false;
    }
};
```

## 📚 Additional Resources

### Documentation
- **GitHub**: https://github.com/IGNF/cartes.gouv.fr-documentation
- **Géoservices**: https://geoservices.ign.fr/
- **API Tutorials**: https://geoplateforme.github.io/tutoriels/

### Related Services
- **geo.api.gouv.fr**: Alternative geocoding service
- **data.gouv.fr**: Open data portal
- **IGN Géoportail**: Legacy mapping service

## 🎯 Best Practices for Spots Project

1. **Use Open Services First**
   - Geocoding, base maps are free
   - No authentication overhead

2. **Respect Rate Limits**
   - Stay under 50 req/sec
   - Implement client-side caching

3. **Proper Attribution**
   - Include "© IGN - Géoplateforme" on maps
   - Link to cartes.gouv.fr when appropriate

4. **Fallback Strategy**
   - Primary: cartes.gouv.fr services
   - Secondary: OpenStreetMap/Nominatim
   - Tertiary: Other providers

## ⚠️ Limitations
- JavaScript required for web interface
- 50 requests/second rate limit
- Some premium data requires authentication
- Service still in beta/evolution phase

---

*Last updated: August 2025*
*Based on official Géoplateforme documentation*