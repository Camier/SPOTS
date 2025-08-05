# 📋 SPOTS Quick Reference Guide

## 🚀 Quick Start

### Start the Application
```bash
# Terminal 1: Backend API
cd /home/miko/projects/spots
source venv/bin/activate
uvicorn src.backend.main:app --reload --port 8000

# Terminal 2: Frontend
cd /home/miko/projects/spots
python -m http.server 8085 --directory src/frontend
```

### Access Points
- **Main App**: http://localhost:8085/regional-map.html
- **API Docs**: http://localhost:8000/docs
- **Database**: `data/occitanie_spots.db`

---

## 📊 Project Stats

- **Total Spots**: 817 verified locations
- **Departments**: 10 active (out of 13 in Occitanie)
- **Data Sources**: OpenStreetMap (95.8%), Social Media (4.2%)
- **Spot Types**: Caves (52.5%), Waterfalls (23.3%), Springs (13.1%), Ruins (7%)

### Department Distribution
| Code | Department | Spots | Percentage |
|------|------------|-------|------------|
| 09 | Ariège | 518 | 63.4% |
| 31 | Haute-Garonne | 83 | 10.2% |
| 81 | Tarn | 56 | 6.9% |
| 46 | Lot | 47 | 5.8% |
| 12 | Aveyron | 40 | 4.9% |

---

## 🔌 API Endpoints

### Core Endpoints
```bash
# Get all spots
GET /api/spots

# Get spots by department
GET /api/spots/department/31

# Get spot details
GET /api/spots/{id}

# Get weather for spot
GET /api/weather/{spot_id}

# Get statistics
GET /api/stats
```

### French Geocoding
```bash
# Geocode address
POST /api/mapping/geocode
Body: {"address": "Place du Capitole, Toulouse"}

# Get elevation
GET /api/mapping/elevation?lat=43.6&lon=1.44

# Find nearest spots
POST /api/mapping/spots/nearest
Body: {"latitude": 43.6, "longitude": 1.44, "radius_km": 10}
```

### IGN Integration
```bash
# Get environmental data
GET /api/ign/spots/{id}/environment

# Get enriched spots
GET /api/ign/spots/enriched

# Get IGN map layers
GET /api/ign/map-layers/ign
```

---

## 🗺️ IGN Services Quick Reference

### WMTS Layers
```javascript
// Base URL for all WMTS services
const WMTS_BASE = 'https://data.geopf.fr/wmts';

// Common parameters
const params = {
    SERVICE: 'WMTS',
    VERSION: '1.0.0',
    REQUEST: 'GetTile',
    TILEMATRIXSET: 'PM',
    FORMAT: 'image/jpeg'
};

// Key layers
const layers = {
    'Plan': 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
    'Scan25': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR',
    'Regional': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-REGIONAL',
    'Satellite': 'ORTHOIMAGERY.ORTHOPHOTOS',
    'Cadastre': 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS'
};
```

### Essential IGN APIs
```python
# Elevation
GET https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json?lon={lon}&lat={lat}

# Geocoding
GET https://data.geopf.fr/geocodage/search?q={address}&limit=10

# Reverse Geocoding
GET https://data.geopf.fr/geocodage/reverse?lon={lon}&lat={lat}

# Isochrone
POST https://data.geopf.fr/navigation/isochrone
```

---

## 🛠️ Common Tasks

### Filter Spots
```bash
# By department
python3 filter_spots_data.py --department 31

# By type
python3 filter_spots_data.py --type waterfall cave

# By elevation
python3 filter_spots_data.py --elevation-min 1000 --elevation-max 2000

# Export results
python3 filter_spots_data.py --department 09 --export ariege_spots.json
```

### Data Management
```bash
# Run scrapers
python3 scripts/run_scrapers.py --all

# Enrich with IGN data
python3 scripts/enrich_with_ign.py

# Quality filter
python3 scripts/quality_filter.py --min-confidence 0.8

# Export for GPS
python3 scripts/export_data.py --format gpx
```

---

## 🔧 Development Commands

### Testing
```bash
# Backend tests
pytest
pytest --cov=src.backend

# Frontend tests
npm test
npm run test:e2e
```

### Database
```bash
# Access database
sqlite3 data/occitanie_spots.db

# Common queries
.tables
SELECT COUNT(*) FROM spots;
SELECT * FROM spots WHERE department = '31';
SELECT department, COUNT(*) FROM spots GROUP BY department;
```

### Git Workflow
```bash
git add .
git commit -m "feat: add IGN elevation service"
git push origin main
```

---

## 🚨 Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```javascript
   // Check CORS is enabled
   // Ensure backend is running on port 8000
   // Use http://localhost:8000 not https
   ```

2. **IGN Tiles Not Loading**
   ```javascript
   // Verify layer name (case sensitive)
   // Check zoom constraints
   // Ensure proper attribution
   ```

3. **Database Errors**
   ```bash
   # Check database exists
   ls -la data/occitanie_spots.db
   
   # Verify schema
   sqlite3 data/occitanie_spots.db ".schema spots"
   ```

### Performance Tips

1. **Enable Clustering**: For >100 markers
2. **Lazy Load**: Load spots progressively
3. **Cache IGN Data**: Store elevation/geocoding results
4. **Use CDN**: For static assets

---

## 📞 Support & Resources

### Project Resources
- **Documentation**: `/home/miko/projects/spots/COMPREHENSIVE_DOCUMENTATION.md`
- **IGN Guide**: `/home/miko/projects/spots/docs/IGN_COMPLETE_GUIDE.md`
- **Frontend Review**: `/home/miko/projects/spots/FRONTEND_REVIEW.md`

### External Links
- **IGN Géoservices**: https://geoservices.ign.fr/
- **API Console**: https://geoservices.ign.fr/console
- **Leaflet Docs**: https://leafletjs.com/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

### Environment Variables
```bash
# .env file
IGN_API_KEY=your-ign-key
MAPBOX_TOKEN=your-mapbox-token
DATABASE_URL=sqlite:///data/occitanie_spots.db
SECRET_KEY=your-secret-key
```

---

## 🎯 Next Steps Priority

1. **Connect Frontend to API** (2-3 days)
   - Create API service module
   - Update spots loader
   - Add error handling

2. **Add TypeScript** (1 week)
   - Type definitions for spots
   - API response types
   - Map component types

3. **Implement Testing** (1 week)
   - Unit tests for API
   - Integration tests
   - E2E tests with Playwright

4. **Deploy to Production** (2 weeks)
   - Docker configuration
   - CI/CD pipeline
   - Domain setup

---

**Remember**: The backend API is fully operational. The highest priority is connecting the frontend to use dynamic data instead of static JSON files.
