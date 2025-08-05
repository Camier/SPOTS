# 📚 SPOTS - Comprehensive Documentation

## 🗺️ Spots Secrets Occitanie
**Version**: 2.2.0  
**Last Updated**: August 2025  
**Coverage**: 13 departments of Occitanie region, France

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Data Sources & IGN Integration](#data-sources--ign-integration)
4. [API Documentation](#api-documentation)
5. [Frontend Documentation](#frontend-documentation)
6. [Installation & Setup](#installation--setup)
7. [Usage Guides](#usage-guides)
8. [Development Guide](#development-guide)
9. [IGN Services Reference](#ign-services-reference)
10. [Deployment](#deployment)

---

## 🌟 Project Overview

SPOTS (Secret Places Occitanie Tourism System) is a comprehensive platform for discovering hidden outdoor locations across the Occitanie region of France. It combines social media intelligence, official geographic data from IGN (Institut national de l'information géographique et forestière), and real-time weather integration.

### Key Features

- **817 verified outdoor spots** across 10 active departments
- **Real-time weather integration** via Open-Meteo API
- **Premium IGN mapping** with official French cartography
- **Multi-source data aggregation** from social media and OpenStreetMap
- **Advanced geocoding** using French government services
- **Mobile-responsive PWA** with offline capabilities

### Technical Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Frontend**: JavaScript ES6, Leaflet.js, Tailwind CSS
- **Database**: SQLite (upgradeable to PostgreSQL)
- **Maps**: IGN France, ESRI, OpenStreetMap
- **APIs**: IGN Géoservices, BAN/BAL, Open-Meteo

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Data Sources      │     │   Backend API       │     │   Frontend App      │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ • Instagram         │────▶│ • FastAPI           │────▶│ • Leaflet Maps      │
│ • Facebook          │     │ • Data Processing   │     │ • Regional View     │
│ • Reddit            │     │ • Geocoding         │     │ • Weather Display   │
│ • OpenStreetMap    │     │ • IGN Integration   │     │ • Spot Filtering    │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         │                           │                            │
         └───────────────────────────┴────────────────────────────┘
                                     │
                              ┌──────▼──────┐
                              │  Database   │
                              │   SQLite    │
                              │ 817 spots   │
                              └─────────────┘
```

### Directory Structure

```
spots/
├── src/
│   ├── backend/          # FastAPI application
│   │   ├── api/         # API endpoints
│   │   ├── scrapers/    # Data collection
│   │   ├── services/    # Business logic
│   │   └── models/      # Database models
│   └── frontend/        # Web interface
│       ├── js/modules/  # ES6 modules
│       ├── css/         # Styles
│       └── *.html       # Map interfaces
├── data/                # Databases & exports
├── scripts/             # Automation tools
├── tests/              # Test suites
└── docs/               # Documentation
```

---

## 🗃️ Data Sources & IGN Integration

### Primary Data Sources

#### 1. OpenStreetMap (95.8% of data)
- **Caves**: 429 locations
- **Waterfalls**: 190 locations
- **Natural Springs**: 107 locations
- **Historical Ruins**: 57 locations

#### 2. Social Media (4.2% of data)
- **Instagram**: Location-tagged posts with Playwright automation
- **Reddit**: r/france, r/toulouse, r/randonnee communities
- **Facebook**: Public outdoor groups

### IGN (Institut Géographique National) Integration

#### Available IGN Services

1. **Cartographic Layers**
   - **SCAN Régional® (1:250,000)**: Regional overview maps
   - **SCAN 25® (1:25,000)**: Detailed topographic maps
   - **Plan IGN**: Multi-scale vector cartography
   - **Photographies aériennes**: High-resolution aerial imagery
   - **Parcellaire Express (PCI)**: Cadastral boundaries

2. **Data Services**
   - **Géocodage**: Address to coordinate conversion
   - **Altimétrie**: Elevation data for any point
   - **Administrative**: Official boundaries (ADMIN EXPRESS)
   - **Environmental**: Protected areas, forests, water bodies

3. **Specialized Datasets**
   - **BD TOPO®**: 3D vector description of territory
   - **BD FORÊT®**: Forest inventory and classification
   - **BD ORTHO®**: Orthophotography coverage
   - **RGE ALTI®**: Digital Elevation Model (DEM)

#### IGN API Implementation

```python
# Elevation Service
GET https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json
?lon=1.4442&lat=43.6047&zonly=true

# Geocoding Service  
GET https://data.geopf.fr/geocodage/search
?q=Toulouse&limit=10&returntruegeometry=true

# WMS/WMTS Layers
https://data.geopf.fr/wmts?
SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&
LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&
TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Currently no authentication required (add for production)

### Endpoints

#### Spots Management

##### GET /api/spots
Retrieve all spots with optional filtering

```javascript
// Request
GET /api/spots?department=31&type=waterfall&limit=50

// Response
{
  "spots": [
    {
      "id": 1,
      "name": "Cascade de la Vallée",
      "latitude": 43.1234,
      "longitude": 1.5678,
      "type": "waterfall",
      "department": "31",
      "elevation": 450.5,
      "description": "Beautiful hidden waterfall",
      "verified": true,
      "confidence_score": 0.95
    }
  ],
  "total": 817,
  "filtered": 25
}
```

##### GET /api/spots/{id}
Get detailed information about a specific spot

##### GET /api/spots/department/{code}
Get all spots in a specific department (09, 12, 31, 32, 46, 65, 81, 82)

##### GET /api/spots/quality
Get high-quality verified spots only

#### Weather Integration

##### GET /api/weather/{spot_id}
Get current weather conditions for a spot
```javascript
{
  "temperature": 22.5,
  "conditions": "clear",
  "wind_speed": 12.3,
  "precipitation": 0,
  "recommendations": ["hiking", "photography"]
}
```

#### French Geocoding Services

##### POST /api/mapping/geocode
Convert address to coordinates using BAN (Base Adresse Nationale)
```javascript
// Request
{
  "address": "Place du Capitole, Toulouse"
}

// Response
{
  "latitude": 43.6047,
  "longitude": 1.4442,
  "confidence": 0.98,
  "source": "BAN"
}
```

##### GET /api/mapping/elevation?lat={lat}&lon={lon}
Get elevation from IGN altimetry service

##### POST /api/mapping/spots/nearest
Find nearest spots to a location
```javascript
{
  "latitude": 43.6047,
  "longitude": 1.4442,
  "radius_km": 10,
  "limit": 5
}
```

#### IGN Data Enrichment

##### GET /api/ign/spots/{id}/environment
Get environmental analysis using IGN data layers
```javascript
{
  "elevation": 854.2,
  "nearest_water": {
    "name": "Lac de Montbel",
    "distance_m": 1250,
    "type": "lake"
  },
  "forest_coverage": 0.75,
  "protected_areas": ["Parc Naturel Régional"],
  "hiking_trails": [
    {
      "name": "GR10",
      "distance_m": 500
    }
  ]
}
```

##### GET /api/ign/map-layers/ign
Get available IGN map layers configuration

#### Statistics

##### GET /api/stats
Get regional statistics
```javascript
{
  "total_spots": 817,
  "departments": {
    "09": {"name": "Ariège", "count": 518},
    "31": {"name": "Haute-Garonne", "count": 83}
  },
  "spot_types": {
    "cave": 429,
    "waterfall": 190,
    "natural_spring": 107
  }
}
```

---

## 🖥️ Frontend Documentation

### Map Interfaces

#### 1. Regional Map (Primary Interface)
**File**: `regional-map.html`  
**Purpose**: Main interface showing all Occitanie departments with spot distribution

Features:
- Department-based filtering
- Zone navigation (Pyrénées, Causses, etc.)
- Marker clustering for performance
- Weather overlay capabilities
- IGN layer switching

#### 2. Premium Map
**File**: `premium-map.html`  
**Purpose**: Advanced mapping with premium providers

Providers:
- IGN official layers (SCAN 25, SCAN Régional, Ortho)
- ESRI World Imagery
- Mapbox Satellite (requires API key)
- MapTiler European maps
- OpenTopoMap for elevation

#### 3. Debug Map
**File**: `debug-map.html`  
**Purpose**: Development and troubleshooting interface

### JavaScript Modules

#### Core Modules
```javascript
// API Service (to be implemented)
import { APIService } from './modules/api-service.js';

// Map Controller
import { MapController } from './modules/map-controller-refactored.js';

// Weather Integration
import { WeatherApp } from './modules/weather-app-refactored.js';

// Spot Data Management
import { HiddenSpotsLoader } from './modules/hidden-spots-loader.js';
```

#### Map Providers Configuration
```javascript
// IGN Layers
const ignLayers = {
  'IGN Plan v2': L.tileLayer(IGN_PLAN_URL),
  'IGN Satellite': L.tileLayer(IGN_ORTHO_URL),
  'IGN SCAN 25': L.tileLayer(IGN_SCAN25_URL),
  'IGN SCAN Régional': L.tileLayer(IGN_REGIONAL_URL)
};
```

### Regional Configuration
```javascript
export const REGIONAL_CONFIG = {
  center: [43.8, 1.8], // Occitanie center
  defaultZoom: 8,
  departments: {
    'ariege': { code: '09', center: [42.9, 1.6] },
    'aveyron': { code: '12', center: [44.35, 2.57] },
    'haute-garonne': { code: '31', center: [43.6, 1.4] },
    'gers': { code: '32', center: [43.65, 0.59] },
    'lot': { code: '46', center: [44.73, 1.67] },
    'hautes-pyrenees': { code: '65', center: [43.05, 0.15] },
    'tarn': { code: '81', center: [43.78, 2.25] },
    'tarn-et-garonne': { code: '82', center: [44.02, 1.36] }
  }
};
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git
- SQLite3

### Quick Start

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/spots-occitanie.git
cd spots-occitanie
```

2. **Backend Setup**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys
```

3. **Frontend Setup**
```bash
# Install Node dependencies
npm install

# Build CSS with Tailwind
npm run build-css
```

4. **Database Setup**
```bash
# Initialize database
python scripts/init_database.py

# Run migrations
python scripts/migrate_data.py
```

5. **Start Services**
```bash
# Terminal 1: Start API
uvicorn src.backend.main:app --reload --port 8000

# Terminal 2: Start Frontend
python -m http.server 8085 --directory src/frontend
```

6. **Access Application**
- Frontend: http://localhost:8085/regional-map.html
- API Docs: http://localhost:8000/docs
- Database: `data/occitanie_spots.db`

---

## 📖 Usage Guides

### For End Users

#### Finding Spots
1. Open the regional map at http://localhost:8085
2. Click on departments to filter spots
3. Use zone navigation for geographic areas
4. Click markers for spot details

#### Map Controls
- **Layer Switcher**: Top-right corner to change base maps
- **Zoom**: Mouse wheel or +/- buttons
- **Clusters**: Click to expand spot groups
- **Search**: Use department or type filters

### For Developers

#### Adding New Spots
```python
from src.backend.models import Spot
from src.backend.database import SessionLocal

db = SessionLocal()
new_spot = Spot(
    name="Hidden Waterfall",
    latitude=43.123,
    longitude=1.456,
    type="waterfall",
    department="31",
    description="Beautiful hidden cascade"
)
db.add(new_spot)
db.commit()
```

#### Extending Scrapers
```python
# Create new scraper in src/backend/scrapers/
class MyCustomScraper:
    def __init__(self):
        self.source_name = "my_source"
    
    async def scrape(self):
        # Implement scraping logic
        spots = []
        return spots
```

#### Using IGN Services
```python
from src.backend.services.ign_service import IGNService

ign = IGNService()

# Get elevation
elevation = await ign.get_elevation(lat=43.6, lon=1.44)

# Get nearby features
features = await ign.get_nearby_features(
    lat=43.6, 
    lon=1.44, 
    radius_m=1000
)
```

---

## 🗺️ IGN Services Reference

### Official IGN Resources

#### Documentation
- **Main Portal**: https://geoservices.ign.fr/
- **API Documentation**: https://geoservices.ign.fr/documentation
- **Data Catalog**: https://geoservices.ign.fr/catalogue
- **Developer Portal**: https://geoservices.ign.fr/services-web

#### Key Services Used

##### 1. Géoplateforme - Core Infrastructure
- **URL**: https://data.geopf.fr/
- **Purpose**: Unified access point for French geographic data
- **Authentication**: API key required for some services

##### 2. WMTS - Web Map Tile Service
```
Base URL: https://data.geopf.fr/wmts
Layers:
- GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2
- GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR
- GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-REGIONAL
- ORTHOIMAGERY.ORTHOPHOTOS
```

##### 3. WMS - Web Map Service
```
Base URL: https://data.geopf.fr/wms
Layers:
- BDTOPO (Topographic database)
- BDFORET (Forest database)
- BDPR (Routes database)
```

##### 4. Altimetry Service
```
Endpoint: https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json
Parameters:
- lon: Longitude (required)
- lat: Latitude (required)
- zonly: Return only elevation (optional)
```

##### 5. Geocoding Service
```
Endpoint: https://data.geopf.fr/geocodage/search
Parameters:
- q: Query string
- limit: Max results
- lat/lon: Reference point for proximity
- returntruegeometry: Include geometry
```

### Data Layers Integration

#### Elevation (RGE ALTI)
- **Resolution**: 1m to 25m depending on area
- **Coverage**: All French territory
- **Format**: GeoTIFF, ASCII Grid
- **Usage**: Spot elevation enrichment

#### Hydrography (BD TOPO)
- **Features**: Rivers, lakes, springs
- **Attributes**: Name, type, flow direction
- **Usage**: Water proximity calculations

#### Transportation (ROUTE 500)
- **Features**: Roads, paths, trails
- **Classification**: GR, PR, local paths
- **Usage**: Access difficulty assessment

#### Land Cover (OCS GE)
- **Categories**: Forest, agriculture, urban
- **Resolution**: 10m
- **Usage**: Environmental context

### IGN Layer Configuration

```javascript
// Optimal configuration for SPOTS project
const ignConfig = {
  // Regional overview (zoom 6-11)
  'SCAN-REGIONAL': {
    url: 'https://data.geopf.fr/wmts',
    layer: 'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-REGIONAL',
    format: 'image/jpeg',
    style: 'normal',
    attribution: '© IGN-F/Géoportail'
  },
  
  // Detailed exploration (zoom 12-17)
  'SCAN25': {
    url: 'https://data.geopf.fr/wmts',
    layer: 'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR',
    format: 'image/jpeg',
    style: 'normal',
    attribution: '© IGN-F/Géoportail'
  },
  
  // Satellite imagery (zoom 1-20)
  'ORTHOPHOTO': {
    url: 'https://data.geopf.fr/wmts',
    layer: 'ORTHOIMAGERY.ORTHOPHOTOS',
    format: 'image/jpeg',
    style: 'normal',
    attribution: '© IGN-F/Géoportail'
  }
};
```

---

## 🔧 Development Guide

### Setting Up Development Environment

#### IDE Configuration
```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.pythonPath": "${workspaceFolder}/venv/bin/python"
}
```

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

### Testing

#### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src.backend

# Run specific test
pytest tests/test_api.py::test_get_spots
```

#### Frontend Tests
```javascript
// Using Jest
npm test

// E2E with Playwright
npm run test:e2e
```

### Data Pipeline

#### 1. Data Collection
```bash
# Run all scrapers
python scripts/run_scrapers.py --all

# Run specific scraper
python scripts/run_scrapers.py --source instagram

# Scheduled scraping (cron)
0 2 * * * cd /path/to/spots && python scripts/run_scrapers.py --all
```

#### 2. Data Enrichment
```bash
# Geocode addresses
python scripts/geocode_spots.py

# Add IGN data
python scripts/enrich_with_ign.py

# Quality filtering
python scripts/quality_filter.py --min-confidence 0.8
```

#### 3. Data Export
```bash
# Export to GeoJSON
python scripts/export_data.py --format geojson

# Export for GPS devices
python scripts/export_data.py --format gpx

# Generate statistics
python scripts/generate_stats.py
```

### API Development

#### Adding New Endpoints
```python
# src/backend/api/my_endpoint.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(db: Session = Depends(get_db)):
    # Implementation
    return {"status": "success"}

# Register in main.py
app.include_router(my_endpoint.router, prefix="/api")
```

#### Custom Middleware
```python
# src/backend/middleware/logging.py
from fastapi import Request
import time

async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"{request.method} {request.url.path} - {process_time:.3f}s")
    return response
```

---

## 🚢 Deployment

### Production Configuration

#### Environment Variables
```bash
# .env.production
DATABASE_URL=postgresql://user:pass@localhost/spots_prod
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
IGN_API_KEY=your-ign-key
MAPBOX_TOKEN=your-mapbox-token
SENTRY_DSN=your-sentry-dsn
```

#### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db/spots
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=spots
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name spots.example.com;

    location / {
        root /var/www/spots/frontend;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Deployment Checklist

- [ ] Set production environment variables
- [ ] Configure HTTPS with Let's Encrypt
- [ ] Setup database backups
- [ ] Configure monitoring (Sentry, Prometheus)
- [ ] Setup log aggregation
- [ ] Configure CDN for static assets
- [ ] Setup rate limiting
- [ ] Enable CORS for production domains
- [ ] Configure caching headers
- [ ] Setup health check endpoints

### Monitoring

#### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.2.0",
        "database": check_database_connection(),
        "services": {
            "ign": check_ign_service(),
            "weather": check_weather_service()
        }
    }
```

#### Metrics Collection
```python
# Using Prometheus
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('app_requests_total', 'Total requests')
request_duration = Histogram('app_request_duration_seconds', 'Request duration')

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

---

## 📚 Additional Resources

### Project Links
- **GitHub**: https://github.com/yourusername/spots-occitanie
- **API Documentation**: http://localhost:8000/docs
- **Issue Tracker**: GitHub Issues

### External Documentation
- **IGN Géoservices**: https://geoservices.ign.fr/documentation
- **Leaflet.js**: https://leafletjs.com/reference.html
- **FastAPI**: https://fastapi.tiangolo.com/
- **Open-Meteo**: https://open-meteo.com/en/docs

### Community
- **Discord**: Join our Discord server
- **Contributing**: See CONTRIBUTING.md
- **Code of Conduct**: See CODE_OF_CONDUCT.md

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

### Data Licenses
- **IGN Data**: Open License 2.0 (Licence Ouverte 2.0)
- **OpenStreetMap**: ODbL (Open Database License)
- **Weather Data**: Open-Meteo Community License

---

**Last Updated**: August 2025  
**Maintained by**: SPOTS Development Team
