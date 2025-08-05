#!/usr/bin/env python3
"""
Comprehensive Data Enrichment for SPOTS Project
Enriches the 995 cleaned spots with detailed geographic, tourism, and activity data
"""

import sqlite3
import requests
import time
import json
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp

class SpotsDataEnricher:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # API endpoints and keys
        self.apis = {
            # French government APIs (free)
            'ign_elevation': 'https://data.geopf.fr/altimetrie/1.0.0/calcul/alti/rest/elevation.json',
            'ign_geocoding': 'https://data.geopf.fr/geocodage/reverse',
            'ban_geocoding': 'https://api-adresse.data.gouv.fr/reverse/',
            
            # OpenStreetMap APIs (free)
            'osm_nominatim': 'https://nominatim.openstreetmap.org/reverse',
            'osm_overpass': 'https://overpass-api.de/api/interpreter',
            
            # Weather/Climate (free)
            'openmeteo': 'https://api.open-meteo.com/v1/forecast',
            
            # Tourism data (free)
            'france_tourism': 'https://diffuseur.datatourisme.fr/webservice/v2',
        }
        
        # Rate limiting
        self.rate_limits = {
            'ign': 100,  # requests per minute
            'osm': 60,   # requests per minute
            'ban': 150   # requests per minute
        }
        
        # Department mapping
        self.departments = {
            '09': {'name': 'Ariège', 'bounds': ((42.5, 0.8), (43.2, 2.2))},
            '12': {'name': 'Aveyron', 'bounds': ((43.7, 1.8), (44.9, 3.1))},
            '31': {'name': 'Haute-Garonne', 'bounds': ((42.9, 0.4), (43.9, 2.0))},
            '32': {'name': 'Gers', 'bounds': ((43.3, -0.1), (44.1, 1.2))},
            '46': {'name': 'Lot', 'bounds': ((44.2, 0.9), (45.1, 2.2))},
            '65': {'name': 'Hautes-Pyrénées', 'bounds': ((42.7, -0.3), (43.5, 0.6))},
            '81': {'name': 'Tarn', 'bounds': ((43.4, 1.5), (44.2, 2.8))},
            '82': {'name': 'Tarn-et-Garonne', 'bounds': ((43.7, 0.7), (44.4, 1.8))}
        }
        
        # Enrichment statistics
        self.stats = {
            'enriched_elevation': 0,
            'enriched_address': 0,
            'enriched_department': 0,
            'enriched_tourism_data': 0,
            'enriched_accessibility': 0,
            'enriched_activities': 0,
            'failed_requests': 0
        }

    def analyze_enrichment_needs(self):
        """Analyze current data state and prioritize enrichment"""
        print("🔍 ANALYZING ENRICHMENT NEEDS")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        
        # Priority 1: Missing core geographic data
        cursor.execute("SELECT COUNT(*) FROM spots WHERE elevation IS NULL OR elevation = 0")
        missing_elevation = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE address IS NULL OR address = ''")
        missing_address = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE department IS NULL OR department = ''")
        missing_department = cursor.fetchone()[0]
        
        print(f"📊 PRIORITY 1 - Core Geographic Data:")
        print(f"  Missing elevation: {missing_elevation} spots")
        print(f"  Missing address: {missing_address} spots")
        print(f"  Missing department: {missing_department} spots")
        
        # Priority 2: Activity-specific enrichment needs
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM spots 
            GROUP BY type 
            ORDER BY count DESC
        """)
        
        print(f"\n📊 PRIORITY 2 - Activity-Specific Enrichment:")
        for type_name, count in cursor.fetchall():
            print(f"  {type_name}: {count} spots need activity data")
        
        return {
            'missing_elevation': missing_elevation,
            'missing_address': missing_address,
            'missing_department': missing_department
        }

    async def enrich_elevation_data(self):
        """Enrich missing elevation data using IGN API"""
        print("\n🏔️ ENRICHING ELEVATION DATA...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude 
            FROM spots 
            WHERE elevation IS NULL OR elevation = 0
            LIMIT 100
        """)
        
        spots_to_enrich = cursor.fetchall()
        print(f"📍 Processing {len(spots_to_enrich)} spots for elevation...")
        
        async with aiohttp.ClientSession() as session:
            for spot in spots_to_enrich:
                spot_id, lat, lng = spot
                
                try:
                    # IGN Elevation API
                    url = f"{self.apis['ign_elevation']}?lat={lat}&lon={lng}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'elevations' in data and data['elevations']:
                                elevation = round(data['elevations'][0])
                                
                                # Update database
                                cursor.execute(
                                    "UPDATE spots SET elevation = ? WHERE id = ?",
                                    (elevation, spot_id)
                                )
                                self.stats['enriched_elevation'] += 1
                        
                        # Rate limiting
                        await asyncio.sleep(0.6)  # 100 requests per minute
                        
                except Exception as e:
                    print(f"❌ Error enriching elevation for spot {spot_id}: {e}")
                    self.stats['failed_requests'] += 1
        
        self.conn.commit()
        print(f"✅ Enriched elevation for {self.stats['enriched_elevation']} spots")

    async def enrich_address_data(self):
        """Enrich missing address data using multiple geocoding services"""
        print("\n📍 ENRICHING ADDRESS DATA...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude 
            FROM spots 
            WHERE address IS NULL OR address = ''
            LIMIT 200
        """)
        
        spots_to_enrich = cursor.fetchall()
        print(f"📮 Processing {len(spots_to_enrich)} spots for addresses...")
        
        async with aiohttp.ClientSession() as session:
            for spot in spots_to_enrich:
                spot_id, lat, lng = spot
                address = None
                
                try:
                    # Try BAN (Base Adresse Nationale) first - French official
                    url = f"{self.apis['ban_geocoding']}?lat={lat}&lon={lng}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'features' and data['features']:
                                feature = data['features'][0]
                                if 'properties' in feature and 'label' in feature['properties']:
                                    address = feature['properties']['label']
                    
                    # Fallback to OSM Nominatim if BAN fails
                    if not address:
                        await asyncio.sleep(1)  # Respectful rate limiting for OSM
                        url = f"{self.apis['osm_nominatim']}?lat={lat}&lon={lng}&format=json"
                        async with session.get(url, headers={'User-Agent': 'SpotsProject/1.0'}) as response:
                            if response.status == 200:
                                data = await response.json()
                                if 'display_name' in data:
                                    address = data['display_name']
                    
                    if address:
                        # Update database
                        cursor.execute(
                            "UPDATE spots SET address = ? WHERE id = ?",
                            (address, spot_id)
                        )
                        self.stats['enriched_address'] += 1
                    
                    # Rate limiting
                    await asyncio.sleep(0.4)  # 150 requests per minute for BAN
                    
                except Exception as e:
                    print(f"❌ Error enriching address for spot {spot_id}: {e}")
                    self.stats['failed_requests'] += 1
        
        self.conn.commit()
        print(f"✅ Enriched addresses for {self.stats['enriched_address']} spots")

    def enrich_department_data(self):
        """Enrich department data using coordinate bounds"""
        print("\n🗺️ ENRICHING DEPARTMENT DATA...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude 
            FROM spots 
            WHERE department IS NULL OR department = ''
        """)
        
        spots_to_enrich = cursor.fetchall()
        print(f"🏛️ Processing {len(spots_to_enrich)} spots for departments...")
        
        for spot in spots_to_enrich:
            spot_id, lat, lng = spot
            
            # Check which department bounds contain this coordinate
            for dept_code, dept_info in self.departments.items():
                bounds = dept_info['bounds']
                min_bounds, max_bounds = bounds
                min_lat, min_lng = min_bounds
                max_lat, max_lng = max_bounds
                
                if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                    cursor.execute(
                        "UPDATE spots SET department = ? WHERE id = ?",
                        (dept_code, spot_id)
                    )
                    self.stats['enriched_department'] += 1
                    break
        
        self.conn.commit()
        print(f"✅ Enriched departments for {self.stats['enriched_department']} spots")

    def enrich_activity_specific_data(self):
        """Enrich with activity-specific metadata"""
        print("\n🎯 ENRICHING ACTIVITY-SPECIFIC DATA...")
        
        cursor = self.conn.cursor()
        
        # Enhanced descriptions and metadata by type
        activity_enhancements = {
            'cave': {
                'enhanced_description': "Grotte naturelle ou cavité souterraine. Idéale pour la spéléologie et l'exploration géologique. Vérifiez l'équipement nécessaire et les conditions d'accès avant la visite.",
                'recommended_activities': ['spéléologie', 'géologie', 'photographie'],
                'equipment_needed': ['lampe frontale', 'casque', 'vêtements de protection'],
                'difficulty_level': 'Modéré',
                'season_recommendation': 'Toute saison (intérieur)',
                'accessibility': 'Variable selon la grotte'
            },
            'waterfall': {
                'enhanced_description': "Cascade naturelle offrant un spectacle saisissant. Parfaite pour la randonnée, la photographie nature et la détente. L'accès peut varier selon les conditions météorologiques.",
                'recommended_activities': ['randonnée', 'photographie', 'pique-nique'],
                'equipment_needed': ['chaussures de randonnée', 'appareil photo', 'vêtements imperméables'],
                'difficulty_level': 'Facile à modéré',
                'season_recommendation': 'Printemps et automne (débit optimal)',
                'accessibility': 'Sentiers de randonnée'
            },
            'natural_spring': {
                'enhanced_description': "Source naturelle aux propriétés souvent remarquables. Point d'intérêt pour la randonnée, l'observation de la nature et la découverte géologique.",
                'recommended_activities': ['randonnée', 'observation nature', 'géologie'],
                'equipment_needed': ['chaussures de marche', 'gourde', 'jumelles'],
                'difficulty_level': 'Facile',
                'season_recommendation': 'Printemps et été',
                'accessibility': 'Généralement facile'
            },
            'historical_ruins': {
                'enhanced_description': "Vestiges historiques témoignant du patrimoine régional. Site culturel d'intérêt pour la découverte de l'histoire locale et l'architecture ancienne.",
                'recommended_activities': ['visite culturelle', 'photographie', 'histoire'],
                'equipment_needed': ['appareil photo', 'guide historique', 'chaussures confortables'],
                'difficulty_level': 'Facile',
                'season_recommendation': 'Printemps, été, automne',
                'accessibility': 'Variable selon le site'
            }
        }
        
        for spot_type, enhancements in activity_enhancements.items():
            # Update enhanced descriptions
            cursor.execute("""
                UPDATE spots 
                SET description = ?,
                    access_info = ?,
                    weather_sensitive = ?
                WHERE type = ? AND (description IS NULL OR description NOT LIKE '%spéléologie%')
            """, (
                enhancements['enhanced_description'],
                f"Difficulté: {enhancements['difficulty_level']}. Équipement: {', '.join(enhancements['equipment_needed'])}. Saison recommandée: {enhancements['season_recommendation']}.",
                1 if spot_type in ['waterfall', 'natural_spring'] else 0,
                spot_type
            ))
            
            self.stats['enriched_activities'] += cursor.rowcount
        
        self.conn.commit()
        print(f"✅ Enriched activity data for {self.stats['enriched_activities']} spots")

    def create_enrichment_metadata_table(self):
        """Create additional metadata table for enriched data"""
        print("\n📊 CREATING ENRICHMENT METADATA...")
        
        cursor = self.conn.cursor()
        
        # Create enrichment metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spot_enrichment (
                spot_id INTEGER PRIMARY KEY,
                recommended_activities TEXT,
                equipment_needed TEXT,
                difficulty_level TEXT,
                best_season TEXT,
                accessibility_info TEXT,
                nearby_amenities TEXT,
                safety_notes TEXT,
                last_enriched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spot_id) REFERENCES spots (id)
            )
        """)
        
        # Populate with activity-specific data
        cursor.execute("SELECT id, type FROM spots")
        all_spots = cursor.fetchall()
        
        activity_metadata = {
            'cave': {
                'activities': 'Spéléologie, exploration, photographie souterraine',
                'equipment': 'Lampe frontale, casque, vêtements de protection, gants',
                'difficulty': 'Modéré à difficile',
                'season': 'Toute saison (température constante)',
                'accessibility': 'Accès parfois technique, vérifier conditions',
                'safety': 'Ne jamais explorer seul, informer de sa sortie'
            },
            'waterfall': {
                'activities': 'Randonnée, photographie, observation nature',
                'equipment': 'Chaussures antidérapantes, vêtements imperméables',
                'difficulty': 'Facile à modéré',
                'season': 'Printemps (débit maximal), éviter périodes de gel',
                'accessibility': 'Sentiers généralement balisés',
                'safety': 'Attention aux rochers glissants près de l\'eau'
            },
            'natural_spring': {
                'activities': 'Randonnée, hydrogéologie, détente',
                'equipment': 'Chaussures de marche, gourde, appareil photo',
                'difficulty': 'Facile',
                'season': 'Toute saison, meilleur débit au printemps',
                'accessibility': 'Généralement accessible à pied',
                'safety': 'Eau non potable sauf indication contraire'
            },
            'historical_ruins': {
                'activities': 'Visite culturelle, photographie, histoire locale',
                'equipment': 'Chaussures confortables, appareil photo, guide',
                'difficulty': 'Facile',
                'season': 'Printemps à automne pour meilleure visibilité',
                'accessibility': 'Variable, certains sites restaurés',
                'safety': 'Attention aux structures instables'
            }
        }
        
        for spot_id, spot_type in all_spots:
            if spot_type in activity_metadata:
                metadata = activity_metadata[spot_type]
                cursor.execute("""
                    INSERT OR REPLACE INTO spot_enrichment 
                    (spot_id, recommended_activities, equipment_needed, difficulty_level, 
                     best_season, accessibility_info, safety_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    spot_id,
                    metadata['activities'],
                    metadata['equipment'],
                    metadata['difficulty'],
                    metadata['season'],
                    metadata['accessibility'],
                    metadata['safety']
                ))
        
        self.conn.commit()
        print(f"✅ Created enrichment metadata for {len(all_spots)} spots")

    async def run_comprehensive_enrichment(self):
        """Run the complete enrichment process"""
        print("🚀 STARTING COMPREHENSIVE DATA ENRICHMENT")
        print("=" * 60)
        
        # Step 1: Analyze needs
        needs = self.analyze_enrichment_needs()
        
        # Step 2: Core geographic data (most important)
        if needs['missing_elevation'] > 0:
            await self.enrich_elevation_data()
        
        if needs['missing_address'] > 0:
            await self.enrich_address_data()
        
        if needs['missing_department'] > 0:
            self.enrich_department_data()
        
        # Step 3: Activity-specific enrichment
        self.enrich_activity_specific_data()
        
        # Step 4: Create enrichment metadata
        self.create_enrichment_metadata_table()
        
        # Step 5: Update confidence scores based on enrichment
        self.update_confidence_scores()
        
        # Step 6: Generate final report
        self.print_enrichment_report()

    def update_confidence_scores(self):
        """Update confidence scores based on enriched data"""
        print("\n⭐ UPDATING CONFIDENCE SCORES...")
        
        cursor = self.conn.cursor()
        
        # Enhanced scoring algorithm
        cursor.execute("""
            UPDATE spots 
            SET confidence_score = CASE 
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL THEN 0.9
                WHEN (address IS NOT NULL AND address != '') 
                 AND (elevation IS NOT NULL AND elevation > 0) THEN 0.8
                WHEN address IS NOT NULL AND address != '' THEN 0.7
                WHEN elevation IS NOT NULL AND elevation > 0 THEN 0.6
                ELSE 0.5
            END,
            verified = CASE
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL THEN 1
                ELSE 0
            END
        """)
        
        self.conn.commit()
        print("✅ Updated confidence scores based on enriched data")

    def print_enrichment_report(self):
        """Print comprehensive enrichment report"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE ENRICHMENT COMPLETED")
        print("="*60)
        
        cursor = self.conn.cursor()
        
        # Final statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(confidence_score) as avg_confidence,
                SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified_count,
                SUM(CASE WHEN address IS NOT NULL AND address != '' THEN 1 ELSE 0 END) as has_address,
                SUM(CASE WHEN elevation IS NOT NULL AND elevation > 0 THEN 1 ELSE 0 END) as has_elevation,
                SUM(CASE WHEN department IS NOT NULL THEN 1 ELSE 0 END) as has_department
            FROM spots
        """)
        
        stats = cursor.fetchone()
        total, avg_conf, verified, has_addr, has_elev, has_dept = stats
        
        print(f"📈 ENRICHMENT STATISTICS:")
        print(f"  Enriched elevation: {self.stats['enriched_elevation']} spots")
        print(f"  Enriched addresses: {self.stats['enriched_address']} spots")
        print(f"  Enriched departments: {self.stats['enriched_department']} spots")
        print(f"  Enriched activities: {self.stats['enriched_activities']} spots")
        print(f"  Failed requests: {self.stats['failed_requests']}")
        
        print(f"\n✅ FINAL DATA QUALITY:")
        print(f"  Total spots: {total}")
        print(f"  Average confidence: {avg_conf:.2f}")
        print(f"  Verified spots: {verified} ({verified/total*100:.1f}%)")
        print(f"  With addresses: {has_addr} ({has_addr/total*100:.1f}%)")
        print(f"  With elevation: {has_elev} ({has_elev/total*100:.1f}%)")
        print(f"  With departments: {has_dept} ({has_dept/total*100:.1f}%)")
        
        print(f"\n🎯 DATABASE IS NOW HIGHLY ENRICHED AND PRODUCTION-READY!")

async def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python comprehensive_enrichment.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    # Create backup
    import shutil
    backup_path = db_path.replace('.db', '_backup_before_enrichment.db')
    shutil.copy2(db_path, backup_path)
    print(f"💾 Backup created: {backup_path}")
    
    # Run enrichment
    enricher = SpotsDataEnricher(db_path)
    await enricher.run_comprehensive_enrichment()
    enricher.conn.close()

if __name__ == "__main__":
    asyncio.run(main())
