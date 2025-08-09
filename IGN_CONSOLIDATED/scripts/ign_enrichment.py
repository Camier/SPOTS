#!/usr/bin/env python3
"""
IGN-Powered Comprehensive Enrichment
Uses official IGN Geoservices APIs to enrich the SPOTS database
"""

import sqlite3
import requests
import asyncio
import aiohttp
import os
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

class IGNEnricher:
    def __init__(self, db_path: str):
        # Load environment variables
        load_dotenv()
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # IGN API configuration
        self.ign_api_key = os.getenv('IGN_API_KEY')
        if not self.ign_api_key:
            raise ValueError("IGN_API_KEY not found in environment variables!")
        
        # IGN service endpoints
        self.ign_endpoints = {
            'elevation': f'https://wxs.ign.fr/{self.ign_api_key}/alti/rest/elevation.json',
            'geocoding': f'https://wxs.ign.fr/{self.ign_api_key}/geoportail/ols',
            'reverse_geocoding': f'https://wxs.ign.fr/{self.ign_api_key}/geoportail/ols',
            'administrative': f'https://wxs.ign.fr/{self.ign_api_key}/geoportail/ols'
        }
        
        # Fallback free services
        self.fallback_endpoints = {
            'ban_geocoding': 'https://api-adresse.data.gouv.fr/reverse/',
            'ign_free_elevation': 'https://data.geopf.fr/altimetrie/1.0.0/calcul/alti/rest/elevation.json'
        }
        
        # Rate limiting (IGN allows higher rates with API key)
        self.rate_limit_delay = 0.1  # 10 requests per second
        
        # Statistics
        self.stats = {
            'enriched_addresses_ign': 0,
            'enriched_addresses_ban': 0,
            'enriched_elevation_ign': 0,
            'enriched_elevation_free': 0,
            'enriched_administrative': 0,
            'api_errors': 0,
            'total_api_calls': 0
        }

    async def enrich_addresses_with_ign(self):
        """Enrich addresses using IGN reverse geocoding API"""
        print("🏠 ENRICHING ADDRESSES WITH IGN GEOPORTAL...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude, name, type
            FROM spots 
            WHERE address IS NULL OR address = ''
            LIMIT 500
        """)
        
        spots_to_enrich = cursor.fetchall()
        print(f"📮 Processing {len(spots_to_enrich)} spots for IGN addresses...")
        
        async with aiohttp.ClientSession() as session:
            for spot in spots_to_enrich:
                spot_id, lat, lng, name, spot_type = spot
                
                try:
                    # IGN Reverse Geocoding
                    address = await self._get_ign_reverse_geocoding(session, lat, lng)
                    
                    if address:
                        cursor.execute(
                            "UPDATE spots SET address = ? WHERE id = ?",
                            (address, spot_id)
                        )
                        self.stats['enriched_addresses_ign'] += 1
                    else:
                        # Fallback to BAN if IGN fails
                        address = await self._get_ban_reverse_geocoding(session, lat, lng)
                        if address:
                            cursor.execute(
                                "UPDATE spots SET address = ? WHERE id = ?",
                                (address, spot_id)
                            )
                            self.stats['enriched_addresses_ban'] += 1
                    
                    self.stats['total_api_calls'] += 1
                    await asyncio.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    print(f"❌ Error enriching address for spot {spot_id}: {e}")
                    self.stats['api_errors'] += 1
        
        self.conn.commit()
        print(f"✅ Enriched addresses: IGN={self.stats['enriched_addresses_ign']}, BAN={self.stats['enriched_addresses_ban']}")

    async def _get_ign_reverse_geocoding(self, session: aiohttp.ClientSession, 
                                       lat: float, lng: float) -> Optional[str]:
        """Get address from IGN reverse geocoding service"""
        
        # IGN reverse geocoding XML request
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
        <XLS xmlns="http://www.opengis.net/xls" 
             xmlns:gml="http://www.opengis.net/gml" 
             version="1.2">
            <RequestHeader/>
            <Request requestID="1" version="1.2" methodName="ReverseGeocodeRequest">
                <ReverseGeocodeRequest>
                    <Position>
                        <gml:Point>
                            <gml:pos>{lat} {lng}</gml:pos>
                        </gml:Point>
                    </Position>
                    <ReverseGeocodePreference>StreetAddress</ReverseGeocodePreference>
                </ReverseGeocodeRequest>
            </Request>
        </XLS>"""
        
        try:
            async with session.post(
                self.ign_endpoints['reverse_geocoding'],
                data=xml_request,
                headers={'Content-Type': 'application/xml'}
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    # Parse XML response for address
                    # Simplified parsing - in production, use proper XML parser
                    if 'freeFormAddress' in content:
                        # Extract address from XML (simplified)
                        import re
                        match = re.search(r'<Address.*?freeFormAddress="([^"]+)"', content)
                        if match:
                            return match.group(1)
                    
        except Exception as e:
            print(f"IGN geocoding error: {e}")
        
        return None

    async def _get_ban_reverse_geocoding(self, session: aiohttp.ClientSession,
                                       lat: float, lng: float) -> Optional[str]:
        """Fallback to BAN (Base Adresse Nationale) for address"""
        
        try:
            url = f"{self.fallback_endpoints['ban_geocoding']}?lat={lat}&lon={lng}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'features' in data and data['features']:
                        feature = data['features'][0]
                        if 'properties' in feature and 'label' in feature['properties']:
                            return feature['properties']['label']
        except Exception as e:
            print(f"BAN geocoding error: {e}")
        
        return None

    async def enrich_elevation_with_ign(self):
        """Enrich elevation using IGN precise elevation service"""
        print("🏔️ ENRICHING ELEVATION WITH IGN PRECISION...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude
            FROM spots 
            WHERE elevation IS NULL OR elevation = 0
            LIMIT 200
        """)
        
        spots_to_enrich = cursor.fetchall()
        print(f"📏 Processing {len(spots_to_enrich)} spots for IGN elevation...")
        
        async with aiohttp.ClientSession() as session:
            for spot in spots_to_enrich:
                spot_id, lat, lng = spot
                
                try:
                    # Try IGN elevation service first
                    elevation = await self._get_ign_elevation(session, lat, lng)
                    
                    if elevation is None:
                        # Fallback to free IGN service
                        elevation = await self._get_free_ign_elevation(session, lat, lng)
                        if elevation is not None:
                            self.stats['enriched_elevation_free'] += 1
                    else:
                        self.stats['enriched_elevation_ign'] += 1
                    
                    if elevation is not None:
                        cursor.execute(
                            "UPDATE spots SET elevation = ? WHERE id = ?",
                            (round(elevation), spot_id)
                        )
                    
                    self.stats['total_api_calls'] += 1
                    await asyncio.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    print(f"❌ Error enriching elevation for spot {spot_id}: {e}")
                    self.stats['api_errors'] += 1
        
        self.conn.commit()
        print(f"✅ Enriched elevation: IGN={self.stats['enriched_elevation_ign']}, Free={self.stats['enriched_elevation_free']}")

    async def _get_ign_elevation(self, session: aiohttp.ClientSession,
                               lat: float, lng: float) -> Optional[float]:
        """Get elevation from IGN paid service"""
        
        try:
            url = f"{self.ign_endpoints['elevation']}?lat={lat}&lon={lng}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'elevations' in data and data['elevations']:
                        return data['elevations'][0]
        except Exception as e:
            print(f"IGN elevation error: {e}")
        
        return None

    async def _get_free_ign_elevation(self, session: aiohttp.ClientSession,
                                    lat: float, lng: float) -> Optional[float]:
        """Fallback to free IGN elevation service"""
        
        try:
            url = f"{self.fallback_endpoints['ign_free_elevation']}?lat={lat}&lon={lng}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'elevations' in data and data['elevations']:
                        return data['elevations'][0]
        except Exception as e:
            print(f"Free IGN elevation error: {e}")
        
        return None

    def enrich_administrative_data(self):
        """Enrich with French administrative data"""
        print("🏛️ ENRICHING ADMINISTRATIVE DATA...")
        
        cursor = self.conn.cursor()
        
        # Add commune and postal code information where addresses exist
        cursor.execute("""
            SELECT id, address, department, latitude, longitude
            FROM spots 
            WHERE address IS NOT NULL AND address != ''
        """)
        
        spots_with_addresses = cursor.fetchall()
        print(f"📋 Processing {len(spots_with_addresses)} spots for administrative data...")
        
        # Extract commune and postal codes from addresses
        for spot in spots_with_addresses:
            spot_id, address, department, lat, lng = spot
            
            # Extract postal code and commune from address
            commune, postal_code = self._extract_administrative_info(address)
            
            if commune or postal_code:
                # Update with administrative info
                cursor.execute("""
                    UPDATE spots 
                    SET access_info = COALESCE(access_info, '') || 
                        CASE 
                            WHEN ? IS NOT NULL THEN ' | Commune: ' || ?
                            ELSE ''
                        END ||
                        CASE 
                            WHEN ? IS NOT NULL THEN ' | Code postal: ' || ?
                            ELSE ''
                        END
                    WHERE id = ?
                """, (commune, commune, postal_code, postal_code, spot_id))
                
                self.stats['enriched_administrative'] += 1
        
        self.conn.commit()
        print(f"✅ Enriched administrative data for {self.stats['enriched_administrative']} spots")

    def _extract_administrative_info(self, address: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract commune and postal code from French address"""
        import re
        
        commune = None
        postal_code = None
        
        # French postal code pattern (5 digits)
        postal_match = re.search(r'\b(\d{5})\b', address)
        if postal_match:
            postal_code = postal_match.group(1)
        
        # Extract commune (usually last part after postal code)
        if postal_code:
            parts = address.split(postal_code)
            if len(parts) > 1:
                commune_part = parts[1].strip()
                # Take first word after postal code as commune
                commune_words = commune_part.split()
                if commune_words:
                    commune = commune_words[0]
        
        return commune, postal_code

    def update_quality_scores(self):
        """Update quality scores based on IGN enrichment"""
        print("⭐ UPDATING QUALITY SCORES...")
        
        cursor = self.conn.cursor()
        
        # Enhanced scoring with IGN data
        cursor.execute("""
            UPDATE spots 
            SET confidence_score = CASE 
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL
                 AND access_info LIKE '%Commune:%' THEN 0.95  -- Full IGN enrichment
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL THEN 0.9         -- Core data complete
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 THEN 0.8  -- Geographic complete
                WHEN address IS NOT NULL AND address != '' THEN 0.7    -- Address available
                WHEN elevation IS NOT NULL AND elevation > 0 THEN 0.6  -- Elevation available
                ELSE confidence_score
            END,
            verified = CASE
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL THEN 1
                ELSE 0
            END
        """)
        
        self.conn.commit()
        print("✅ Updated quality scores based on IGN enrichment")

    async def run_ign_enrichment(self):
        """Run complete IGN-powered enrichment"""
        print("🇫🇷 STARTING IGN GEOSERVICES ENRICHMENT")
        print("=" * 60)
        print(f"🔑 Using API Key: {self.ign_api_key[:20]}..." if len(self.ign_api_key) > 20 else f"🔑 Using API Key: {self.ign_api_key}")
        
        start_time = time.time()
        
        # Phase 1: Address enrichment
        await self.enrich_addresses_with_ign()
        
        # Phase 2: Elevation enrichment  
        await self.enrich_elevation_with_ign()
        
        # Phase 3: Administrative data
        self.enrich_administrative_data()
        
        # Phase 4: Quality score updates
        self.update_quality_scores()
        
        # Final report
        elapsed = time.time() - start_time
        self.print_final_report(elapsed)

    def print_final_report(self, elapsed_time: float):
        """Print comprehensive enrichment report"""
        print("\n" + "="*60)
        print("🇫🇷 IGN GEOSERVICES ENRICHMENT COMPLETED")
        print("="*60)
        
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
                SUM(CASE WHEN access_info LIKE '%Commune:%' THEN 1 ELSE 0 END) as has_commune
            FROM spots
        """)
        
        stats = cursor.fetchone()
        total, avg_conf, verified, has_addr, has_elev, has_dept, has_commune = stats
        
        print(f"📈 IGN ENRICHMENT STATISTICS:")
        print(f"  IGN addresses added: {self.stats['enriched_addresses_ign']}")
        print(f"  BAN addresses added: {self.stats['enriched_addresses_ban']}")
        print(f"  IGN elevations added: {self.stats['enriched_elevation_ign']}")
        print(f"  Free elevations added: {self.stats['enriched_elevation_free']}")
        print(f"  Administrative data: {self.stats['enriched_administrative']}")
        print(f"  Total API calls: {self.stats['total_api_calls']}")
        print(f"  API errors: {self.stats['api_errors']}")
        print(f"  Processing time: {elapsed_time:.1f} seconds")
        
        print(f"\n✅ FINAL DATABASE QUALITY:")
        print(f"  Total spots: {total}")
        print(f"  Average confidence: {avg_conf:.2f}")
        print(f"  Verified spots: {verified} ({verified/total*100:.1f}%)")
        print(f"  With addresses: {has_addr} ({has_addr/total*100:.1f}%)")
        print(f"  With elevation: {has_elev} ({has_elev/total*100:.1f}%)")
        print(f"  With departments: {has_dept} ({has_dept/total*100:.1f}%)")
        print(f"  With commune data: {has_commune} ({has_commune/total*100:.1f}%)")
        
        if has_addr/total > 0.5 and has_elev/total > 0.9:
            print(f"\n🏆 EXCELLENT ENRICHMENT ACHIEVED!")
            print(f"    Your SPOTS database is now premium quality!")
        else:
            print(f"\n🎯 GOOD PROGRESS - READY FOR ADDITIONAL ENRICHMENT")

async def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python ign_enrichment.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create .env file with IGN_API_KEY=your_api_key")
        sys.exit(1)
    
    # Create backup
    import shutil
    backup_path = db_path.replace('.db', '_backup_before_ign_enrichment.db')
    shutil.copy2(db_path, backup_path)
    print(f"💾 Backup created: {backup_path}")
    
    try:
        # Run IGN enrichment
        enricher = IGNEnricher(db_path)
        await enricher.run_ign_enrichment()
        enricher.conn.close()
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please add your IGN API key to the .env file:")
        print("IGN_API_KEY=your_key_here")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Enrichment error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
