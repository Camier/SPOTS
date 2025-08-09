# SPOT Satellite Project Workflow in QGIS

## 🛰️ Working with SPOT Imagery in QGIS

### Step 1: Load Your SPOT Data

#### For SPOT 6/7 (1.5m resolution):
```
1. Drag & drop your SPOT files into QGIS, or:
2. Layer → Add Layer → Add Raster Layer
3. Select your SPOT files:
   - .TIF/.TIFF (GeoTIFF format)
   - .JP2 (JPEG2000 format)
   - DIMAP format (.DIM + data folder)
```

#### Typical SPOT Band Configuration:
- **Band 1**: Blue (0.450-0.520 μm)
- **Band 2**: Green (0.530-0.590 μm)
- **Band 3**: Red (0.625-0.695 μm)
- **Band 4**: Near-Infrared (0.760-0.890 μm)
- **PAN**: Panchromatic (0.450-0.745 μm) - 1.5m resolution

### Step 2: Create Natural Color Composite

1. **For Multispectral Display**:
   - Right-click layer → Properties → Symbology
   - Render type: "Multiband color"
   - Red band: Band 3
   - Green band: Band 2
   - Blue band: Band 1

2. **Enhance Contrast**:
   - Min/Max Value Settings
   - Choose "Cumulative count cut" (2-98%)
   - Click "Apply"

### Step 3: Pan-Sharpening (if you have PAN band)

Using GDAL:
```
Processing Toolbox → GDAL → Raster miscellaneous → Build Virtual Raster
Then: GDAL → Raster miscellaneous → Pansharpening
```

### Step 4: Use Semi-Automatic Classification Plugin (SCP)

#### Initial Setup:
1. **Raster** → **SCP** → **Band set**
2. Click "Refresh list" 🔄
3. Select your SPOT bands
4. Quick wavelength: Select "SPOT 6"
5. Click "Add band set"

#### Create Training Samples:
1. **SCP** → **Training input**
2. Create ROIs (Regions of Interest):
   - Urban areas
   - Vegetation
   - Water bodies
   - Bare soil
   - Roads

3. **Collect signatures** (at least 20-30 per class)
4. **Save training input**

#### Run Classification:
1. **SCP** → **Band processing** → **Classification**
2. Algorithm options:
   - Maximum Likelihood
   - Minimum Distance
   - Spectral Angle Mapping
3. Use MC ID (Macroclass) for broader classes
4. Click "Run" ▶️

### Step 5: Calculate Vegetation Indices

#### NDVI (Normalized Difference Vegetation Index):
```
Processing Toolbox → Raster analysis → Raster calculator
Expression: (Band4 - Band3) / (Band4 + Band3)
Where: Band4 = NIR, Band3 = Red
```

#### Quick Method with SCP:
1. **SCP** → **Band calc**
2. Expression: `(b4-b3)/(b4+b3)`
3. Output will show vegetation health (-1 to +1)

### Step 6: Advanced Analysis Tools

#### Using QuickOSM for Context:
1. **Vector** → **QuickOSM** → **Quick Query**
2. Download reference data:
   - Key: `landuse` → Shows land use polygons
   - Key: `building` → Shows structures
   - Key: `highway` → Shows roads
3. Use as reference for classification validation

#### Change Detection (if you have multi-temporal SPOT):
1. Load two SPOT images from different dates
2. **SCP** → **Preprocessing** → **Land cover change**
3. Select classification rasters
4. Generate change detection report

### Step 7: Export Results

#### For Web Sharing (using qgis2web):
1. Style your classified image with meaningful colors
2. **Web** → **qgis2web** → **Create web map**
3. Choose Leaflet or OpenLayers
4. Include popups with class information

#### For Reports:
1. **Project** → **New Print Layout**
2. Add:
   - Map with SPOT imagery
   - Legend showing classes
   - Scale bar and north arrow
   - Statistics table

## 🎯 Specific SPOT Project Workflows

### A. Urban Growth Monitoring
```python
# In QGIS Python Console:
# Calculate built-up area change between two dates

# Load your classified images first, then:
from qgis.core import QgsRasterCalculator, QgsRasterCalculatorEntry

# Define entries for each raster
entries = []
# ... (setup raster calculator for change detection)
```

### B. Agricultural Monitoring
1. **Calculate NDVI time series**
2. **Identify crop types** using multi-temporal signatures
3. **Estimate yields** using vegetation indices

### C. Environmental Assessment
1. **Detect deforestation** 
2. **Monitor water bodies**
3. **Track urban sprawl**

## 📊 Quick Processing Chains

### For Toulouse Area Analysis:
1. **Load SPOT image** of Toulouse region
2. **Add OSM basemap**: Web → QuickMapServices → OSM → OSM Standard
3. **Download Toulouse data**: Vector → QuickOSM → Quick Query
   - In: "Toulouse, France"
   - Key: "building" or "landuse"
4. **Classify** using SCP with local training samples
5. **Validate** using OSM reference data

## 💡 Pro Tips for SPOT Processing

1. **Atmospheric Correction**: 
   - Use SCP's DOS1 (Dark Object Subtraction)
   - Raster → SCP → Preprocessing → DOS1

2. **Mosaic Multiple Scenes**:
   - Raster → Miscellaneous → Build Virtual Raster
   - Or: Raster → Miscellaneous → Merge

3. **Accuracy Assessment**:
   - Use SCP's accuracy tool
   - Create validation points
   - Generate confusion matrix

4. **Band Combinations**:
   - **Natural Color**: 3-2-1
   - **False Color (Vegetation)**: 4-3-2
   - **Urban**: 4-3-1

## 🔧 Troubleshooting

### If SPOT Files Won't Load:
1. Check CRS: should be UTM or Geographic
2. Try: Raster → Projections → Warp (Reproject)
3. Build pyramids: Right-click → Properties → Pyramids

### For Large Files:
1. Create overviews/pyramids
2. Use COG (Cloud Optimized GeoTIFF) format
3. Process in tiles if needed

## 📁 Project Organization
```
/SPOT_Project/
├── raw_data/          # Original SPOT files
├── processed/         # Pan-sharpened, corrected
├── classification/    # Classification results
├── indices/          # NDVI, other indices
├── validation/       # Accuracy assessment
├── exports/          # Final maps, web
└── documentation/    # Metadata, reports
```

## Next Steps:
1. **Load your SPOT data**
2. **Try basic visualization**
3. **Run a simple classification**
4. **Calculate NDVI**
5. **Export a web map**

Ready to start your SPOT analysis! 🚀
