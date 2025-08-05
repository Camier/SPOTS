# SPOTS Project - Quick Context

**Project**: SPOTS (Secret Places Occitanie Tourism System)
**Location**: `/home/miko/projects/spots`
**Purpose**: Discover hidden outdoor spots across Occitanie, France using social media mining + official IGN maps

## Access Points
- **Frontend**: http://localhost:8085/regional-map.html
- **API Docs**: http://localhost:8000/docs
- **Database**: `data/occitanie_spots.db` (817 spots)

## Tech Stack
- **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLite
- **Frontend**: JavaScript ES6, Leaflet.js, 15+ map providers
- **Scraping**: Playwright/Puppeteer for Instagram/Reddit
- **APIs**: IGN Géoservices, Open-Meteo, BAN geocoding

## Key Files
```
src/
├── backend/main.py          # FastAPI server
├── frontend/
│   ├── regional-map.html    # Main interface
│   ├── js/modules/          # 14 ES6 modules
│   └── enhanced-map-ign-advanced.html  # Advanced IGN
data/
├── occitanie_spots.db       # 817 spots (10 departments)
scripts/
├── filter_spots_data.py     # Data filtering tool
```

## Quick Start
```bash
cd /home/miko/projects/spots
# Terminal 1: Backend
source venv/bin/activate && uvicorn src.backend.main:app --reload
# Terminal 2: Frontend  
python -m http.server 8085 --directory src/frontend
```

## Current Status
✅ Backend API fully operational (14+ endpoints)
❌ Frontend using static JSON instead of API
✅ 817 verified spots (Ariège 63%, Haute-Garonne 10%)
✅ IGN integration with premium French maps
✅ Social media scraping functional

## Main Features
- Multi-source data: OpenStreetMap (95.8%), Instagram/Reddit (4.2%)
- Spot types: Caves (52%), Waterfalls (23%), Springs (13%)
- French geocoding + elevation data
- Weather integration per spot
- Mobile-responsive PWA ready

## Documentation
- `COMPREHENSIVE_DOCUMENTATION.md` (899 lines)
- `docs/IGN_COMPLETE_GUIDE.md` (569 lines)
- `FRONTEND_REVIEW.md` (513 lines)
- `QUICK_REFERENCE.md` (286 lines)

**Priority Task**: Connect frontend to API (2-3 days work)
