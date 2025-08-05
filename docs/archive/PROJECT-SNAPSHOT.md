# 📸 PROJECT SNAPSHOT: SPOTS SECRETS OCCITANIE
*Generated: August 4, 2025*

## 🎯 Project Overview
**Name**: Spots Secrets - Occitanie  
**Version**: 2.0.0  
**Description**: Discover outdoor spots in Occitanie with real-time weather integration  
**Language**: Python (Backend) + JavaScript (Frontend)  
**License**: MIT  

## 📊 Project Statistics
- **Total Files**: 289,097
- **Total Directories**: 36,785
- **Total Size**: 53.85 GiB
- **Python Files**: 3,703
- **JavaScript Files**: 3,850
- **HTML Files**: 59
- **CSS Files**: 17

## 🏗️ Architecture Overview

### Backend (Python/FastAPI)
- **Framework**: FastAPI v0.109.0 with Uvicorn
- **Database**: SQLite + SQLAlchemy ORM
- **Main Entry**: `src/backend/main.py`
- **API Endpoints**: 
  - `/api/mapping` - France mapping services
  - `/api/ign` - IGN data integration
  - `/api/spots` - Spot management
  - `/api/weather` - Weather integration

### Frontend (JavaScript/Leaflet)
- **Type**: Progressive Web App (PWA)
- **Framework**: Vanilla JavaScript (ES6 Modules)
- **Mapping**: Leaflet v1.9.4 + MarkerCluster
- **Entry Point**: `src/frontend/index.html`
- **Module System**: ES6 Modules

## 📦 Key Dependencies

### JavaScript Dependencies
```json
{
  "leaflet": "^1.9.4",
  "leaflet.markercluster": "^1.5.3"
}
```

### Python Core Dependencies
- **Web Framework**: FastAPI (0.109.0), Uvicorn (0.27.0)
- **Database**: SQLAlchemy (2.0.25), Alembic (1.13.1)
- **Web Scraping**: Playwright (1.41.1), Selenium (4.17.2), BeautifulSoup4 (4.12.3)
- **Data Processing**: Pandas (2.2.0), NumPy (2.2.1)
- **Geocoding**: Geopy (2.4.1), PyProj (3.6.1)
- **Social APIs**: AsyncPRAW (7.7.1), InstaGrapi (2.1.0)
- **NLP**: SpaCy (3.7.2) with French model

## 📁 Directory Structure

```
spots/
├── src/
│   ├── backend/            # Python backend
│   │   ├── api/           # API endpoints
│   │   ├── scrapers/      # Data collection (20+ scrapers)
│   │   ├── processors/    # Data processing
│   │   ├── validators/    # Data validation
│   │   └── main.py       # FastAPI app
│   └── frontend/          # Web interface
│       ├── js/           # JavaScript modules
│       │   └── modules/  # Core functionality
│       ├── css/          # Stylesheets
│       ├── pwa/          # PWA manifests
│       └── index.html    # Main entry
├── tests/                 # Test suites
├── docs/                  # Documentation
├── scripts/              # Utility scripts
├── data/                 # Data storage
└── config/               # Configuration
```

## 🚀 Main Entry Points

### Backend
- **API Server**: `src/backend/main.py` - FastAPI application
- **CLI Tools**: Various scrapers in `src/backend/scrapers/`
- **Data Pipeline**: `src/backend/data_management/`

### Frontend
- **Web App**: `src/frontend/index.html`
- **JavaScript Entry**: `src/frontend/js/modules/index.js`
- **Map Controller**: `src/frontend/js/modules/map-controller-refactored.js`

## 🌍 Core Features

### 1. Multi-Source Data Collection
- Reddit scraper (French communities)
- Instagram scraper (unified strategy pattern)
- OpenStreetMap integration
- Tourism sites scraper
- Facebook data miner

### 2. Intelligent Geocoding
- IGN Géoplateforme integration
- Ola Maps API support
- Coordinate extraction from text
- EPSG:3857 reprojection

### 3. Map Layers (IGN Official)
- SCAN25 (1:25,000 topographic)
- Satellite imagery
- Cadastral parcels
- Hiking trails
- Administrative boundaries

### 4. Data Validation
- Pydantic schemas
- GPS coordinate validation
- Duplicate detection
- Privacy compliance

## 📈 Recent Activity (Git Log)
```
ef0dfe0 fix: Convert E2E tests from CommonJS to ESM format
8b3e77d fix: Update IGN layer URLs to data.geopf.fr and add data downloader
457560d feat: Implement comprehensive data validation system
83deefb 📚 Add comprehensive data scraping documentation
45d223b 🚀 Implement real data scraping infrastructure for Occitanie spots
b1c9163 feat: Complete consolidation of scattered Toulouse Weather Spots projects
```

## 🔧 Development Scripts

### NPM Scripts
- `npm run dev` - Start development server
- `npm test` - Run Vitest tests
- `npm run lint` - ESLint code check
- `npm run format` - Prettier formatting

### Python Scripts
- `python -m src.backend.main` - Start API server
- `python src/backend/scrapers/reddit_scraper.py` - Run Reddit scraper
- `python src/backend/scrapers/unified_instagram_scraper.py` - Run Instagram scraper

## 🎯 Technical Achievements
1. **IGN Migration**: Successfully migrated from wxs.ign.fr to data.geopf.fr
2. **Test Infrastructure**: Full ESM module support with Vitest
3. **Scraper Consolidation**: Unified 5 Instagram scrapers into 1 strategy pattern
4. **Data Pipeline**: Automated validation and geocoding pipeline
5. **PWA Support**: Offline capability with service workers

## 🏗️ Architecture Highlights
- **Modular Design**: Clear separation of concerns
- **Strategy Pattern**: Flexible scraper implementations
- **Mixin Pattern**: Reusable geocoding functionality
- **Event-Driven**: Frontend uses custom events
- **Async First**: Python async/await throughout

## 🔒 Security & Compliance
- GDPR-compliant data collection
- No personal data storage
- API key management via environment variables
- CORS configuration for production
- Input validation at all levels

## 📝 Notes
- Project covers 8 departments in Occitanie region
- Real data only - no mocking or simulation
- Focus on outdoor activities and hidden spots
- Weather integration for activity recommendations
- Mobile-first responsive design

---
*This snapshot represents the current state of the Spots Secrets Occitanie project, a comprehensive platform for discovering and sharing outdoor locations across the Occitanie region of France.*