#!/usr/bin/env python3
"""
Load MBTiles in QGIS and create an offline project.
"""

from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsCoordinateReferenceSystem,
    QgsLayerTreeLayer
)
from qgis.utils import iface
import os

def load_offline_project():
    """Set up QGIS project with offline tiles and spots."""
    
    project = QgsProject.instance()
    project.clear()
    
    # Set project CRS to WGS84
    crs = QgsCoordinateReferenceSystem("EPSG:4326")
    project.setCrs(crs)
    
    # Base paths
    spots_dir = "/home/miko/Development/projects/spots"
    tiles_dir = os.path.join(spots_dir, "offline_tiles")
    
    # 1. Load MBTiles as raster layer
    mbtiles_path = os.path.join(tiles_dir, "osm.mbtiles")
    if os.path.exists(mbtiles_path):
        # MBTiles URI format for GDAL
        uri = f"type=mbtiles&url=file://{mbtiles_path}"
        mbtiles_layer = QgsRasterLayer(uri, "OSM Offline Tiles", "wms")
        
        if mbtiles_layer.isValid():
            project.addMapLayer(mbtiles_layer)
            print(f"✅ Loaded MBTiles: {mbtiles_path}")
        else:
            print(f"❌ Failed to load MBTiles: {mbtiles_path}")
            # Try alternative GDAL driver
            mbtiles_layer = QgsRasterLayer(mbtiles_path, "OSM Offline Tiles", "gdal")
            if mbtiles_layer.isValid():
                project.addMapLayer(mbtiles_layer)
                print(f"✅ Loaded MBTiles with GDAL driver")
    
    # 2. Load spots database
    spots_db = os.path.join(spots_dir, "data", "occitanie_spots.db")
    if os.path.exists(spots_db):
        # SpatiaLite connection string
        uri = f"dbname='{spots_db}' table='spots' (geometry) sql="
        spots_layer = QgsVectorLayer(uri, "SPOTS Occitanie", "spatialite")
        
        if spots_layer.isValid():
            project.addMapLayer(spots_layer)
            print(f"✅ Loaded spots: {spots_db}")
            
            # Style the spots layer
            from qgis.core import QgsSymbol, QgsSimpleMarkerSymbolLayer
            symbol = QgsSymbol.defaultSymbol(spots_layer.geometryType())
            symbol.setSize(8)
            symbol.setColor(QColor(255, 0, 0))
            spots_layer.renderer().setSymbol(symbol)
            spots_layer.triggerRepaint()
        else:
            print(f"❌ Failed to load spots: {spots_db}")
    
    # 3. Add OpenStreetMap online as fallback
    osm_url = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    osm_layer = QgsRasterLayer(osm_url, "OpenStreetMap (Online)", "wms")
    if osm_layer.isValid():
        project.addMapLayer(osm_layer)
        print("✅ Added OSM online fallback")
    
    # 4. Set map extent to Occitanie
    if iface:
        canvas = iface.mapCanvas()
        # Occitanie approximate extent
        extent = QgsRectangle(-0.5, 42.0, 4.5, 45.0)
        canvas.setExtent(extent)
        canvas.refresh()
        print("✅ Set view to Occitanie region")
    
    # 5. Save project
    project_file = os.path.join(spots_dir, "spots_offline.qgz")
    project.write(project_file)
    print(f"✅ Project saved: {project_file}")
    
    return project_file

# Execute when run in QGIS Python Console
if __name__ == "__console__":
    load_offline_project()