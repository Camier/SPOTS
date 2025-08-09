#!/usr/bin/env python3
"""Merge IGN Exploration and SPOTS Enhanced workflows into unified system."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

class WorkflowMerger:
    """Consolidate multiple SPOTS/QGIS workflows into single unified system."""
    
    def __init__(self):
        self.project_dir = Path("/home/miko/Development/projects/spots")
        self.db_path = self.project_dir / "data" / "occitanie_spots.db"
        self.exports_dir = self.project_dir / "exports"
        self.stats = {
            "json_files_processed": 0,
            "spots_imported": 0,
            "duplicates_skipped": 0,
            "errors": 0
        }
    
    def connect_db(self):
        """Connect to SpatiaLite database."""
        conn = sqlite3.connect(str(self.db_path))
        conn.enable_load_extension(True)
        
        # Load SpatiaLite
        for path in ["/usr/lib/x86_64-linux-gnu/mod_spatialite.so", 
                     "/usr/local/lib/mod_spatialite.so",
                     "mod_spatialite"]:
            try:
                conn.load_extension(path)
                break
            except:
                continue
        
        return conn
    
    def import_json_spots(self, json_path):
        """Import spots from JSON file."""
        print(f"\n📍 Processing: {json_path.name}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conn = self.connect_db()
        cursor = conn.cursor()
        imported = 0
        
        # Handle different JSON structures
        if isinstance(data, list):
            spots = data
        elif 'spots' in data:
            spots = data['spots']
        elif 'features' in data:
            # GeoJSON format
            spots = []
            for feature in data['features']:
                spot = feature.get('properties', {})
                if 'geometry' in feature and feature['geometry'].get('type') == 'Point':
                    coords = feature['geometry']['coordinates']
                    spot['longitude'] = coords[0]
                    spot['latitude'] = coords[1]
                spots.append(spot)
        else:
            spots = []
        
        for spot in spots:
            try:
                # Extract common fields
                name = spot.get('name', spot.get('title', spot.get('location', 'Unknown')))
                lat = spot.get('latitude', spot.get('lat', spot.get('coordinates', {}).get('lat')))
                lon = spot.get('longitude', spot.get('lon', spot.get('coordinates', {}).get('lng')))
                
                if not lat or not lon:
                    continue
                
                # Extract optional fields
                spot_type = spot.get('type', spot.get('category', 'unknown'))
                description = spot.get('description', spot.get('content', ''))
                source = spot.get('source', json_path.stem)
                department = spot.get('department', '')
                
                # Try to infer department from coordinates if not provided
                if not department and lat and lon:
                    if 43.0 < lat < 44.0 and 1.0 < lon < 2.0:
                        department = "31"  # Haute-Garonne (Toulouse area)
                    elif 43.0 < lat < 44.0 and 3.0 < lon < 4.0:
                        department = "34"  # Hérault
                
                # Check for duplicates
                cursor.execute("""
                    SELECT COUNT(*) FROM spots 
                    WHERE name = ? AND ABS(latitude - ?) < 0.0001 AND ABS(longitude - ?) < 0.0001
                """, (name, lat, lon))
                
                if cursor.fetchone()[0] > 0:
                    self.stats["duplicates_skipped"] += 1
                    continue
                
                # Insert spot
                cursor.execute("""
                    INSERT INTO spots (
                        name, type, description, latitude, longitude,
                        department, source, created_at, verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, spot_type, description, lat, lon,
                    department, source, datetime.now().isoformat(), 0
                ))
                
                # Update geometry
                spot_id = cursor.lastrowid
                cursor.execute("""
                    UPDATE spots 
                    SET geometry = MakePoint(?, ?, 4326)
                    WHERE id = ?
                """, (lon, lat, spot_id))
                
                imported += 1
                print(f"  ✅ {name} ({lat:.4f}, {lon:.4f})")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                self.stats["errors"] += 1
        
        conn.commit()
        conn.close()
        
        self.stats["spots_imported"] += imported
        return imported
    
    def process_all_json_files(self):
        """Process all JSON files in exports directory."""
        json_files = list(self.exports_dir.glob("*.json"))
        
        print(f"\n🔍 Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            if "backup" not in json_file.name.lower():
                self.import_json_spots(json_file)
                self.stats["json_files_processed"] += 1
    
    def extract_qgis_layer_data(self):
        """Extract spots from current QGIS layers into database."""
        print("\n🗺️ Extracting data from QGIS layers...")
        
        try:
            from qgis.core import QgsProject, QgsFeature
            
            conn = self.connect_db()
            cursor = conn.cursor()
            extracted = 0
            
            # Get all vector layers
            for layer_id, layer in QgsProject.instance().mapLayers().items():
                if layer.type() == 0:  # Vector layer
                    layer_name = layer.name()
                    
                    # Process exploration layers
                    if any(keyword in layer_name for keyword in ["Urbex", "Cave", "Grotto"]):
                        print(f"\n  Processing layer: {layer_name}")
                        
                        for feature in layer.getFeatures():
                            attrs = feature.attributes()
                            geom = feature.geometry()
                            
                            if geom and not geom.isEmpty():
                                point = geom.asPoint()
                                
                                # Determine type from layer name
                                if "Urbex" in layer_name:
                                    spot_type = "urbex"
                                elif "Cave" in layer_name or "Grotto" in layer_name:
                                    spot_type = "cave"
                                else:
                                    spot_type = "unknown"
                                
                                # Extract name (usually first attribute)
                                name = str(attrs[0]) if attrs else f"{spot_type}_{extracted}"
                                
                                # Check for duplicate
                                cursor.execute("""
                                    SELECT COUNT(*) FROM spots 
                                    WHERE ABS(latitude - ?) < 0.0001 AND ABS(longitude - ?) < 0.0001
                                """, (point.y(), point.x()))
                                
                                if cursor.fetchone()[0] == 0:
                                    cursor.execute("""
                                        INSERT INTO spots (
                                            name, type, latitude, longitude,
                                            source, created_at, verified
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        name, spot_type, point.y(), point.x(),
                                        f"qgis_{layer_name}", datetime.now().isoformat(), 0
                                    ))
                                    
                                    # Update geometry
                                    spot_id = cursor.lastrowid
                                    cursor.execute("""
                                        UPDATE spots 
                                        SET geometry = MakePoint(?, ?, 4326)
                                        WHERE id = ?
                                    """, (point.x(), point.y(), spot_id))
                                    
                                    extracted += 1
            
            conn.commit()
            conn.close()
            
            print(f"\n  ✅ Extracted {extracted} spots from QGIS layers")
            self.stats["spots_imported"] += extracted
            
        except ImportError:
            print("  ⚠️ Not running in QGIS environment, skipping layer extraction")
    
    def create_unified_project(self):
        """Create unified QGIS project with all data."""
        print("\n🎯 Creating unified QGIS project...")
        
        project_path = self.project_dir / "QGIS_ENHANCED" / "spots_unified.qgz"
        
        # Create Python script for QGIS
        qgis_script = """
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
"""
        
        # Save script for manual execution in QGIS
        script_path = self.project_dir / "src" / "qgis_integration" / "create_unified_project.py"
        with open(script_path, 'w') as f:
            f.write(qgis_script)
        
        print(f"  📝 QGIS script saved to: {script_path}")
        print("  ℹ️ Run this script in QGIS Python Console to create unified project")
    
    def print_summary(self):
        """Print merge summary."""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM spots")
        total_spots = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE geometry IS NOT NULL")
        spots_with_geometry = cursor.fetchone()[0]
        
        cursor.execute("SELECT type, COUNT(*) FROM spots GROUP BY type")
        type_counts = cursor.fetchall()
        
        cursor.execute("SELECT department, COUNT(*) FROM spots WHERE department != '' GROUP BY department")
        dept_counts = cursor.fetchall()
        
        conn.close()
        
        print("\n" + "="*60)
        print("📊 WORKFLOW MERGE SUMMARY")
        print("="*60)
        print(f"\n📈 Processing Statistics:")
        print(f"  • JSON files processed: {self.stats['json_files_processed']}")
        print(f"  • Spots imported: {self.stats['spots_imported']}")
        print(f"  • Duplicates skipped: {self.stats['duplicates_skipped']}")
        print(f"  • Errors: {self.stats['errors']}")
        
        print(f"\n🗄️ Database Statistics:")
        print(f"  • Total spots: {total_spots}")
        print(f"  • Spots with geometry: {spots_with_geometry}")
        
        print(f"\n📍 Spots by Type:")
        for spot_type, count in type_counts:
            print(f"  • {spot_type}: {count}")
        
        if dept_counts:
            print(f"\n🏛️ Spots by Department:")
            for dept, count in dept_counts:
                print(f"  • Department {dept}: {count}")
        
        print("\n✅ Workflow merge complete!")
        print(f"📂 Unified database: {self.db_path}")
        print("\n🚀 Next steps:")
        print("  1. Open QGIS")
        print("  2. Run the create_unified_project.py script in Python Console")
        print("  3. Activate SPOTS plugin in Plugin Manager")

def main():
    """Main execution."""
    merger = WorkflowMerger()
    
    print("🔄 Starting SPOTS/QGIS Workflow Merger")
    print("="*60)
    
    # Process all JSON files
    merger.process_all_json_files()
    
    # Extract QGIS layer data if running in QGIS
    merger.extract_qgis_layer_data()
    
    # Create unified project
    merger.create_unified_project()
    
    # Print summary
    merger.print_summary()

if __name__ == "__main__":
    main()