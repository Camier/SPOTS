# 🗺️ IGN Open Data Download Guide for Occitanie

## Overview
The [IGN France OpenData Download UI](https://geotribu.github.io/ign-fr-opendata-download-ui/index.html) by Geotribu provides an interactive map interface to download official IGN geographic data products for any French department or region, including all of Occitanie.

## 🎯 Relevance for Spots Project

### Available Data Products for Occitanie

#### 1. **BDORTHO** (Orthophotography) 📸
- High-resolution aerial imagery
- Available formats: IRC (Infrared) and RVB (True Color)
- Resolution: 20cm (ORTHOHR) or 50cm (BDORTHO)
- **Use case**: Visual validation of outdoor spots, terrain analysis

#### 2. **BDTOPO** (Topographic Database) 🏔️
- Complete topographic features
- Includes: buildings, roads, hydrography, vegetation
- Vector format (Shapefile, GeoPackage)
- **Use case**: Identifying water bodies, trails, access routes

#### 3. **BDFORET** (Forest Database) 🌲
- Forest coverage and types
- Forest boundaries and classifications
- **Use case**: Finding forest spots, camping areas

#### 4. **RGEALTI** (Elevation Model) 📏
- Digital Elevation Model (DEM)
- 1m, 5m, or 25m resolution
- **Use case**: Elevation profiles, viewpoint analysis

#### 5. **BDPARCELLAIRE** (Cadastral Parcels) 🏘️
- Land ownership boundaries
- Property information
- **Use case**: Understanding land access rights

#### 6. **RPG** (Agricultural Land Registry) 🌾
- Agricultural parcels and crop types
- Updated annually
- **Use case**: Avoiding private agricultural land

## 📥 How to Download Data for Occitanie

### Method 1: Interactive Map (Easy)
1. Visit https://geotribu.github.io/ign-fr-opendata-download-ui/index.html
2. Select layer type: DEP (department), REGION, or FR (France)
3. Choose data product (e.g., BDTOPO, BDORTHO)
4. Click on Occitanie departments:
   - 09 (Ariège)
   - 11 (Aude)
   - 12 (Aveyron)
   - 30 (Gard)
   - 31 (Haute-Garonne)
   - 32 (Gers)
   - 34 (Hérault)
   - 46 (Lot)
   - 48 (Lozère)
   - 65 (Hautes-Pyrénées)
   - 66 (Pyrénées-Orientales)
   - 81 (Tarn)
   - 82 (Tarn-et-Garonne)
5. Download links appear in popup

### Method 2: Direct Links Pattern
URLs follow this pattern:
```
https://wxs.ign.fr/{product}/telechargement/prepackage/{product}_D{dept}_latest.7z
```

Example for Hérault (34):
- BDTOPO: `https://wxs.ign.fr/bdtopo/telechargement/prepackage/BDTOPO_D034_latest.7z`
- BDORTHO: `https://wxs.ign.fr/bdortho/telechargement/prepackage/BDORTHO_D034_latest.7z`

### Method 3: Automated Script
```bash
# Clone the repository
git clone https://github.com/geotribu/ign-fr-opendata-download-ui.git
cd ign-fr-opendata-download-ui

# Configure for Occitanie departments
cp example.env .env
# Edit .env to include only Occitanie departments:
# LI_DEPARTEMENTS="009,011,012,030,031,032,034,046,048,065,066,081,082"

# Run the scraper
bash ignfr2map.sh
```

## 🔧 Integration with Spots Project

### Priority Downloads for Outdoor Spots

1. **BDTOPO** - Essential for:
   - Water features (lakes, rivers)
   - Trails and paths
   - Points of interest
   - Access roads

2. **RGEALTI** - Critical for:
   - Elevation data
   - Slope analysis
   - Viewpoint identification

3. **BDORTHO** - Useful for:
   - Visual validation
   - Spot accessibility
   - Terrain features

4. **BDFORET** - Important for:
   - Forest trails
   - Camping spots
   - Nature areas

### Data Processing Pipeline
```python
# Example: Process BDTOPO water features for swimming spots
import geopandas as gpd
from shapely.geometry import Point

# Load BDTOPO hydrography
hydro = gpd.read_file('BDTOPO_34_HYDROGRAPHIE.shp')

# Filter for lakes and water bodies
lakes = hydro[hydro['NATURE'].isin(['Lac', 'Plan d\'eau', 'Retenue'])]

# Check if spots are near water
for spot in occitanie_spots:
    point = Point(spot['lon'], spot['lat'])
    nearby_water = lakes[lakes.distance(point) < 500]  # Within 500m
    if not nearby_water.empty:
        spot['water_access'] = True
        spot['water_feature'] = nearby_water.iloc[0]['NOM']
```

## 📊 Data Volume Estimates

| Department | BDTOPO | BDORTHO | RGEALTI | BDFORET |
|------------|--------|---------|---------|---------|
| Hérault (34) | ~300MB | ~15GB | ~2GB | ~50MB |
| Haute-Garonne (31) | ~400MB | ~20GB | ~3GB | ~80MB |
| Pyrénées-Orientales (66) | ~250MB | ~12GB | ~2.5GB | ~100MB |

**Total for Occitanie**: ~100GB for all products

## 🚀 Quick Start Commands

### Download BDTOPO for all Occitanie
```bash
#!/bin/bash
DEPTS="009 011 012 030 031 032 034 046 048 065 066 081 082"
for dept in $DEPTS; do
    wget "https://wxs.ign.fr/bdtopo/telechargement/prepackage/BDTOPO_D${dept}_latest.7z"
done
```

### Extract and process
```bash
# Extract all files
for file in BDTOPO_D*.7z; do
    7z x "$file"
done

# Merge all shapefiles
ogr2ogr -f "GPKG" occitanie_hydro.gpkg BDTOPO_D009*/HYDROGRAPHIE.shp
for dept in 011 012 030 031 032 034 046 048 065 066 081 082; do
    ogr2ogr -update -append occitanie_hydro.gpkg BDTOPO_D${dept}*/HYDROGRAPHIE.shp
done
```

## 💡 Best Practices

1. **Start with BDTOPO** - Most useful for spot identification
2. **Use elevation data** - Essential for hiking/climbing spots
3. **Cross-reference with orthophotos** - Validate accessibility
4. **Check forest data** - Understand land use restrictions
5. **Automate downloads** - Use scripts for regular updates

## 🔗 Resources

- **Interactive Map**: https://geotribu.github.io/ign-fr-opendata-download-ui/
- **GitHub Repository**: https://github.com/geotribu/ign-fr-opendata-download-ui
- **IGN Open Data Portal**: https://geoservices.ign.fr/
- **Data Documentation**: https://geoservices.ign.fr/documentation/

---

*This tool provides free access to official IGN geographic data, perfect for enriching our Occitanie outdoor spots database with authoritative topographic, elevation, and land use information.*