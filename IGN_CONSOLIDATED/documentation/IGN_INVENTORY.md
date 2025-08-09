# IGN Data Consolidated Inventory

## Overview
Complete consolidation of all IGN (Institut Géographique National) data for the SPOTS project.

## Directory Structure
```
IGN_CONSOLIDATED/
├── offline_tiles/      # All MBTiles databases
├── cache_recovery/     # Recovered data from 848MB cache
├── projects/          # QGIS project files (.qgz)
├── scripts/           # Python scripts for downloading and management
├── config/            # Configuration files
├── documentation/     # This file and other docs
└── exports/          # Exported maps and data
```

## Data Summary

### Offline Tiles (16+ MB)
- **ign_plan.mbtiles** - 9.3 MB - Street maps (Plan IGN v2)
- **ign_ortho.mbtiles** - 3.3 MB - Aerial photography
- **ign_parcelles.mbtiles** - 244 KB - Cadastral parcels
- **osm.mbtiles** - 3.2 MB - OpenStreetMap backup
- **ign_cartes.mbtiles** - 20 KB - Maps (needs more tiles)
- **ign_scan25.mbtiles** - 20 KB - Scan 25 (needs more tiles)

### Cache Data (848 MB)
- **Location**: `/home/miko/IGN_DATA/CACHE/`
- **Files**: 10,401 cached tiles
- **Format**: .d files (image data)
- **Potential**: Could yield 500MB+ of organized tiles

### QGIS Projects (9 files)
1. **spots_offline_complete.qgz** - Latest complete project
2. **spots_unified_with_analysis.qgz** - With spatial analysis
3. **spots_occitanie_final.qgz** - Final Occitanie project
4. **toulouse_spots.qgz** - Toulouse focused
5. **spots_enhanced.qgz** - Enhanced features
6. **spots_unified.qgz** - Unified database
7. **spots_working.qgz** - Working version
8. **spots_occitanie_working.qgz** - Occitanie working
9. **spots_offline.qgz** - Basic offline version

### Scripts
- **download_ign_wmts.py** - Download IGN tiles via WMTS
- **download_ign_tiles.py** - IGN tile downloader
- **download_osm_tiles.py** - OSM tile downloader
- **analyze_ign_cache.py** - Cache recovery tool
- **load_mbtiles_qgis.py** - Load MBTiles in QGIS
- **geoplateforme_oauth2.py** - OAuth2 configuration

### Configuration
- OAuth2 settings for Géoplateforme
- WMTS endpoints configuration
- Authentication credentials (secured)

## Coverage Areas

### Current Coverage
- **Toulouse**: Urban area, 1.35-1.50°E, 43.55-43.65°N
- **Pyrenees Caves**: 1.45-1.65°E, 42.75-42.85°N
- **Montpellier**: 3.30-3.45°E, 43.55-43.70°N
- **Carcassonne**: 2.30-2.40°E, 43.18-43.25°N

### Zoom Levels
- Overview: Z8-10
- Regional: Z11-12
- Local detail: Z13-14
- High detail: Z15-16 (limited areas)

## Access Points

### WMTS Services
- **Public**: https://data.geopf.fr/wmts
- **Private**: https://data.geopf.fr/private/wmts (requires auth)
- **Legacy**: https://wxs.ign.fr/essentiels/geoportail/wmts

### Web Interfaces
- Géoportail: https://www.geoportail.gouv.fr
- Géoservices: https://geoservices.ign.fr

## Storage Strategy

### Current (16 MB)
- Basic offline coverage for key SPOTS areas
- Functional for offline navigation

### Target (50 GB)
- Complete Occitanie coverage
- Multi-scale from Z8 to Z16
- All IGN layers (Plan, Scan25, Ortho, Parcelles)

### Potential (with cache recovery)
- Additional 500MB+ from existing cache
- No new downloads needed
- Immediate availability

## Usage Instructions

### Loading in QGIS
```python
from qgis.core import QgsRasterLayer, QgsProject
import os

base_dir = "/home/miko/Development/projects/spots/IGN_CONSOLIDATED"
mbtiles = os.path.join(base_dir, "offline_tiles/ign_plan.mbtiles")
layer = QgsRasterLayer(mbtiles, "IGN Plan", "gdal")
QgsProject.instance().addMapLayer(layer)
```

### Continuing Downloads
```bash
cd /home/miko/Development/projects/spots/IGN_CONSOLIDATED/scripts
python3 download_ign_wmts.py
```

### Cache Recovery
```bash
python3 analyze_ign_cache.py
```

## Status
- ✅ Initial consolidation complete
- ✅ 16 MB offline tiles available
- ⏳ Cache recovery in progress
- ⏳ Expanding to 50GB target

## Next Steps
1. Run cache recovery to extract 848MB data
2. Continue tile downloads for broader coverage
3. Create automated sync system
4. Build mobile-ready exports

---
*Last updated: August 9, 2025*