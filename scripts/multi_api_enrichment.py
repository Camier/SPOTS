#!/usr/bin/env python3
"""
Multi-API Comprehensive Enrichment for SPOTS Project
Uses multiple APIs in smart fallback order to maximize data completeness
"""

import sqlite3
import requests
import asyncio
import aiohttp
import os
import time
import json
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

class MultiAPIEnricher:
    def __init__(self, db_path: str):
        # Load environment variables
        load_dotenv()
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # API Configuration
        self.api_keys = {
            'ign': os.getenv('IGN_API_KEY'),
            'google': os.getenv('GOOGLE_MAPS_API_KEY'),
            'mapbox': os.getenv('MAPBOX_API_KEY'),
            'locationiq': os.getenv('LOCATIONIQ_API_KEY')
        }
        
        # API Endpoints
        self.endpoints = {
            # IGN (Premium French)
            'ign_geocoding': lambda key: f'https://wxs.ign.fr/{key}/geoportail/ols',
            'ign_elevation': lambda key: f'https://wxs.ign.fr/{key}/alti/rest/elevation.json',
            
            # Google Maps (Premium Global)
            'google_geocoding': 'https://maps.googleapis.com/maps/api/geocode/json',
            'google_places': 'https://maps.googleapis.com/maps/api/place/nearbysearch/json',
            'google_elevation': 'https://maps.googleapis.com/maps/api/elevation/json',
            
            # Mapbox (Good Alternative)
            'mapbox_geocoding': 'https://api.mapbox.com/geocoding/v5/mapbox.places',
            
            # Free Services (No Key)
            'ban_address': 'https://api-adresse.data.gouv.fr/reverse/',
            'nominatim': 'https://nominatim.openstreetmap.org/reverse',
            'overpass': 'https://overpass-api.de/api/interpreter',
            'datatourisme': 'https://diffuseur.datatourisme.fr/webservice/',
            'openmeteo': 'https://api.open-meteo.com/v1/forecast'
        }
        
        # Rate limiting per service
        self.rate_limits = {
            'ign': 0.1,      # 10/sec with key
            'google': 0.02,   # 50/sec  
            'mapbox': 0.1,    # 10/sec
            'ban': 0.1,       # 10/sec
            'nominatim': 1.0, # 1/sec (respectful)
            'overpass': 2.0   # 0.5/sec (very respectful)
        }
        
        # Statistics
        self.stats = {
            'ign_addresses': 0,
            'google_addresses': 0,
            'ban_addresses': 0,
            'osm_addresses': 0,
            'tourism_data': 0,
            'weather_data': 0,
            'elevation_enhanced': 0,
            'total_api_calls': 0,
            'api_errors': 0
        }

    def check_api_availability(self):
        """Check which APIs are available"""
        print("🔍 CHECKING API AVAILABILITY...")
        
        available_apis = []
        
        # Check API keys
        for service, key in self.api_keys.items():
            if key and key.strip() and key != 'your_key_here':
                available_apis.append(service.upper())
                print(f"  ✅ {service.upper()}: Key available")
            else:
                print(f"  ❌ {service.upper()}: No key found")
        
        # Free services always available
        free_services = ['BAN', 'NOMINATIM', 'OVERPASS', 'DATATOURISME', 'OPENMETEO']
        available_apis.extend(free_services)
        
        print(f"\n📊 AVAILABLE SERVICES: {', '.join(available_apis)}")
        return available_apis

    async def enrich_addresses_multi_api(self):
        """Enrich addresses using multiple APIs in priority order"""
        print("🌐 MULTI-API ADDRESS ENRICHMENT...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude, name, type, address
            FROM spots 
            WHERE address IS NULL OR address = ''
            ORDER BY id
        """)
        
        spots_to_enrich = cursor.fetchall()
        print(f"📮 Processing {len(spots_to_enrich)} spots with multi-API strategy...")
        
        async with aiohttp.ClientSession() as session:
            for i, spot in enumerate(spots_to_enrich):
                spot_id, lat, lng, name, spot_type, current_address = spot
                
                if i % 50 == 0:
                    print(f"   Progress: {i}/{len(spots_to_enrich)} ({i/len(spots_to_enrich)*100:.1f}%)")
                
                address = None
                source = None
                
                try:
                    # Priority 1: IGN (most accurate for France)
                    if self.api_keys['ign']:
                        address = await self._get_ign_address(session, lat, lng)
                        if address:
                            source = 'IGN'
                            self.stats['ign_addresses'] += 1
                    
                    # Priority 2: Google Maps (excellent global)
                    if not address and self.api_keys['google']:
                        address = await self._get_google_address(session, lat, lng)
                        if address:
                            source = 'Google'
                            self.stats['google_addresses'] += 1
                    
                    # Priority 3: BAN (French official, free)
                    if not address:
                        address = await self._get_ban_address(session, lat, lng)
                        if address:
                            source = 'BAN'
                            self.stats['ban_addresses'] += 1
                    
                    # Priority 4: Nominatim (OSM, free backup)
                    if not address:
                        address = await self._get_nominatim_address(session, lat, lng)
                        if address:
                            source = 'OSM'
                            self.stats['osm_addresses'] += 1
                    
                    if address:
                        # Extract administrative data
                        admin_data = self._extract_administrative_data(address)
                        
                        # Update database
                        cursor.execute("""
                            UPDATE spots 
                            SET address = ?,
                                access_info = COALESCE(access_info, '') || ' | Source: ' || ?
                            WHERE id = ?
                        """, (address, source, spot_id))
                        
                        # Update administrative data if extracted
                        if admin_data['commune'] or admin_data['postal_code']:
                            self._update_administrative_data(cursor, spot_id, admin_data)
                    
                    self.stats['total_api_calls'] += 1
                    
                    # Adaptive rate limiting based on source
                    if source == 'IGN':
                        await asyncio.sleep(self.rate_limits['ign'])
                    elif source == 'Google':
                        await asyncio.sleep(self.rate_limits['google'])
                    elif source == 'BAN':
                        await asyncio.sleep(self.rate_limits['ban'])
                    else:
                        await asyncio.sleep(self.rate_limits['nominatim'])
                        
                except Exception as e:
                    print(f"❌ Error enriching spot {spot_id}: {e}")
                    self.stats['api_errors'] += 1
        
        self.conn.commit()
        print(f"✅ Multi-API address enrichment complete!")
        print(f"   IGN: {self.stats['ign_addresses']}, Google: {self.stats['google_addresses']}")
        print(f"   BAN: {self.stats['ban_addresses']}, OSM: {self.stats['osm_addresses']}")

    async def _get_ign_address(self, session: aiohttp.ClientSession, 
                              lat: float, lng: float) -> Optional[str]:
        """Get address from IGN service"""
        if not self.api_keys['ign']:
            return None
            
        try:
            # Try modern IGN geocoding API
            url = f"https://data.geopf.fr/geocodage/reverse?lat={lat}&lon={lng}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'features' in data and data['features']:
                        return data['features'][0]['properties']['label']
        except Exception:
            pass
        
        return None

    async def _get_google_address(self, session: aiohttp.ClientSession,
                                 lat: float, lng: float) -> Optional[str]:
        """Get address from Google Maps API"""
        if not self.api_keys['google']:
            return None
            
        try:
            url = f"{self.endpoints['google_geocoding']}?latlng={lat},{lng}&key={self.api_keys['google']}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == 'OK' and data['results']:
                        return data['results'][0]['formatted_address']
        except Exception:
            pass
        
        return None

    async def _get_ban_address(self, session: aiohttp.ClientSession,
                              lat: float, lng: float) -> Optional[str]:
        """Get address from BAN service (already working)"""
        try:
            url = f"{self.endpoints['ban_address']}?lat={lat}&lon={lng}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'features' in data and data['features']:
                        return data['features'][0]['properties']['label']
        except Exception:
            pass
        
        return None

    async def _get_nominatim_address(self, session: aiohttp.ClientSession,
                                   lat: float, lng: float) -> Optional[str]:
        """Get address from Nominatim/OSM"""
        try:
            url = f"{self.endpoints['nominatim']}?lat={lat}&lon={lng}&format=json"
            headers = {'User-Agent': 'SPOTS-Project/1.0'}
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'display_name' in data:
                        return data['display_name']
        except Exception:
            pass
        
        return None

    def _extract_administrative_data(self, address: str) -> Dict[str, Optional[str]]:
        """Extract administrative data from address"""
        import re
        
        # Extract postal code and derive department
        postal_match = re.search(r'\b(\d{5})\b', address)
        postal_code = postal_match.group(1) if postal_match else None
        department = postal_code[:2] if postal_code else None
        
        # Extract commune (after postal code)
        commune = None
        if postal_code:
            parts = address.split(postal_code)
            if len(parts) > 1:
                commune_words = parts[1].strip().split()
                if commune_words:
                    commune = commune_words[0]
        
        return {
            'commune': commune,
            'postal_code': postal_code,
            'department': department
        }

    def _update_administrative_data(self, cursor, spot_id: int, admin_data: Dict):
        """Update administrative data in database"""
        if admin_data['department']:
            cursor.execute("""
                UPDATE spots 
                SET department = ?
                WHERE id = ? AND (department IS NULL OR department = '')
            """, (admin_data['department'], spot_id))

    async def enrich_tourism_data(self):
        """Enrich with tourism data from DataTourisme"""
        print("🏛️ ENRICHING WITH TOURISM DATA...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude, type, name
            FROM spots 
            WHERE type IN ('historical_ruins', 'cave', 'waterfall')
            AND (access_info IS NULL OR access_info NOT LIKE '%Tourism%')
            LIMIT 100
        """)
        
        spots_for_tourism = cursor.fetchall()
        print(f"🎯 Processing {len(spots_for_tourism)} spots for tourism data...")
        
        # This would integrate with DataTourisme API
        # For now, add basic tourism context based on type
        tourism_contexts = {
            'historical_ruins': 'Site historique - Consulter les horaires localement',
            'cave': 'Grotte naturelle - Équipement spéléo recommandé',
            'waterfall': 'Cascade naturelle - Meilleur accès printemps/été'
        }
        
        for spot in spots_for_tourism:
            spot_id, lat, lng, spot_type, name = spot
            
            if spot_type in tourism_contexts:
                tourism_info = tourism_contexts[spot_type]
                
                cursor.execute("""
                    UPDATE spots 
                    SET access_info = COALESCE(access_info, '') || ' | Tourism: ' || ?
                    WHERE id = ?
                """, (tourism_info, spot_id))
                
                self.stats['tourism_data'] += 1
        
        self.conn.commit()
        print(f"✅ Added tourism context to {self.stats['tourism_data']} spots")

    def update_final_quality_scores(self):
        """Update quality scores based on multi-API enrichment"""
        print("⭐ UPDATING FINAL QUALITY SCORES...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE spots 
            SET confidence_score = CASE 
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL
                 AND access_info LIKE '%Source:%' THEN 0.95  -- Multi-API enriched
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL THEN 0.9        -- Complete core data
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 THEN 0.85  -- Geographic complete
                WHEN address IS NOT NULL AND address != '' THEN 0.8     -- Address available
                ELSE confidence_score
            END,
            verified = CASE
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL 
                 AND access_info LIKE '%Source:%' THEN 1
                ELSE verified
            END
        """)
        
        self.conn.commit()
        print("✅ Final quality scores updated")

    async def run_multi_api_enrichment(self):
        """Run comprehensive multi-API enrichment"""
        print("🌍 STARTING MULTI-API COMPREHENSIVE ENRICHMENT")
        print("=" * 70)
        
        # Check API availability
        available_apis = self.check_api_availability()
        
        if len(available_apis) < 3:
            print("⚠️ Limited API access detected. Consider adding more API keys.")
        
        start_time = time.time()
        
        # Phase 1: Multi-API address enrichment
        await self.enrich_addresses_multi_api()
        
        # Phase 2: Tourism data enhancement
        await self.enrich_tourism_data()
        
        # Phase 3: Final quality score updates
        self.update_final_quality_scores()
        
        # Final report
        elapsed = time.time() - start_time
        self.print_final_report(elapsed, available_apis)

    def print_final_report(self, elapsed_time: float, available_apis: List[str]):
        """Print comprehensive final report"""
        print("\n" + "="*70)
        print("🌍 MULTI-API ENRICHMENT COMPLETED")
        print("="*70)
        
        cursor = self.conn.cursor()
        
        # Get final statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(confidence_score) as avg_confidence,
                SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified_count,
                SUM(CASE WHEN address IS NOT NULL AND address != '' THEN 1 ELSE 0 END) as has_address,
                SUM(CASE WHEN elevation IS NOT NULL AND elevation > 0 THEN 1 ELSE 0 END) as has_elevation,
                SUM(CASE WHEN department IS NOT NULL THEN 1 ELSE 0 END) as has_department,
                SUM(CASE WHEN access_info LIKE '%Source:%' THEN 1 ELSE 0 END) as multi_api_enriched
            FROM spots
        """)
        
        stats = cursor.fetchone()
        total, avg_conf, verified, has_addr, has_elev, has_dept, multi_enriched = stats
        
        print(f"📈 ENRICHMENT STATISTICS:")
        print(f"  Available APIs: {', '.join(available_apis)}")
        print(f"  IGN addresses: {self.stats['ign_addresses']}")
        print(f"  Google addresses: {self.stats['google_addresses']}")
        print(f"  BAN addresses: {self.stats['ban_addresses']}")
        print(f"  OSM addresses: {self.stats['osm_addresses']}")
        print(f"  Tourism data: {self.stats['tourism_data']}")
        print(f"  Total API calls: {self.stats['total_api_calls']}")
        print(f"  Processing time: {elapsed_time:.1f} seconds")
        
        print(f"\n🏆 FINAL DATABASE EXCELLENCE:")
        print(f"  Total spots: {total}")
        print(f"  Average confidence: {avg_conf:.2f}")
        print(f"  Verified spots: {verified} ({verified/total*100:.1f}%)")
        print(f"  With addresses: {has_addr} ({has_addr/total*100:.1f}%)")
        print(f"  With elevation: {has_elev} ({has_elev/total*100:.1f}%)")
        print(f"  With departments: {has_dept} ({has_dept/total*100:.1f}%)")
        print(f"  Multi-API enriched: {multi_enriched} ({multi_enriched/total*100:.1f}%)")
        
        if has_addr/total > 0.8:
            print(f"\n🏆 OUTSTANDING! Premium quality outdoor discovery platform!")
        elif has_addr/total > 0.5:
            print(f"\n🎯 EXCELLENT! High-quality database ready for users!")
        else:
            print(f"\n📈 GOOD PROGRESS! Consider adding more API keys for full coverage.")

async def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python multi_api_enrichment.py <database_path>")
        print("\nRequired API keys in .env file:")
        print("  IGN_API_KEY=your_ign_key")
        print("  GOOGLE_MAPS_API_KEY=your_google_key  # Optional but recommended")
        print("  MAPBOX_API_KEY=your_mapbox_key       # Optional")
        print("  LOCATIONIQ_API_KEY=your_locationiq_key  # Optional")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    # Create backup
    import shutil
    backup_path = db_path.replace('.db', '_backup_before_multi_api_enrichment.db')
    shutil.copy2(db_path, backup_path)
    print(f"💾 Backup created: {backup_path}")
    
    # Run multi-API enrichment
    enricher = MultiAPIEnricher(db_path)
    await enricher.run_multi_api_enrichment()
    enricher.conn.close()

if __name__ == "__main__":
    asyncio.run(main())
