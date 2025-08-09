# SPOT Satellite Quick Reference - QGIS

## 🛰️ SPOT Specifications

| SPOT Version | Launch | Resolution (m) | Bands | Swath |
|-------------|--------|----------------|--------|--------|
| SPOT 6/7 | 2012/2014 | PAN: 1.5, MS: 6 | 5 | 60 km |
| SPOT 5 | 2002 | PAN: 2.5/5, MS: 10 | 5 | 60 km |

### Band Wavelengths:
- **B1 Blue**: 0.45-0.52 μm
- **B2 Green**: 0.53-0.59 μm  
- **B3 Red**: 0.62-0.69 μm
- **B4 NIR**: 0.76-0.89 μm
- **PAN**: 0.45-0.75 μm

## 🚀 Quick Start Commands

### 1. Load SPOT in Python Console:
```python
# Quick load
spot = QgsRasterLayer('/path/to/SPOT.tif', 'SPOT')
QgsProject.instance().addMapLayer(spot)
```

### 2. Natural Color (3-2-1):
```
Right-click layer → Properties → Symbology
Render type: Multiband color
Red: Band 3, Green: Band 2, Blue: Band 1
```

### 3. Quick NDVI:
```
Processing Toolbox → search "Raster calculator"
Expression: (B4-B3)/(B4+B3)
```

### 4. Download Toulouse Reference Data:
```
Vector → QuickOSM → Quick Query
Key: landuse, In: Toulouse, France
Run query
```

## 🎨 Useful Band Combinations

| Purpose | RGB Bands | Highlights |
|---------|-----------|------------|
| Natural Color | 3-2-1 | True color view |
| Vegetation | 4-3-2 | Vegetation in red |
| Urban | 4-3-1 | Built areas enhanced |
| Agriculture | 4-2-1 | Crop differentiation |

## 📊 Key Indices

### NDVI (Vegetation):
```
(NIR - Red) / (NIR + Red) = (B4 - B3) / (B4 + B3)
```

### NDWI (Water):
```
(Green - NIR) / (Green + NIR) = (B2 - B4) / (B2 + B4)
```

### NDBI (Built-up):
```
(SWIR - NIR) / (SWIR + NIR)
Note: SPOT doesn't have SWIR, use alternative indices
```

## 🔧 Processing Menu Locations

### Semi-Automatic Classification Plugin:
- **Band Set**: Raster → SCP → Band set
- **ROI Creation**: SCP → Training input
- **Classification**: SCP → Band processing → Classification
- **Preprocessing**: SCP → Preprocessing → [various tools]

### GDAL Tools:
- **Merge**: Raster → Miscellaneous → Merge
- **Clip**: Raster → Extraction → Clip raster by extent
- **Reproject**: Raster → Projections → Warp
- **Pansharp**: Processing → GDAL → Raster miscellaneous → Pansharpening

### SAGA Tools:
- **Terrain**: Processing → SAGA → Terrain Analysis
- **Filters**: Processing → SAGA → Raster filter

## 🎯 Toulouse-Specific Tasks

### Get Toulouse Extent:
```python
# Toulouse bounding box (WGS84)
toulouse_bbox = QgsRectangle(1.35, 43.53, 1.53, 43.67)

# For UTM Zone 31N
# toulouse_bbox = QgsRectangle(372000, 4825000, 390000, 4840000)
```

### Common CRS for Toulouse:
- **Geographic**: EPSG:4326 (WGS84)
- **Projected**: EPSG:32631 (UTM Zone 31N)
- **Local**: EPSG:2154 (Lambert-93, France)

## 📝 Classification Workflow

1. **Prepare Data**:
   - Load SPOT image
   - Create band set in SCP
   
2. **Collect Training Samples**:
   - Urban (red)
   - Vegetation (green)
   - Water (blue)
   - Agriculture (yellow)
   - Bare soil (brown)

3. **Run Classification**:
   - Maximum Likelihood
   - Check "Algorithm band set"
   - Output: classified.tif

4. **Post-Process**:
   - Sieve (remove small patches)
   - Accuracy assessment
   - Area statistics

## ⚡ Keyboard Shortcuts

- **Pan**: Space + drag
- **Zoom**: Ctrl + mouse wheel
- **Identify**: Ctrl + Shift + I
- **Measure**: Ctrl + Shift + M
- **Python Console**: Ctrl + Alt + P

## 🐍 Quick Python Snippets

### Get Layer Info:
```python
layer = iface.activeLayer()
print(f"Bands: {layer.bandCount()}")
print(f"Size: {layer.width()} x {layer.height()}")
print(f"CRS: {layer.crs().authid()}")
```

### Export Current View:
```python
iface.mapCanvas().saveAsImage('/path/to/export.png')
```

### Add Basemap:
```python
# After enabling QuickMapServices
from qgis.utils import iface
iface.mainWindow().findChild(QAction, 'mActionAddWmsLayer').trigger()
```

## 📊 Quick Stats in Python:
```python
provider = layer.dataProvider()
stats = provider.bandStatistics(1, QgsRasterBandStats.All)
print(f"Min: {stats.minimumValue}")
print(f"Max: {stats.maximumValue}")
print(f"Mean: {stats.mean}")
```

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Black image | Adjust min/max in Symbology |
| Wrong colors | Check band order (3-2-1) |
| Slow loading | Build pyramids |
| Can't classify | Install/enable SCP plugin |
| No basemaps | Configure QuickMapServices |

## 📁 Project Structure
```
SPOT_Project/
├── spot_processing_tools.py  # Python functions
├── SPOT_QGIS_Workflow.md    # Full guide
├── quick_reference.md        # This file
└── data/
    ├── raw/                 # Original SPOT
    ├── processed/           # Corrections
    └── results/             # Classifications
```

---
**Pro Tip**: Save this as a PDF (Ctrl+P) and keep it handy while working! 📌
