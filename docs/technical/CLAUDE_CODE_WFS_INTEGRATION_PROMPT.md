# Claude Code Prompt: IGN WFS Integration for SPOTS Platform

## Project Context
I'm working on the SPOTS project at `/home/miko/projects/spots` - a platform for discovering 817 hidden outdoor locations across Occitanie, France. It has:

- **Backend**: Python/FastAPI (port 8000) with SQLite database
- **Frontend**: JavaScript/Leaflet (port 8085) with IGN French maps  
- **Current IGN Integration**: Static OpenData processing + 15+ WMTS layers
- **Architecture**: Fully functional API with glassmorphism frontend

## Integration Goal
Enhance the existing IGN integration by adding **real-time WFS (Web Feature Service)** capabilities for dynamic vector data queries from IGN Géoplateforme.

## Files to Integrate

### Backend Files (Created, Need Integration):
1. `src/backend/services/ign_wfs_service.py` - WFS service class (✅ Ready)
2. `src/backend/api/wfs_endpoints_addition.py` - New API endpoints (✅ Ready)

### Frontend Files (Created, Need Integration):
3. `src/frontend/js/ign-wfs-client.js` - JavaScript WFS client (✅ Ready)

### Reference Files:
4. `IGN_WFS_INTEGRATION_GUIDE.md` - Complete integration instructions
5. `test_ign_wfs_integration.py` - Test suite for validation

## Tasks for Claude Code

### 1. Backend Integration (Priority 1)

**Integrate WFS Service into Existing API:**
- Add WFS service import to `src/backend/api/ign_data.py`
- Copy the 5 new endpoints from `wfs_endpoints_addition.py` into the existing router
- Ensure proper imports and dependencies
- Maintain existing functionality unchanged

**Key Requirements:**
- Add `from ..services.ign_wfs_service import IGNWFSService`
- Initialize `wfs_service = IGNWFSService()` after existing `ign_service`
- Add these endpoints to the existing router:
  - `/wfs/capabilities`
  - `/spots/{spot_id}/wfs-analysis` 
  - `/wfs/transport`
  - `/wfs/hydrography`
  - `/wfs/administrative`

### 2. Frontend Integration (Priority 2)

**Update Main Map Interface:**
- Integrate `ign-wfs-client.js` into `src/frontend/enhanced-map-ign-advanced.html`
- Add WFS layer controls to existing layer management
- Implement click-to-analyze functionality for spots
- Add WFS analysis results display panel

**Key Requirements:**
- Include the WFS client script
- Initialize `const wfsClient = new IGNWFSClient('http://localhost:8000/api/ign')`
- Add WFS layers to existing layer control system
- Implement spot analysis button/functionality
- Maintain existing glassmorphism UI design

### 3. Testing & Validation (Priority 3)

**Ensure Integration Works:**
- Run the test suite: `python test_ign_wfs_integration.py`
- Verify all 5 new API endpoints respond correctly
- Test frontend WFS client functionality
- Validate map interactions work properly

## Current Project Structure

```
spots/
├── src/
│   ├── backend/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── mapping_france.py   # Existing mapping API
│   │   │   └── ign_data.py         # 🎯 MAIN INTEGRATION TARGET
│   │   ├── services/
│   │   │   └── ign_wfs_service.py  # ✅ Ready to integrate
│   │   └── scrapers/
│   └── frontend/
│       ├── enhanced-map-ign-advanced.html  # 🎯 MAIN FRONTEND TARGET
│       └── js/
│           └── ign-wfs-client.js    # ✅ Ready to integrate
├── data/
│   └── occitanie_spots.db          # 817 spots database
└── IGN_WFS_INTEGRATION_GUIDE.md    # 📖 Complete instructions
```

## Implementation Approach

### Phase 1: Backend (30 minutes)
1. **Read existing `src/backend/api/ign_data.py`** to understand current structure
2. **Integrate WFS service** following the patterns in `wfs_endpoints_addition.py`
3. **Maintain backward compatibility** - don't modify existing endpoints
4. **Test API endpoints** with curl/httpie

### Phase 2: Frontend (45 minutes)
1. **Read existing `enhanced-map-ign-advanced.html`** to understand current architecture
2. **Integrate WFS client** maintaining existing glassmorphism design
3. **Add interactive features** for spot analysis and WFS layer visualization
4. **Test in browser** at http://localhost:8085

### Phase 3: Validation (15 minutes)
1. **Run test suite** to validate WFS connectivity
2. **Test complete workflow** from frontend to backend
3. **Verify 817 spots** work with new WFS analysis features

## Critical Requirements

### ✅ Must Preserve:
- All existing API functionality
- Current frontend design and UX
- 817 spots database integrity
- Existing IGN WMTS layers and features
- Current development workflow

### 🚀 Must Add:
- Real-time WFS vector data queries
- Interactive spot environment analysis
- Dynamic map layer integration
- Accessibility scoring for spots
- Error handling and performance optimization

## Success Criteria

1. **Backend**: All 5 WFS endpoints return valid responses
2. **Frontend**: Click-to-analyze works with real-time data visualization
3. **Integration**: Existing functionality unchanged, new features working
4. **Testing**: `test_ign_wfs_integration.py` passes all tests
5. **User Experience**: Seamless blend of static and dynamic IGN data

## Development Notes

- **Python Version**: 3.12
- **FastAPI Version**: Latest stable
- **Database**: SQLite with 817 spots
- **Frontend**: Vanilla JS + Leaflet + IGN layers
- **Styling**: Glassmorphism design system
- **CORS**: Already configured for localhost development

## References

- **Integration Guide**: `IGN_WFS_INTEGRATION_GUIDE.md` - Complete step-by-step instructions
- **IGN Documentation**: https://geoservices.ign.fr/services-web
- **WFS Standard**: OGC Web Feature Service 2.0.0
- **Project Context**: See `SPOTS_QUICKREF.md` for full project overview

---

**Goal**: Transform SPOTS from a static spot database into a dynamic geographic analysis platform with real-time IGN data integration, while preserving all existing excellent functionality.

**Estimated Time**: 1.5 hours for complete integration and testing.
