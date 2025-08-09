#!/usr/bin/env python3
"""
Quick Nominatim Enrichment - Fill Missing Addresses Now!
Uses OpenStreetMap's free Nominatim service to get addresses for remaining spots
"""

import sqlite3
import requests
import time
import asyncio
import aiohttp

class NominatimEnricher:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        self.nominatim_url = 'https://nominatim.openstreetmap.org/reverse'
        self.rate_limit = 1.0  # 1 second between requests (respectful)
        
        self.stats = {
            'processed': 0,
            'found_addresses': 0,
            'errors': 0
        }

    async def enrich_with_nominatim(self):
        """Enrich missing addresses using Nominatim"""
        print("🗺️ NOMINATIM (OSM) ADDRESS ENRICHMENT")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude, name, type
            FROM spots 
            WHERE address IS NULL OR address = ''
            ORDER BY id
        """)
        
        missing_spots = cursor.fetchall()
        total_spots = len(missing_spots)
        estimated_time = total_spots * self.rate_limit / 60
        
        print(f"📍 Processing {total_spots} spots (estimated time: {estimated_time:.1f} minutes)")
        print("🐌 Using respectful 1-second delays for OSM service...")
        
        async with aiohttp.ClientSession() as session:
            for i, spot in enumerate(missing_spots):
                spot_id, lat, lng, name, spot_type = spot
                
                if i % 25 == 0:
                    progress = i / total_spots * 100
                    print(f"   Progress: {i}/{total_spots} ({progress:.1f}%) - Found: {self.stats['found_addresses']}")
                
                try:
                    address = await self._get_nominatim_address(session, lat, lng)
                    
                    if address:
                        # Clean and format the address
                        cleaned_address = self._clean_nominatim_address(address)
                        
                        # Update database
                        cursor.execute("""
                            UPDATE spots 
                            SET address = ?,
                                access_info = COALESCE(access_info, '') || ' | Source: OSM'
                            WHERE id = ?
                        """, (cleaned_address, spot_id))
                        
                        self.stats['found_addresses'] += 1
                        
                        # Extract department if possible
                        department = self._extract_department_from_address(cleaned_address)
                        if department:
                            cursor.execute("""
                                UPDATE spots 
                                SET department = ?
                                WHERE id = ? AND (department IS NULL OR department = '')
                            """, (department, spot_id))
                    
                    self.stats['processed'] += 1
                    
                    # Respectful rate limiting
                    await asyncio.sleep(self.rate_limit)
                    
                except Exception as e:
                    print(f"❌ Error processing spot {spot_id}: {e}")
                    self.stats['errors'] += 1
                    await asyncio.sleep(self.rate_limit)  # Still wait on error
        
        self.conn.commit()
        print(f"\\n✅ Nominatim enrichment complete!")
        print(f"   Processed: {self.stats['processed']}")
        print(f"   Found addresses: {self.stats['found_addresses']}")
        print(f"   Success rate: {self.stats['found_addresses']/self.stats['processed']*100:.1f}%")

    async def _get_nominatim_address(self, session: aiohttp.ClientSession, 
                                   lat: float, lng: float) -> str:
        """Get address from Nominatim service"""
        try:
            url = f"{self.nominatim_url}?lat={lat}&lon={lng}&format=json&addressdetails=1"
            headers = {'User-Agent': 'SPOTS-Project/1.0 (educational)'}
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'display_name' in data:
                        return data['display_name']
                elif response.status == 429:  # Rate limited
                    print("⚠️ Rate limited, waiting longer...")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            pass
        
        return None

    def _clean_nominatim_address(self, address: str) -> str:
        """Clean and format Nominatim address"""
        # Remove excessive detail for cleaner addresses
        parts = address.split(', ')
        
        # Keep relevant parts for French addresses
        relevant_parts = []
        skip_words = ['France', 'Occitanie', 'Occitania']
        
        for part in parts:
            if part not in skip_words and len(part) > 1:
                relevant_parts.append(part)
                
                # Stop at postal code (French format)
                if len(part) == 5 and part.isdigit():
                    # Add next part (city name) if available
                    next_idx = parts.index(part) + 1
                    if next_idx < len(parts):
                        relevant_parts.append(parts[next_idx])
                    break
        
        # Limit to reasonable length
        cleaned = ', '.join(relevant_parts[:6])
        return cleaned if len(cleaned) < 200 else cleaned[:200] + '...'

    def _extract_department_from_address(self, address: str) -> str:
        """Extract department code from French address"""
        import re
        
        # Look for French postal code (5 digits)
        postal_match = re.search(r'\\b(\\d{5})\\b', address)
        if postal_match:
            postal_code = postal_match.group(1)
            department = postal_code[:2]
            
            # Validate it's an Occitanie department
            occitanie_depts = ['09', '11', '12', '30', '31', '32', '34', '46', '48', '65', '66', '81', '82']
            if department in occitanie_depts:
                return department
        
        return None

    def update_quality_scores(self):
        """Update quality scores after Nominatim enrichment"""
        print("⭐ UPDATING QUALITY SCORES...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE spots 
            SET confidence_score = CASE 
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL THEN 0.8
                WHEN address IS NOT NULL AND address != '' 
                 AND elevation IS NOT NULL AND elevation > 0 THEN 0.75
                WHEN address IS NOT NULL AND address != '' THEN 0.7
                ELSE confidence_score
            END
        """)
        
        self.conn.commit()
        print("✅ Quality scores updated")

    def print_final_report(self):
        """Print enrichment report"""
        print("\\n" + "="*50)
        print("📊 NOMINATIM ENRICHMENT REPORT")
        print("="*50)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(confidence_score) as avg_confidence,
                SUM(CASE WHEN address IS NOT NULL AND address != '' THEN 1 ELSE 0 END) as has_address,
                SUM(CASE WHEN elevation IS NOT NULL AND elevation > 0 THEN 1 ELSE 0 END) as has_elevation,
                SUM(CASE WHEN department IS NOT NULL THEN 1 ELSE 0 END) as has_department,
                SUM(CASE WHEN access_info LIKE '%OSM%' THEN 1 ELSE 0 END) as osm_enriched
            FROM spots
        """)
        
        stats = cursor.fetchone()
        total, avg_conf, has_addr, has_elev, has_dept, osm_enriched = stats
        
        print(f"📈 ENRICHMENT RESULTS:")
        print(f"  New OSM addresses: {self.stats['found_addresses']}")
        print(f"  Success rate: {self.stats['found_addresses']/self.stats['processed']*100:.1f}%")
        print(f"  Processing errors: {self.stats['errors']}")
        
        print(f"\\n✅ UPDATED DATABASE QUALITY:")
        print(f"  Total spots: {total}")
        print(f"  With addresses: {has_addr} ({has_addr/total*100:.1f}%)")
        print(f"  With elevation: {has_elev} ({has_elev/total*100:.1f}%)")
        print(f"  With departments: {has_dept} ({has_dept/total*100:.1f}%)")
        print(f"  Average confidence: {avg_conf:.2f}")
        
        improvement = has_addr/total
        if improvement > 0.7:
            print(f"\\n🏆 EXCELLENT! Over 70% address coverage achieved!")
        elif improvement > 0.5:
            print(f"\\n🎯 GREAT! Over 50% address coverage - ready for API enhancement!")
        else:
            print(f"\\n📈 GOOD PROGRESS! Significant improvement made.")
        
        print(f"\\n🚀 NEXT STEPS:")
        print(f"  • Get IGN API key for premium French data")
        print(f"  • Add Google Maps API for global coverage") 
        print(f"  • Run multi-API enrichment script")

    async def run_nominatim_enrichment(self):
        """Run complete Nominatim enrichment"""
        start_time = time.time()
        
        await self.enrich_with_nominatim()
        self.update_quality_scores()
        
        elapsed = time.time() - start_time
        print(f"\\n⏱️ Total processing time: {elapsed/60:.1f} minutes")
        
        self.print_final_report()

async def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python nominatim_enrichment.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    print("🗺️ QUICK NOMINATIM ENRICHMENT")
    print("Fill missing addresses while you get API keys!")
    print("Uses OpenStreetMap's free, respectful service")
    print()
    
    response = input("Continue with Nominatim enrichment? (y/n): ")
    if response.lower() != 'y':
        print("Aborted. Get your API keys and run multi_api_enrichment.py instead!")
        return
    
    # Create backup
    import shutil
    backup_path = db_path.replace('.db', '_backup_before_nominatim.db')
    shutil.copy2(db_path, backup_path)
    print(f"💾 Backup created: {backup_path}")
    
    # Run Nominatim enrichment
    enricher = NominatimEnricher(db_path)
    await enricher.run_nominatim_enrichment()
    enricher.conn.close()

if __name__ == "__main__":
    asyncio.run(main())
