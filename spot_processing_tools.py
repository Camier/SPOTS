"""
SPOT Image Processing Script for QGIS
Run this in QGIS Python Console to automate common SPOT tasks
"""

from qgis.core import *
from qgis.gui import *
import processing

# ============================================
# 1. LOAD SPOT MULTISPECTRAL IMAGE
# ============================================
def load_spot_image(file_path, band_names=['Blue', 'Green', 'Red', 'NIR']):
    """Load SPOT multispectral image"""
    
    # For single multiband file
    rlayer = QgsRasterLayer(file_path, "SPOT_Image")
    if rlayer.isValid():
        QgsProject.instance().addMapLayer(rlayer)
        print(f"✓ Loaded SPOT image: {rlayer.name()}")
        print(f"  Bands: {rlayer.bandCount()}")
        print(f"  CRS: {rlayer.crs().authid()}")
        return rlayer
    else:
        print("✗ Failed to load image")
        return None

# ============================================
# 2. CREATE RGB COMPOSITE
# ============================================
def set_rgb_rendering(layer, r_band=3, g_band=2, b_band=1):
    """Set natural color composite for SPOT"""
    layer.setRenderer(
        QgsMultiBandColorRenderer(
            layer.dataProvider(),
            r_band, g_band, b_band
        )
    )
    # Enhance contrast
    layer.renderer().setRedContrastEnhancement(
        QgsContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum)
    )
    layer.renderer().setGreenContrastEnhancement(
        QgsContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum)
    )
    layer.renderer().setBlueContrastEnhancement(
        QgsContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum)
    )
    layer.triggerRepaint()
    print(f"✓ Set RGB composite: R={r_band}, G={g_band}, B={b_band}")

# ============================================
# 3. CALCULATE NDVI
# ============================================
def calculate_ndvi(input_raster, output_path, nir_band=4, red_band=3):
    """Calculate NDVI from SPOT image"""
    
    entries = []
    # NIR band
    nir = QgsRasterCalculatorEntry()
    nir.raster = input_raster
    nir.bandNumber = nir_band
    nir.ref = 'NIR@1'
    entries.append(nir)
    
    # Red band
    red = QgsRasterCalculatorEntry()
    red.raster = input_raster
    red.bandNumber = red_band
    red.ref = 'Red@1'
    entries.append(red)
    
    # NDVI formula
    formula = '(NIR@1 - Red@1) / (NIR@1 + Red@1)'
    
    # Calculate
    calc = QgsRasterCalculator(
        formula,
        output_path,
        'GTiff',
        input_raster.extent(),
        input_raster.crs(),
        input_raster.width(),
        input_raster.height(),
        entries
    )
    
    result = calc.processCalculation()
    if result == 0:
        # Load result
        ndvi_layer = QgsRasterLayer(output_path, 'NDVI')
        QgsProject.instance().addMapLayer(ndvi_layer)
        
        # Apply color ramp
        apply_ndvi_style(ndvi_layer)
        print(f"✓ NDVI calculated: {output_path}")
        return ndvi_layer
    else:
        print(f"✗ NDVI calculation failed: {result}")
        return None

# ============================================
# 4. APPLY NDVI COLOR RAMP
# ============================================
def apply_ndvi_style(ndvi_layer):
    """Apply vegetation color ramp to NDVI"""
    # Create color ramp
    ramp = QgsGradientColorRamp.create({
        'color1': '#8B0000',  # Dark red for low NDVI
        'color2': '#00FF00',  # Green for high NDVI
        'stops': '0.2,255,255,0,255:0.5,255,255,255,255:0.7,0,255,0,255'
    })
    
    # Apply to layer
    renderer = QgsSingleBandPseudoColorRenderer(
        ndvi_layer.dataProvider(),
        1,
        QgsColorRampShader()
    )
    renderer.shader().setRasterShaderFunction(
        QgsColorRampShader(QgsColorRampShader.Interpolated)
    )
    renderer.shader().rasterShaderFunction().setColorRampType(
        QgsColorRampShader.Interpolated
    )
    renderer.shader().rasterShaderFunction().setColorRampItemList([
        QgsColorRampShader.ColorRampItem(-1, QColor(139, 0, 0), '<-0.2'),
        QgsColorRampShader.ColorRampItem(-0.2, QColor(255, 0, 0), '-0.2'),
        QgsColorRampShader.ColorRampItem(0, QColor(255, 255, 0), '0'),
        QgsColorRampShader.ColorRampItem(0.2, QColor(255, 255, 255), '0.2'),
        QgsColorRampShader.ColorRampItem(0.5, QColor(0, 255, 0), '0.5'),
        QgsColorRampShader.ColorRampItem(1, QColor(0, 139, 0), '>0.5')
    ])
    
    ndvi_layer.setRenderer(renderer)
    ndvi_layer.triggerRepaint()

# ============================================
# 5. QUICK STATISTICS
# ============================================
def get_band_statistics(layer, band_num=1):
    """Get statistics for a raster band"""
    provider = layer.dataProvider()
    stats = provider.bandStatistics(band_num, QgsRasterBandStats.All)
    
    print(f"\n📊 Band {band_num} Statistics:")
    print(f"  Min: {stats.minimumValue:.3f}")
    print(f"  Max: {stats.maximumValue:.3f}")
    print(f"  Mean: {stats.mean:.3f}")
    print(f"  StdDev: {stats.stdDev:.3f}")
    
    return stats

# ============================================
# 6. EXTRACT AOI FOR TOULOUSE
# ============================================
def clip_to_toulouse(input_layer, output_path):
    """Clip raster to Toulouse extent"""
    # Toulouse approximate extent (decimal degrees)
    toulouse_extent = QgsRectangle(1.35, 43.53, 1.53, 43.67)
    
    params = {
        'INPUT': input_layer,
        'PROJWIN': toulouse_extent,
        'OUTPUT': output_path
    }
    
    result = processing.run("gdal:cliprasterbyextent", params)
    
    if result['OUTPUT']:
        clipped = QgsRasterLayer(result['OUTPUT'], 'SPOT_Toulouse')
        QgsProject.instance().addMapLayer(clipped)
        print(f"✓ Clipped to Toulouse: {output_path}")
        return clipped
    return None

# ============================================
# 7. PAN-SHARPENING
# ============================================  
def pansharpen_spot(ms_path, pan_path, output_path):
    """Pan-sharpen SPOT multispectral with panchromatic"""
    params = {
        'SPECTRAL': ms_path,
        'PANCHROMATIC': pan_path,
        'OUTPUT': output_path,
        'RESAMPLING': 'cubic',
        'OPTIONS': ''
    }
    
    result = processing.run("gdal:pansharp", params)
    
    if result['OUTPUT']:
        pansharp = QgsRasterLayer(result['OUTPUT'], 'SPOT_Pansharpened')
        QgsProject.instance().addMapLayer(pansharp)
        print(f"✓ Pan-sharpened: {output_path}")
        return pansharp
    return None

# ============================================
# EXAMPLE WORKFLOW
# ============================================
"""
# Example usage:
# 1. Load your SPOT image
spot = load_spot_image('/path/to/your/SPOT_image.tif')

# 2. Set natural color display
if spot:
    set_rgb_rendering(spot, r_band=3, g_band=2, b_band=1)
    
# 3. Calculate NDVI
ndvi = calculate_ndvi(spot, '/path/to/output/ndvi.tif')

# 4. Get statistics
if ndvi:
    get_band_statistics(ndvi, 1)

# 5. Clip to Toulouse
toulouse_clip = clip_to_toulouse(spot, '/path/to/output/spot_toulouse.tif')

# 6. If you have pan band
# pansharp = pansharpen_spot('multispectral.tif', 'panchromatic.tif', 'pansharpened.tif')
"""

print("✓ SPOT processing functions loaded!")
print("  See example workflow at the bottom of the script")
