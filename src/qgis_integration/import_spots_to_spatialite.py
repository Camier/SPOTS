#!/usr/bin/env python3
"""Import GeoJSON spots data into SpatiaLite database for QGIS integration."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

def import_geojson_to_spatialite(geojson_path, db_path):
    """Import spots from GeoJSON file into SpatiaLite database."""
    
    # Load GeoJSON data
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Connect to SpatiaLite database
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    
    # Try to load SpatiaLite extension
    try:
        conn.load_extension("mod_spatialite")
    except:
        # Try alternative paths
        for path in ["/usr/lib/x86_64-linux-gnu/mod_spatialite.so", 
                     "/usr/local/lib/mod_spatialite.so"]:
            try:
                conn.load_extension(path)
                break
            except:
                continue
    
    cursor = conn.cursor()
    
    # Initialize spatial metadata if needed
    cursor.execute("SELECT InitSpatialMetadata(1)")
    
    imported_count = 0
    
    # Process each feature
    for feature in data.get('features', []):
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        if geometry.get('type') == 'Point':
            coords = geometry.get('coordinates', [])
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
                
                # Extract properties
                name = properties.get('name', 'Unknown Spot')
                spot_type = properties.get('type', 'unknown')
                description = properties.get('description', '')
                source = properties.get('source', 'geojson_import')
                department = properties.get('department', '')
                commune = properties.get('commune', '')
                difficulty = properties.get('difficulty', 2)
                danger_level = properties.get('danger_level', 1)
                
                # Insert into spots table
                try:
                    cursor.execute("""
                        INSERT INTO spots (
                            name, type, description, latitude, longitude,
                            department, source, created_at, verified
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name, spot_type, description, lat, lon,
                        department, source, datetime.now().isoformat(), 0
                    ))
                    
                    # Update geometry column
                    spot_id = cursor.lastrowid
                    cursor.execute("""
                        UPDATE spots 
                        SET geometry = MakePoint(?, ?, 4326)
                        WHERE id = ?
                    """, (lon, lat, spot_id))
                    
                    imported_count += 1
                    print(f"Imported: {name} at ({lat}, {lon})")
                    
                except sqlite3.IntegrityError as e:
                    print(f"Skipped duplicate: {name} - {e}")
                except Exception as e:
                    print(f"Error importing {name}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Update spatial index
    cursor.execute("SELECT UpdateLayerStatistics('spots', 'geometry')")
    
    # Get final count
    cursor.execute("SELECT COUNT(*) FROM spots")
    total_spots = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n✅ Import complete!")
    print(f"Imported {imported_count} new spots")
    print(f"Total spots in database: {total_spots}")
    
    return imported_count

def main():
    """Main import function."""
    project_dir = Path("/home/miko/Development/projects/spots")
    db_path = project_dir / "data" / "occitanie_spots.db"
    
    # Import from available GeoJSON files
    geojson_files = [
        project_dir / "exports" / "instagram_spots_20250803_195033.geojson",
        project_dir / "exports" / "facebook_spots_20250803_213547.geojson"
    ]
    
    total_imported = 0
    
    for geojson_file in geojson_files:
        if geojson_file.exists():
            print(f"\n📍 Importing from: {geojson_file.name}")
            imported = import_geojson_to_spatialite(geojson_file, db_path)
            total_imported += imported
        else:
            print(f"⚠️ File not found: {geojson_file}")
    
    print(f"\n🎯 Total spots imported: {total_imported}")
    
    # Verify geometry column
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM spots WHERE geometry IS NOT NULL
    """)
    geo_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"📍 Spots with geometry: {geo_count}")

if __name__ == "__main__":
    main()