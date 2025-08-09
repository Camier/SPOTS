# 🗺️ SPOTS Project Quick Reference

**Path**: `/home/miko/projects/spots`  
**Description**: Hidden outdoor spots discovery platform for Occitanie, France  
**Data**: 817 verified spots | 10 departments | 4 types (caves, waterfalls, springs, ruins)

## 🔗 Access
- Frontend: http://localhost:8085/regional-map.html
- API: http://localhost:8000/docs
- DB: `data/occitanie_spots.db`

## 🛠️ Tech
- **Backend**: Python/FastAPI/SQLite → ✅ Working
- **Frontend**: JS/Leaflet/IGN Maps → ⚠️ Using static JSON
- **Scraping**: Playwright/Instagram → ✅ Working

## 📂 Structure
```
spots/
├── src/backend/main.py      # API server
├── src/frontend/            # 11 map interfaces
├── data/occitanie_spots.db  # 817 spots
└── scripts/filter_spots.py  # Data tools
```

## ⚡ Commands
```bash
cd /home/miko/projects/spots
uvicorn src.backend.main:app --reload  # Start API
python -m http.server 8085 -d src/frontend  # Start UI
```

## 🎯 Status
- ✅ API: 14+ endpoints operational
- ✅ Maps: IGN + 15 providers configured  
- ✅ Data: 817 spots (63% Ariège)
- ❌ Integration: Frontend↔API disconnected

**Next**: Connect frontend to API (2-3 days)
