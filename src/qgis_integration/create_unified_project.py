
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer

# Clear existing project
QgsProject.instance().clear()

# Set project CRS to WGS84
QgsProject.instance().setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

# Add basemaps
osm_layer = QgsRasterLayer(
    "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "OpenStreetMap", "wms"
)
QgsProject.instance().addMapLayer(osm_layer)

# Add SpatiaLite database layer
db_path = "/home/miko/Development/projects/spots/data/occitanie_spots.db"
uri = f"dbname='{db_path}' table='spots' (geometry) sql="
spots_layer = QgsVectorLayer(uri, "SPOTS Unified Database", "spatialite")

if spots_layer.isValid():
    QgsProject.instance().addMapLayer(spots_layer)
    print(f"✅ Loaded {spots_layer.featureCount()} spots")
else:
    print("❌ Failed to load SpatiaLite layer")

# Save project
QgsProject.instance().write("/home/miko/Development/projects/spots/QGIS_ENHANCED/spots_unified.qgz")
print("✅ Project saved")
