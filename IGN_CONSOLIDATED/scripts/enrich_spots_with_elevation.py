#!/usr/bin/env python3
"""Enrich existing spots with elevation data using Ola Maps API"""

import sqlite3
import os
import sys
from pathlib import Path
import time
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from backend.scrapers.geocoding_mixin import GeocodingMixin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class SpotEnricher(GeocodingMixin):
    """Enrich spots with elevation and address data"""
    
    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent / "data" / "occitanie_spots.db"
        
    def enrich_all_spots(self, batch_size=50):
        """Add elevation and address data to all spots"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get spots without elevation
        cursor.execute("""
            SELECT id, name, latitude, longitude, elevation, address
            FROM spots
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND (elevation IS NULL OR address IS NULL)
            ORDER BY id
        """)
        
        spots = cursor.fetchall()
        total = len(spots)
        logger.info(f"Found {total} spots to enrich")
        
        enriched = 0
        errors = 0
        
        for i, spot in enumerate(spots):
            spot_id = spot['id']
            lat = spot['latitude']
            lon = spot['longitude']
            
            updates = {}
            
            # Get elevation if missing
            if spot['elevation'] is None:
                elevation = self.get_elevation(lat, lon)
                if elevation is not None:
                    updates['elevation'] = elevation
                    logger.info(f"[{i+1}/{total}] Added elevation {elevation}m for spot {spot_id}: {spot['name']}")
                    
            # Get address if missing
            if spot['address'] is None:
                address = self.reverse_geocode(lat, lon)
                if address:
                    updates['address'] = address
                    logger.info(f"[{i+1}/{total}] Added address for spot {spot_id}: {address[:50]}...")
                    
            # Update database
            if updates:
                try:
                    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                    values = list(updates.values()) + [spot_id]
                    
                    cursor.execute(
                        f"UPDATE spots SET {set_clause} WHERE id = ?",
                        values
                    )
                    enriched += 1
                    
                    # Commit in batches
                    if enriched % batch_size == 0:
                        conn.commit()
                        logger.info(f"Committed {enriched} updates")
                        
                except Exception as e:
                    logger.error(f"Error updating spot {spot_id}: {e}")
                    errors += 1
                    
            # Rate limiting
            if self.ola_api_key:
                time.sleep(0.5)  # Be nice to the API
            else:
                break  # No API key, stop
                
        # Final commit
        conn.commit()
        conn.close()
        
        logger.info(f"\nEnrichment complete!")
        logger.info(f"✅ Enriched: {enriched} spots")
        logger.info(f"❌ Errors: {errors}")
        logger.info(f"⏭️ Skipped: {total - enriched - errors}")
        
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
        
        # Elevation statistics
        cursor.execute("""
            SELECT 
                MIN(elevation) as min_elev,
                MAX(elevation) as max_elev,
                AVG(elevation) as avg_elev,
                COUNT(CASE WHEN elevation > 1000 THEN 1 END) as high_altitude
            FROM spots
            WHERE elevation IS NOT NULL
        """)
        stats = cursor.fetchone()
        
        # Type statistics
        cursor.execute("""
            SELECT 
                type,
                COUNT(*) as count,
                AVG(elevation) as avg_elevation
            FROM spots
            WHERE elevation IS NOT NULL
            GROUP BY type
            ORDER BY avg_elevation DESC
        """)
        type_stats = cursor.fetchall()
        
        conn.close()
        
        print("\n📊 Elevation Statistics:")
        print(f"Total spots with coordinates: {total_with_coords}")
        print(f"Spots with elevation data: {with_elevation} ({with_elevation/total_with_coords*100:.1f}%)")
        print(f"\nElevation range: {stats[0]:.0f}m - {stats[1]:.0f}m")
        print(f"Average elevation: {stats[2]:.0f}m")
        print(f"High altitude spots (>1000m): {stats[3]}")
        
        print("\n🏔️ Average elevation by type:")
        for spot_type, count, avg_elev in type_stats:
            if avg_elev:
                print(f"  {spot_type or 'Unknown'}: {avg_elev:.0f}m ({count} spots)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich spots with elevation data")
    parser.add_argument('--stats', action='store_true', help='Show elevation statistics')
    parser.add_argument('--api-key', help='Ola Maps API key (or set OLA_MAPS_API_KEY env var)')
    
    args = parser.parse_args()
    
    if args.api_key:
        os.environ['OLA_MAPS_API_KEY'] = args.api_key
        
    enricher = SpotEnricher()
    
    if args.stats:
        enricher.show_elevation_stats()
    else:
        if not enricher.ola_api_key:
            print("⚠️ Warning: OLA_MAPS_API_KEY not set!")
            print("Set it with: export OLA_MAPS_API_KEY='your-key-here'")
            print("Or pass it with: --api-key YOUR_KEY")
            enricher.show_elevation_stats()
        else:
            enricher.enrich_all_spots()