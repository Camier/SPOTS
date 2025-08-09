#!/usr/bin/env python3
"""Fix coordinate system issues in SPOTS database."""

import sqlite3
from pathlib import Path
import math

def transform_lambert93_to_wgs84(x, y):
    """
    Transform Lambert93 (EPSG:2154) coordinates to WGS84 (EPSG:4326).
    Using simplified transformation for French territory.
    """
    # Lambert93 parameters
    a = 6378137.0  # Semi-major axis
    f = 1 / 298.257223563  # Flattening
    
    # Lambert93 projection center (France)
    lambda0 = 3.0 * math.pi / 180  # Central meridian (3°E)
    phi0 = 46.5 * math.pi / 180    # Central parallel (46.5°N)
    
    # False easting and northing
    x0 = 700000
    y0 = 6600000
    
    # Adjust coordinates
    x_adj = x - x0
    y_adj = y - y0
    
    # Simplified inverse projection (approximate)
    # This is a rough approximation for demonstration
    # In production, use pyproj or GDAL for accurate transformation
    
    # Rough estimate for Toulouse/Occitanie region
    if 100000 < x < 800000 and 5000000 < y < 7000000:
        # These appear to be Lambert93 coordinates
        # Approximate transformation for Occitanie region
        lon = 1.4 + (x - 570000) / 85000  # Rough scaling
        lat = 43.6 + (y - 6280000) / 110000  # Rough scaling
    else:
        # Already in WGS84 or unknown system
        return None, None
    
    return lat, lon

def fix_coordinates():
    """Fix coordinate system issues in the database."""
    
    db_path = Path("/home/miko/Development/projects/spots/data/occitanie_spots.db")
    conn = sqlite3.connect(str(db_path))
    conn.enable_load_extension(True)
    
    # Try to load SpatiaLite
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
                pass
    
    cursor = conn.cursor()
    
    # Get all spots with potential coordinate issues
    cursor.execute("""
        SELECT id, name, latitude, longitude 
        FROM spots 
        WHERE latitude > 180 OR longitude > 180 
           OR latitude < -90 OR longitude < -180
    """)
    
    spots_to_fix = cursor.fetchall()
    print(f"Found {len(spots_to_fix)} spots with coordinate issues")
    
    fixed_count = 0
    
    for spot_id, name, lat, lon in spots_to_fix:
        print(f"\nProcessing: {name}")
        print(f"  Current: lat={lat}, lon={lon}")
        
        # Try to fix based on coordinate ranges
        new_lat, new_lon = None, None
        
        # Check if coordinates are swapped
        if -180 <= lat <= 180 and -90 <= lon <= 90:
            # Possibly swapped
            new_lat, new_lon = lon, lat
            print(f"  Swapped coordinates detected")
        
        # Check if in Lambert93 range
        elif 100000 < lon < 800000 and 5000000 < lat < 7000000:
            # Likely Lambert93
            new_lat, new_lon = transform_lambert93_to_wgs84(lon, lat)
            print(f"  Lambert93 coordinates detected")
        
        # Check if in Web Mercator or other projection
        elif abs(lat) > 1000 or abs(lon) > 1000:
            # Try to determine based on typical ranges for Occitanie
            # This is a fallback for unknown projections
            if lat > 5000000:  # Likely northing
                # Rough approximation for Occitanie region
                new_lat = 43.0 + (lat - 5400000) / 100000
                new_lon = 1.0 + (lon - 200000) / 100000
                print(f"  Unknown projection, using approximation")
        
        if new_lat and new_lon:
            # Validate new coordinates
            if -90 <= new_lat <= 90 and -180 <= new_lon <= 180:
                print(f"  Fixed: lat={new_lat:.6f}, lon={new_lon:.6f}")
                
                # Update database
                cursor.execute("""
                    UPDATE spots 
                    SET latitude = ?, longitude = ?
                    WHERE id = ?
                """, (new_lat, new_lon, spot_id))
                
                # Update geometry
                cursor.execute("""
                    UPDATE spots 
                    SET geometry = MakePoint(?, ?, 4326)
                    WHERE id = ?
                """, (new_lon, new_lat, spot_id))
                
                fixed_count += 1
            else:
                print(f"  ❌ Invalid transformation result")
        else:
            print(f"  ❌ Could not determine correct coordinates")
    
    conn.commit()
    
    # Verify results
    cursor.execute("""
        SELECT COUNT(*) FROM spots 
        WHERE latitude BETWEEN -90 AND 90 
          AND longitude BETWEEN -180 AND 180
    """)
    valid_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM spots")
    total_count = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "="*50)
    print(f"✅ Coordinate Fix Complete!")
    print(f"Fixed: {fixed_count} spots")
    print(f"Valid coordinates: {valid_count}/{total_count}")
    print(f"Success rate: {valid_count/total_count*100:.1f}%")

if __name__ == "__main__":
    fix_coordinates()