## SPOTS Project - Concise Overview

**What**: Web platform discovering 817 hidden outdoor spots across Occitanie, France through social media mining and official IGN mapping services.

**Where**: `/home/miko/projects/spots`

**Stack**: 
- Backend: Python 3.12 + FastAPI + SQLite (http://localhost:8000)
- Frontend: JavaScript + Leaflet.js + IGN maps (http://localhost:8085)
- Scraping: Playwright for Instagram/Reddit data

**Key Components**:
- `src/backend/main.py` - API with 14+ endpoints
- `src/frontend/regional-map.html` - Main map interface  
- `data/occitanie_spots.db` - 817 spots across 10 departments
- 95.8% data from OpenStreetMap, 4.2% from social media

**Current Issue**: Frontend loads static JSON instead of using the fully functional API (needs 2-3 days to fix)

**Features**: French geocoding (BAN), IGN elevation data, weather integration (Open-Meteo), multi-language map layers, spot clustering, mobile PWA-ready

**To Run**:
```bash
cd /home/miko/projects/spots
# Backend: source venv/bin/activate && uvicorn src.backend.main:app --reload
# Frontend: python -m http.server 8085 --directory src/frontend
```
