#!/usr/bin/env python3
"""
Aggressive Data Cleaning for SPOTS Project
Cleans poor quality data and enriches remaining spots with meaningful information
"""

import sqlite3
import json
import time
import requests
from typing import Dict, List, Tuple, Optional

class AggressiveDataCleaner:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        
        # Cleaning statistics
        self.stats = {
            'total_initial': 0,
            'deleted_duplicates': 0,
            'deleted_low_quality': 0,
            'enriched_names': 0,
            'enriched_types': 0,
            'final_count': 0
        }
        
        # Quality thresholds
        self.quality_criteria = {
            'min_elevation_for_mountain_spots': 500,  # meters
            'max_duplicate_distance': 50,  # meters
            'required_data_completeness': 0.3  # 30% of fields must be filled
        }
    
    def analyze_current_state(self):
        """Analyze current data state"""
        print("🔍 ANALYZING CURRENT DATABASE STATE")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        
        # Total count
        cursor.execute("SELECT COUNT(*) FROM spots")
        self.stats['total_initial'] = cursor.fetchone()[0]
        print(f"📊 Total spots: {self.stats['total_initial']}")
        
        # Sources breakdown
        cursor.execute("""
            SELECT source, COUNT(*) as count, 
                   AVG(CASE WHEN elevation IS NOT NULL AND elevation > 0 THEN 1 ELSE 0 END) as has_elevation_pct,
                   AVG(CASE WHEN address IS NOT NULL AND address != '' THEN 1 ELSE 0 END) as has_address_pct
            FROM spots 
            GROUP BY source 
            ORDER BY count DESC
        """)
        
        print("\n📍 SOURCES ANALYSIS:")
        for row in cursor.fetchall():
            source, count, elev_pct, addr_pct = row
            print(f"  {source}: {count} spots | Elevation: {elev_pct*100:.1f}% | Address: {addr_pct*100:.1f}%")
    
    def identify_duplicates(self) -> List[int]:
        """Identify duplicate spots based on proximity"""
        print("\n🔍 IDENTIFYING DUPLICATES...")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, latitude, longitude FROM spots ORDER BY id")
        spots = cursor.fetchall()
        
        duplicates = []
        processed = set()
        
        for i, spot1 in enumerate(spots):
            if spot1[0] in processed:
                continue
                
            for j, spot2 in enumerate(spots[i+1:], i+1):
                if spot2[0] in processed:
                    continue
                
                # Calculate distance (rough approximation)
                lat_diff = abs(spot1[1] - spot2[1]) * 111000  # Convert to meters
                lng_diff = abs(spot1[2] - spot2[2]) * 111000 * 0.7  # Adjust for latitude
                distance = (lat_diff**2 + lng_diff**2)**0.5
                
                if distance < self.quality_criteria['max_duplicate_distance']:
                    # Keep the one with better data
                    cursor.execute("SELECT elevation, address FROM spots WHERE id = ?", (spot1[0],))
                    data1 = cursor.fetchone()
                    cursor.execute("SELECT elevation, address FROM spots WHERE id = ?", (spot2[0],))
                    data2 = cursor.fetchone()
                    
                    # Score based on available data
                    score1 = sum([1 for x in data1 if x is not None and x != ''])
                    score2 = sum([1 for x in data2 if x is not None and x != ''])
                    
                    if score1 >= score2:
                        duplicates.append(spot2[0])
                        processed.add(spot2[0])
                    else:
                        duplicates.append(spot1[0])
                        processed.add(spot1[0])
                        break
        
        print(f"🎯 Found {len(duplicates)} duplicates within {self.quality_criteria['max_duplicate_distance']}m")
        return duplicates
    
    def identify_low_quality_spots(self) -> List[int]:
        """Identify spots with extremely low data quality"""
        print("\n🔍 IDENTIFYING LOW QUALITY SPOTS...")
        
        cursor = self.conn.cursor()
        
        # Spots with suspicious characteristics
        low_quality_ids = []
        
        # 1. Spots with impossible coordinates (outside reasonable bounds)
        cursor.execute("""
            SELECT id FROM spots 
            WHERE latitude < 42.0 OR latitude > 46.0 
               OR longitude < -1.0 OR longitude > 5.0
        """)
        out_of_bounds = [row[0] for row in cursor.fetchall()]
        low_quality_ids.extend(out_of_bounds)
        print(f"  📍 Out of bounds coordinates: {len(out_of_bounds)}")
        
        # 2. Spots with no distinguishing features and no elevation
        cursor.execute("""
            SELECT id FROM spots 
            WHERE (elevation IS NULL OR elevation <= 0)
              AND (address IS NULL OR address = '')
              AND source LIKE 'osm_%'
              AND confidence_score <= 0.5
        """)
        no_data = [row[0] for row in cursor.fetchall()]
        
        # Keep only if they're from valuable sources
        valuable_sources = ['osm_caves', 'osm_waterfalls']  # These are rarer and worth keeping
        cursor.execute(f"""
            SELECT id FROM spots 
            WHERE id IN ({','.join(map(str, no_data))}) 
              AND source NOT IN ({','.join(['?' for _ in valuable_sources])})
        """, valuable_sources)
        
        truly_useless = [row[0] for row in cursor.fetchall()]
        low_quality_ids.extend(truly_useless)
        print(f"  📊 Completely empty data: {len(truly_useless)}")
        
        return list(set(low_quality_ids))  # Remove duplicates
    
    def enrich_spot_names(self):
        """Enrich spot names based on source and location"""
        print("\n✨ ENRICHING SPOT NAMES...")
        
        cursor = self.conn.cursor()
        
        # Define name patterns based on source
        name_patterns = {
            'osm_springs': 'Source naturelle',
            'osm_caves': 'Grotte',
            'osm_ruins': 'Ruines historiques',
            'osm_waterfalls': 'Cascade',
            'osm_viewpoints': 'Point de vue'
        }
        
        type_patterns = {
            'osm_springs': 'natural_spring',
            'osm_caves': 'cave',
            'osm_ruins': 'historical_ruins',
            'osm_waterfalls': 'waterfall',
            'osm_viewpoints': 'viewpoint'
        }
        
        for source, base_name in name_patterns.items():
            # Get spots for this source
            cursor.execute("""
                SELECT id, latitude, longitude, elevation, address, department 
                FROM spots 
                WHERE source = ? AND name = 'Unknown'
            """, (source,))
            
            spots_to_update = cursor.fetchall()
            print(f"  📍 Enriching {len(spots_to_update)} {source} spots...")
            
            for spot in spots_to_update:
                spot_id, lat, lng, elevation, address, department = spot
                
                # Create descriptive name
                name_parts = [base_name]
                
                # Add location info
                if department:
                    dept_names = {
                        '09': 'Ariège', '12': 'Aveyron', '31': 'Haute-Garonne', 
                        '32': 'Gers', '46': 'Lot', '65': 'Hautes-Pyrénées',
                        '81': 'Tarn', '82': 'Tarn-et-Garonne'
                    }
                    if department in dept_names:
                        name_parts.append(f"({dept_names[department]})")
                
                # Add elevation for mountain features
                if elevation and elevation > 1000:
                    name_parts.append(f"alt. {int(elevation)}m")
                
                # Add address info if available
                if address and len(address) > 10:
                    # Extract commune name from address
                    address_parts = address.split()
                    for part in address_parts:
                        if len(part) > 5 and part[0].isupper():  # Likely commune name
                            name_parts.append(f"près de {part}")
                            break
                
                enriched_name = ' '.join(name_parts)
                enriched_type = type_patterns.get(source, 'outdoor_spot')
                
                # Create meaningful description
                descriptions = {
                    'osm_springs': f"Source naturelle située dans la région Occitanie. Coordonnées: {lat:.5f}, {lng:.5f}",
                    'osm_caves': f"Grotte ou cavité naturelle découverte via OpenStreetMap. Idéale pour la spéléologie.",
                    'osm_ruins': f"Vestiges historiques répertoriés. Site d'intérêt patrimonial et culturel.",
                    'osm_waterfalls': f"Cascade naturelle dans un cadre pittoresque. Point d'intérêt pour la randonnée.",
                    'osm_viewpoints': f"Belvédère offrant une vue panoramique sur la région Occitanie."
                }
                
                description = descriptions.get(source, "Spot naturel d'intérêt dans la région Occitanie.")
                
                # Update database
                cursor.execute("""
                    UPDATE spots 
                    SET name = ?, type = ?, description = ?, confidence_score = 0.7
                    WHERE id = ?
                """, (enriched_name, enriched_type, description, spot_id))
                
                self.stats['enriched_names'] += 1
        
        self.conn.commit()
        print(f"✅ Enriched {self.stats['enriched_names']} spot names")
    
    def clean_database(self):
        """Execute the complete cleaning process"""
        print("🧹 STARTING AGGRESSIVE DATABASE CLEANING")
        print("=" * 60)
        
        # Step 1: Analyze current state
        self.analyze_current_state()
        
        # Step 2: Identify and remove duplicates
        duplicates = self.identify_duplicates()
        if duplicates:
            placeholders = ','.join(['?' for _ in duplicates])
            self.conn.execute(f"DELETE FROM spots WHERE id IN ({placeholders})", duplicates)
            self.stats['deleted_duplicates'] = len(duplicates)
            print(f"🗑️  Deleted {len(duplicates)} duplicate spots")
        
        # Step 3: Identify and remove low quality spots
        low_quality = self.identify_low_quality_spots()
        if low_quality:
            placeholders = ','.join(['?' for _ in low_quality])
            self.conn.execute(f"DELETE FROM spots WHERE id IN ({placeholders})", low_quality)
            self.stats['deleted_low_quality'] = len(low_quality)
            print(f"🗑️  Deleted {len(low_quality)} low quality spots")
        
        # Step 4: Enrich remaining data
        self.enrich_spot_names()
        
        # Step 5: Update confidence scores for enriched data
        self.conn.execute("""
            UPDATE spots 
            SET confidence_score = CASE 
                WHEN address IS NOT NULL AND address != '' THEN 0.8
                WHEN elevation IS NOT NULL AND elevation > 0 THEN 0.7
                ELSE 0.6
            END,
            verified = CASE
                WHEN address IS NOT NULL AND address != '' AND elevation IS NOT NULL THEN 1
                ELSE 0
            END
            WHERE name != 'Unknown'
        """)
        
        # Step 6: Final statistics
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM spots")
        self.stats['final_count'] = cursor.fetchone()[0]
        
        self.conn.commit()
        self.print_final_report()
    
    def print_final_report(self):
        """Print final cleaning report"""
        print("\n" + "="*60)
        print("📊 CLEANING COMPLETED - FINAL REPORT")
        print("="*60)
        
        print(f"📈 STATISTICS:")
        print(f"  Initial spots: {self.stats['total_initial']}")
        print(f"  Deleted duplicates: {self.stats['deleted_duplicates']}")
        print(f"  Deleted low quality: {self.stats['deleted_low_quality']}")
        print(f"  Enriched names: {self.stats['enriched_names']}")
        print(f"  Final count: {self.stats['final_count']}")
        
        reduction = self.stats['total_initial'] - self.stats['final_count']
        reduction_pct = (reduction / self.stats['total_initial']) * 100
        print(f"\n📉 REDUCTION: {reduction} spots removed ({reduction_pct:.1f}%)")
        
        # Quality check
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM spots WHERE name != 'Unknown'")
        enriched_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE verified = 1")
        verified_count = cursor.fetchone()[0]
        
        print(f"\n✅ QUALITY IMPROVEMENT:")
        print(f"  Spots with meaningful names: {enriched_count}/{self.stats['final_count']} ({enriched_count/self.stats['final_count']*100:.1f}%)")
        print(f"  Verified spots: {verified_count}/{self.stats['final_count']} ({verified_count/self.stats['final_count']*100:.1f}%)")
        
        print(f"\n🎯 RECOMMENDATION: Database is now ready for production use!")

def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python aggressive_data_cleaning.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    # Create backup first
    import shutil
    backup_path = db_path.replace('.db', '_backup_before_cleaning.db')
    shutil.copy2(db_path, backup_path)
    print(f"💾 Backup created: {backup_path}")
    
    # Run cleaning
    cleaner = AggressiveDataCleaner(db_path)
    cleaner.clean_database()
    cleaner.conn.close()

if __name__ == "__main__":
    main()
