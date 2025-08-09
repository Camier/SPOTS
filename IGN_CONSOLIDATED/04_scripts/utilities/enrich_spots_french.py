#!/usr/bin/env python3
"""Enrich existing spots with elevation and address data using French services"""

import sqlite3
import sys
from pathlib import Path
import time
import logging
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from backend.scrapers.geocoding_france import OccitanieGeocoder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class FrenchSpotEnricher(OccitanieGeocoder):
    """Enrich spots with French geocoding and elevation data"""
    
    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent / "data" / "occitanie_spots.db"
        self.stats = {
            'geocoded': 0,
            'elevated': 0,
            'addressed': 0,
            'errors': 0,
            'skipped': 0
        }
        
    def enrich_all_spots(self, batch_size=50):
        """Add elevation and address data to all spots"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get spots without elevation or address
        cursor.execute("""
            SELECT id, name, latitude, longitude, elevation, address, type
            FROM spots
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND (elevation IS NULL OR address IS NULL)
            ORDER BY id
        """)
        
        spots = cursor.fetchall()
        total = len(spots)
        logger.info(f"Found {total} spots to enrich with French geocoding data")
        
        for i, spot in enumerate(spots):
            spot_id = spot['id']
            lat = spot['latitude']
            lon = spot['longitude']
            spot_name = spot['name'] or f"Spot {spot_id}"
            
            updates = {}
            
            # Get elevation if missing
            if spot['elevation'] is None:
                elevation = self.get_elevation(lat, lon)
                if elevation is not None:
                    updates['elevation'] = elevation
                    self.stats['elevated'] += 1
                    logger.info(f"[{i+1}/{total}] Added elevation {elevation}m for {spot_name}")
                    
            # Get address if missing
            if spot['address'] is None:
                address = self.reverse_geocode(lat, lon)
                if address:
                    updates['address'] = address
                    self.stats['addressed'] += 1
                    
                    # Also get department code
                    dept_code = self.get_department_code(lat, lon)
                    if dept_code and dept_code in self.OCCITANIE_DEPARTMENTS:
                        updates['department'] = dept_code
                        logger.info(f"[{i+1}/{total}] Added address for {spot_name}: {address[:50]}... (Dept: {dept_code})")
                    else:
                        logger.warning(f"[{i+1}/{total}] Spot {spot_name} may not be in Occitanie")
                    
            # Update database
            if updates:
                try:
                    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                    values = list(updates.values()) + [spot_id]
                    
                    cursor.execute(
                        f"UPDATE spots SET {set_clause} WHERE id = ?",
                        values
                    )
                    
                    # Commit in batches
                    if (i + 1) % batch_size == 0:
                        conn.commit()
                        logger.info(f"Committed batch {(i + 1) // batch_size}")
                        
                except Exception as e:
                    logger.error(f"Error updating spot {spot_id}: {e}")
                    self.stats['errors'] += 1
            else:
                self.stats['skipped'] += 1
                
            # Progress update every 100 spots
            if (i + 1) % 100 == 0:
                self.show_progress(i + 1, total)
                
        # Final commit
        conn.commit()
        conn.close()
        
        self.show_final_stats(total)
        
    def show_progress(self, current: int, total: int):
        """Show enrichment progress"""
        percent = current / total * 100
        logger.info(f"\nProgress: {current}/{total} ({percent:.1f}%)")
        logger.info(f"  ✅ Elevated: {self.stats['elevated']}")
        logger.info(f"  📍 Addressed: {self.stats['addressed']}")
        logger.info(f"  ❌ Errors: {self.stats['errors']}")
        
    def show_final_stats(self, total: int):
        """Show final enrichment statistics"""
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ENRICHMENT COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Total spots processed: {total}")
        logger.info(f"✅ Elevation added: {self.stats['elevated']}")
        logger.info(f"📍 Addresses added: {self.stats['addressed']}")
        logger.info(f"⏭️ Skipped (already complete): {self.stats['skipped']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        
    def show_elevation_stats(self):
        """Show statistics about elevation data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total spots with coordinates
        cursor.execute("""
            SELECT COUNT(*) FROM spots 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)
        total_with_coords = cursor.fetchone()[0]
        
        # Spots with elevation
        cursor.execute("""
            SELECT COUNT(*) FROM spots 
            WHERE elevation IS NOT NULL
        """)
        with_elevation = cursor.fetchone()[0]
        
        # Spots with address
        cursor.execute("""
            SELECT COUNT(*) FROM spots 
            WHERE address IS NOT NULL
        """)
        with_address = cursor.fetchone()[0]
        
        # Elevation statistics
        cursor.execute("""
            SELECT 
                MIN(elevation) as min_elev,
                MAX(elevation) as max_elev,
                AVG(elevation) as avg_elev,
                COUNT(CASE WHEN elevation > 1000 THEN 1 END) as high_altitude,
                COUNT(CASE WHEN elevation > 2000 THEN 1 END) as very_high_altitude
            FROM spots
            WHERE elevation IS NOT NULL
        """)
        stats = cursor.fetchone()
        
        # Type statistics
        cursor.execute("""
            SELECT 
                type,
                COUNT(*) as count,
                AVG(elevation) as avg_elevation,
                MIN(elevation) as min_elevation,
                MAX(elevation) as max_elevation
            FROM spots
            WHERE elevation IS NOT NULL
            GROUP BY type
            ORDER BY avg_elevation DESC
        """)
        type_stats = cursor.fetchall()
        
        # Department statistics
        cursor.execute("""
            SELECT 
                department,
                COUNT(*) as count,
                AVG(elevation) as avg_elevation
            FROM spots
            WHERE department IS NOT NULL AND elevation IS NOT NULL
            GROUP BY department
            ORDER BY count DESC
        """)
        dept_stats = cursor.fetchall()
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("📊 FRENCH GEOCODING STATISTICS")
        print("=" * 60)
        print(f"Total spots with coordinates: {total_with_coords}")
        print(f"Spots with elevation data: {with_elevation} ({with_elevation/total_with_coords*100:.1f}%)")
        print(f"Spots with address data: {with_address} ({with_address/total_with_coords*100:.1f}%)")
        
        if stats[0] is not None:
            print(f"\n🏔️ Elevation range: {stats[0]:.0f}m - {stats[1]:.0f}m")
            print(f"Average elevation: {stats[2]:.0f}m")
            print(f"High altitude spots (>1000m): {stats[3]}")
            print(f"Very high altitude spots (>2000m): {stats[4]}")
        
        print("\n📊 Average elevation by type:")
        for spot_type, count, avg_elev, min_elev, max_elev in type_stats:
            if avg_elev:
                print(f"  {spot_type or 'Unknown'}: {avg_elev:.0f}m ({count} spots, range: {min_elev:.0f}-{max_elev:.0f}m)")
                
        print("\n🗺️ Spots by department:")
        for dept, count, avg_elev in dept_stats:
            dept_name = self.OCCITANIE_DEPARTMENTS.get(dept, dept)
            print(f"  {dept} - {dept_name}: {count} spots (avg: {avg_elev:.0f}m)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich spots with French geocoding data")
    parser.add_argument('--stats', action='store_true', help='Show geocoding statistics')
    parser.add_argument('--test', action='store_true', help='Test with first 10 spots only')
    
    args = parser.parse_args()
    
    enricher = FrenchSpotEnricher()
    
    if args.stats:
        enricher.show_elevation_stats()
    elif args.test:
        # Test mode - just process first 10 spots
        conn = sqlite3.connect(enricher.db_path)
        conn.execute("CREATE TEMP TABLE spots_backup AS SELECT * FROM spots")
        
        logger.info("TEST MODE: Processing first 10 spots only")
        enricher.enrich_all_spots(batch_size=10)
        
        # Show what would happen
        enricher.show_elevation_stats()
        
        # Restore original data
        conn.execute("DELETE FROM spots")
        conn.execute("INSERT INTO spots SELECT * FROM spots_backup")
        conn.commit()
        conn.close()
        
        logger.info("\nTEST MODE: Original data restored")
    else:
        logger.info("Starting French geocoding enrichment...")
        logger.info("Using free services:")
        logger.info("  - Base Adresse Nationale (BAN) for geocoding")
        logger.info("  - IGN altimetry service for elevation")
        logger.info("  - No API key required!")
        enricher.enrich_all_spots()