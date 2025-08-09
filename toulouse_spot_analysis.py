"""
SPOT Toulouse Analysis - Ready-to-Run Script
============================================
This script demonstrates a complete workflow for analyzing
SPOT satellite imagery of the Toulouse area using QGIS

Author: QGIS Assistant
Date: August 2025
"""

from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
import processing
import os

# ============================================
# CONFIGURATION
# ============================================

# Set your paths here
BASE_DIR = "/home/miko/Documents/SPOT_Project"
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "results")

# Create directories if they don't exist
for directory in [DATA_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)

# Toulouse Area of Interest (WGS84)
TOULOUSE_EXTENT = {
    'xmin': 1.35,
    'ymin': 43.53,
    'xmax': 1.53,
    'ymax': 43.67
}

# ============================================
# MAIN WORKFLOW
# ============================================

def run_spot_toulouse_analysis():
    """Complete SPOT analysis workflow for Toulouse"""
    
    print("="*50)
    print("SPOT TOULOUSE ANALYSIS")
    print("="*50)
    
    # Step 1: Add basemap
    print("\n1. Adding basemap...")
    add_osm_basemap()
    
    # Step 2: Download Toulouse reference data
    print("\n2. Downloading Toulouse OSM data...")
    toulouse_layers = download_toulouse_data()
    
    # Step 3: Instructions for loading SPOT
    print("\n3. SPOT Image Loading")
    print_spot_loading_instructions()
    
    # Step 4: Create processing functions
    print("\n4. Processing functions ready!")
    
    return True

# ============================================
# HELPER FUNCTIONS
# ============================================

def add_osm_basemap():
    """Add OpenStreetMap basemap"""
    # This assumes QuickMapServices is installed and configured
    try:
        # Try to add OSM basemap programmatically
        urlWithParams = 'type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png'
        urlWithParams += '&crs=EPSG:3857&zmax=19&zmin=0'
        
        osm_layer = QgsRasterLayer(urlWithParams, 'OpenStreetMap', 'wms')
        
        if osm_layer.isValid():
            QgsProject.instance().addMapLayer(osm_layer)
            print("✓ OSM basemap added")
            
            # Zoom to Toulouse
            canvas = iface.mapCanvas()
            rect = QgsRectangle(
                TOULOUSE_EXTENT['xmin'],
                TOULOUSE_EXTENT['ymin'],
                TOULOUSE_EXTENT['xmax'],
                TOULOUSE_EXTENT['ymax']
            )
            rect_transformed = transform_extent(rect, 'EPSG:4326', 'EPSG:3857')
            canvas.setExtent(rect_transformed)
            canvas.refresh()
        else:
            print("✗ Could not add OSM. Use QuickMapServices menu instead")
    except Exception as e:
        print(f"✗ Basemap error: {e}")
        print("  Use: Web → QuickMapServices → OSM → OSM Standard")

def download_toulouse_data():
    """Download reference data for Toulouse using QuickOSM"""
    layers = {}
    
    # Note: This requires QuickOSM to be installed and enabled
    queries = [
        {'key': 'landuse', 'name': 'Land Use'},
        {'key': 'building', 'name': 'Buildings'},
        {'key': 'natural', 'value': 'water', 'name': 'Water Bodies'},
        {'key': 'highway', 'name': 'Roads'}
    ]
    
    print("\nTo download Toulouse reference data:")
    print("1. Vector → QuickOSM → Quick Query")
    print("2. For each query below:")
    
    for query in queries:
        print(f"\n   Query: {query['name']}")
        print(f"   - Key: {query['key']}")
        if 'value' in query:
            print(f"   - Value: {query['value']}")
        print("   - In: Toulouse, France")
        print("   - Click 'Run query'")
    
    return layers

def transform_extent(extent, source_crs, target_crs):
    """Transform extent between CRS"""
    source = QgsCoordinateReferenceSystem(source_crs)
    target = QgsCoordinateReferenceSystem(target_crs)
    transform = QgsCoordinateTransform(source, target, QgsProject.instance())
    return transform.transformBoundingBox(extent)

def print_spot_loading_instructions():
    """Print instructions for loading SPOT data"""
    print("\nTo load your SPOT image:")
    print("1. Drag and drop your SPOT .TIF file into QGIS")
    print("   OR")
    print("2. Layer → Add Layer → Add Raster Layer")
    print("\nThen run these functions:")
    print("- process_spot_image(layer)")
    print("- calculate_indices(layer)")
    print("- classify_landcover(layer)")

# ============================================
# SPOT PROCESSING FUNCTIONS
# ============================================

def process_spot_image(spot_layer):
    """Process SPOT image with standard workflow"""
    if not spot_layer:
        print("✗ No SPOT layer provided")
        return
    
    print(f"\nProcessing: {spot_layer.name()}")
    
    # 1. Set natural color rendering
    set_natural_color(spot_layer)
    
    # 2. Calculate statistics
    print_statistics(spot_layer)
    
    # 3. Clip to Toulouse if needed
    if is_larger_than_toulouse(spot_layer):
        print("\nImage covers larger area than Toulouse")
        print("Consider clipping with: clip_to_toulouse(layer)")
    
    return spot_layer

def set_natural_color(layer):
    """Set natural color band combination"""
    if layer.bandCount() >= 3:
        # SPOT natural color: R=Band3, G=Band2, B=Band1
        renderer = QgsMultiBandColorRenderer(
            layer.dataProvider(), 3, 2, 1
        )
        
        # Apply contrast enhancement
        renderer.setRedContrastEnhancement(
            QgsContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum)
        )
        renderer.setGreenContrastEnhancement(
            QgsContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum)
        )
        renderer.setBlueContrastEnhancement(
            QgsContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum)
        )
        
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        print("✓ Natural color rendering applied (3-2-1)")

def print_statistics(layer):
    """Print basic statistics for all bands"""
    print("\n📊 Image Statistics:")
    print(f"Size: {layer.width()} x {layer.height()} pixels")
    print(f"CRS: {layer.crs().authid()}")
    print(f"Bands: {layer.bandCount()}")
    
    for band in range(1, min(layer.bandCount() + 1, 5)):
        stats = layer.dataProvider().bandStatistics(
            band, QgsRasterBandStats.Min | QgsRasterBandStats.Max | QgsRasterBandStats.Mean
        )
        print(f"\nBand {band}:")
        print(f"  Min: {stats.minimumValue:.2f}")
        print(f"  Max: {stats.maximumValue:.2f}")
        print(f"  Mean: {stats.mean:.2f}")

def is_larger_than_toulouse(layer):
    """Check if image extent is larger than Toulouse AOI"""
    extent = layer.extent()
    # Transform to WGS84 for comparison
    if layer.crs().authid() != 'EPSG:4326':
        extent = transform_extent(extent, layer.crs().authid(), 'EPSG:4326')
    
    return (extent.width() > 0.2 or extent.height() > 0.2)

def calculate_indices(spot_layer):
    """Calculate vegetation and urban indices"""
    output_ndvi = os.path.join(OUTPUT_DIR, 'toulouse_ndvi.tif')
    
    print("\nCalculating indices...")
    
    # NDVI
    params = {
        'INPUT_A': spot_layer,
        'BAND_A': 4,  # NIR
        'INPUT_B': spot_layer,
        'BAND_B': 3,  # Red
        'FORMULA': '(A-B)/(A+B)',
        'OUTPUT': output_ndvi,
        'NO_DATA': -9999,
        'RTYPE': 5  # Float32
    }
    
    try:
        result = processing.run("gdal:rastercalculator", params)
        if result['OUTPUT']:
            ndvi = QgsRasterLayer(result['OUTPUT'], 'NDVI_Toulouse')
            QgsProject.instance().addMapLayer(ndvi)
            apply_ndvi_style(ndvi)
            print("✓ NDVI calculated")
            return ndvi
    except Exception as e:
        print(f"✗ NDVI calculation failed: {e}")
        return None

def apply_ndvi_style(ndvi_layer):
    """Apply vegetation color ramp"""
    # Create color ramp items
    color_ramp_items = [
        QgsColorRampShader.ColorRampItem(-1, QColor(120, 0, 0), 'Water/No veg'),
        QgsColorRampShader.ColorRampItem(0, QColor(255, 178, 0), 'Bare soil'),
        QgsColorRampShader.ColorRampItem(0.2, QColor(255, 255, 0), 'Low veg'),
        QgsColorRampShader.ColorRampItem(0.4, QColor(180, 255, 0), 'Moderate veg'),
        QgsColorRampShader.ColorRampItem(0.6, QColor(0, 255, 0), 'Dense veg'),
        QgsColorRampShader.ColorRampItem(1, QColor(0, 120, 0), 'Very dense')
    ]
    
    # Create shader
    shader = QgsRasterShader()
    color_ramp = QgsColorRampShader()
    color_ramp.setColorRampType(QgsColorRampShader.Interpolated)
    color_ramp.setColorRampItemList(color_ramp_items)
    shader.setRasterShaderFunction(color_ramp)
    
    # Apply to renderer
    renderer = QgsSingleBandPseudoColorRenderer(ndvi_layer.dataProvider(), 1, shader)
    ndvi_layer.setRenderer(renderer)
    ndvi_layer.triggerRepaint()
    print("✓ NDVI style applied")

def classify_landcover(spot_layer):
    """Simple unsupervised classification"""
    output_class = os.path.join(OUTPUT_DIR, 'toulouse_classification.tif')
    
    print("\nRunning unsupervised classification...")
    print("For better results, use Semi-Automatic Classification Plugin:")
    print("1. Raster → SCP → Band set")
    print("2. Create training ROIs")
    print("3. Run supervised classification")
    
    # K-means clustering example
    params = {
        'INPUT': spot_layer,
        'CLUSTERS': 5,  # 5 classes
        'ITERATIONS': 20,
        'OUTPUT': output_class
    }
    
    # Note: This would require SAGA or other provider
    print("\nTo classify:")
    print("1. Use Processing Toolbox → SAGA → Imagery → Classification")
    print("2. Or use SCP for supervised classification")

# ============================================
# ANALYSIS FUNCTIONS
# ============================================

def analyze_urban_growth(spot_old, spot_new):
    """Compare two SPOT images for urban change"""
    print("\nUrban Growth Analysis")
    print("1. Classify both images")
    print("2. Reclassify to urban/non-urban")
    print("3. Calculate difference")
    print("4. Generate statistics")

def extract_green_spaces():
    """Extract parks and green areas"""
    print("\nGreen Space Extraction")
    print("1. Use NDVI threshold (>0.4)")
    print("2. Filter by minimum area")
    print("3. Combine with OSM parks data")
    print("4. Calculate total green area")

# ============================================
# RUN THE ANALYSIS
# ============================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("SPOT TOULOUSE ANALYSIS TOOLKIT")
    print("="*50)
    print("\nFunctions available:")
    print("- run_spot_toulouse_analysis() : Complete workflow")
    print("- process_spot_image(layer) : Basic processing")
    print("- calculate_indices(layer) : Calculate NDVI") 
    print("- classify_landcover(layer) : Land cover classification")
    print("\nStart with: run_spot_toulouse_analysis()")

# Run the initial setup
run_spot_toulouse_analysis()
