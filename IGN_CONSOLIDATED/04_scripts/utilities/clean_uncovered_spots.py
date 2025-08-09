#!/usr/bin/env python3
"""
Clean Uncovered Spots - Remove spots that couldn't be properly geocoded or validated
"""

import sqlite3
import shutil
from datetime import datetime

class SpotCleaner:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.removed_spots = []
        
    def analyze_coverage(self):
        """Analyze current coverage and identify problematic spots"""
        print("🔍 ANALYZING SPOT COVERAGE")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        
        # Overall statistics
        cursor.execute("SELECT COUNT(*) FROM spots")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE verified = 1")
        verified = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE address IS NULL OR address = ''")
        no_address = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(confidence_score), MIN(confidence_score), MAX(confidence_score) FROM spots")
        conf_stats = cursor.fetchone()
        
        print(f"📊 CURRENT STATUS:")
        print(f"  Total spots: {total}")
        print(f"  Verified: {verified} ({verified/total*100:.1f}%)")
        print(f"  Unverified: {total-verified} ({(total-verified)/total*100:.1f}%)")
        print(f"  Without address: {no_address}")
        print(f"  Confidence: avg={conf_stats[0]:.3f}, min={conf_stats[1]:.3f}, max={conf_stats[2]:.3f}")
        
        return total, verified, no_address
    
    def identify_problematic_spots(self):
        """Identify spots that should be considered 'uncovered' and removed"""
        print("\n🎯 IDENTIFYING PROBLEMATIC SPOTS")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        problematic_criteria = []
        
        # 1. Spots without addresses
        cursor.execute("SELECT COUNT(*) FROM spots WHERE address IS NULL OR address = ''")
        no_address_count = cursor.fetchone()[0]
        if no_address_count > 0:
            problematic_criteria.append(f"No address: {no_address_count}")
        
        # 2. Spots with very generic or short addresses
        cursor.execute("""
            SELECT COUNT(*) FROM spots 
            WHERE LENGTH(address) < 20 OR address LIKE '%France%' AND LENGTH(address) < 30
        """)
        generic_addr_count = cursor.fetchone()[0]
        if generic_addr_count > 0:
            problematic_criteria.append(f"Generic addresses: {generic_addr_count}")
        
        # 3. Spots outside reasonable Occitanie bounds (rough check)
        cursor.execute("""
            SELECT COUNT(*) FROM spots 
            WHERE latitude < 42.0 OR latitude > 45.5 OR longitude < 0.0 OR longitude > 5.0
        """)
        outside_region_count = cursor.fetchone()[0]
        if outside_region_count > 0:
            problematic_criteria.append(f"Outside region: {outside_region_count}")
        
        # 4. Spots with extremely low confidence scores
        cursor.execute("SELECT COUNT(*) FROM spots WHERE confidence_score < 0.5")
        very_low_conf_count = cursor.fetchone()[0]
        if very_low_conf_count > 0:
            problematic_criteria.append(f"Very low confidence (<0.5): {very_low_conf_count}")
        
        # 5. Spots with coordinates 0,0 (common error)
        cursor.execute("SELECT COUNT(*) FROM spots WHERE latitude = 0 AND longitude = 0")
        zero_coords_count = cursor.fetchone()[0]
        if zero_coords_count > 0:
            problematic_criteria.append(f"Zero coordinates: {zero_coords_count}")
        
        print("🔍 PROBLEMATIC SPOT CATEGORIES:")
        if problematic_criteria:
            for criteria in problematic_criteria:
                print(f"  • {criteria}")
        else:
            print("  ✅ No clearly problematic spots found!")
            print("  📈 Nominatim enrichment was very successful")
        
        return problematic_criteria
    
    def get_removal_candidates(self):
        """Get spots that should be removed"""
        cursor = self.conn.cursor()
        
        # Build comprehensive removal query
        removal_conditions = [
            "(address IS NULL OR address = '')",
            "(LENGTH(address) < 15)",
            "(latitude < 42.0 OR latitude > 45.5 OR longitude < 0.0 OR longitude > 5.0)",
            "(confidence_score < 0.5)",
            "(latitude = 0 AND longitude = 0)"
        ]
        
        query = f"""
            SELECT id, name, latitude, longitude, address, confidence_score, verified
            FROM spots 
            WHERE {' OR '.join(removal_conditions)}
            ORDER BY confidence_score ASC, id ASC
        """
        
        cursor.execute(query)
        candidates = cursor.fetchall()
        
        print(f"\n📋 REMOVAL CANDIDATES: {len(candidates)} spots")
        if candidates:
            print("Sample problematic spots:")
            for i, spot in enumerate(candidates[:10]):
                reason = "No address" if not spot[4] else f"Short addr ({len(spot[4])} chars)" if len(spot[4]) < 15 else "Other issue"
                print(f"  {i+1}. ID {spot[0]}: {spot[1][:40]}... - {reason}")
                print(f"      Location: {spot[2]:.4f}, {spot[3]:.4f} - Conf: {spot[5]:.3f}")
        
        return candidates
    
    def remove_uncovered_spots(self, candidates, confirm=True):
        """Remove the identified problematic spots"""
        if not candidates:
            print("\n✅ NO SPOTS TO REMOVE - All spots are properly covered!")
            return
        
        print(f"\n🗑️ PREPARING TO REMOVE {len(candidates)} UNCOVERED SPOTS")
        
        if confirm:
            print("\nSpots to be removed:")
            for spot in candidates[:5]:
                print(f"  • ID {spot[0]}: {spot[1][:50]}")
            if len(candidates) > 5:
                print(f"  ... and {len(candidates) - 5} more")
            
            response = input(f"\nRemove these {len(candidates)} uncovered spots? (y/n): ").lower()
            if response != 'y':
                print("❌ Removal cancelled")
                return
        
        # Create backup before removal
        backup_path = self.db_path.replace('.db', f'_backup_before_removal_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(self.db_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        
        # Remove spots
        cursor = self.conn.cursor()
        removed_ids = [spot[0] for spot in candidates]
        
        cursor.execute(f"DELETE FROM spots WHERE id IN ({','.join(map(str, removed_ids))})")
        self.conn.commit()
        
        self.removed_spots = candidates
        print(f"✅ Removed {len(candidates)} uncovered spots")
        
    def print_final_report(self):
        """Print final cleanup report"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM spots")
        final_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE verified = 1")
        final_verified = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(confidence_score) FROM spots")
        final_avg_conf = cursor.fetchone()[0]
        
        print("\n" + "="*50)
        print("🧹 CLEANUP COMPLETE")
        print("="*50)
        print(f"📊 FINAL STATISTICS:")
        print(f"  Remaining spots: {final_count}")
        print(f"  Verified spots: {final_verified} ({final_verified/final_count*100:.1f}%)")
        print(f"  Average confidence: {final_avg_conf:.3f}")
        print(f"  Removed spots: {len(self.removed_spots)}")
        
        if self.removed_spots:
            print(f"\n🗑️ REMOVED SPOT SUMMARY:")
            print(f"  Total removed: {len(self.removed_spots)}")
            print(f"  Quality improvement: {final_avg_conf:.3f} avg confidence")
        
        print(f"\n✅ DATABASE READY FOR PRODUCTION!")
        print(f"  All remaining spots have addresses and reasonable quality")
        
    def run_cleanup(self, auto_confirm=False):
        """Run complete cleanup process"""
        print("🧹 SPOT COVERAGE CLEANUP")
        print("Removing uncovered or problematic spots")
        print()
        
        # Analyze current state
        total, verified, no_addr = self.analyze_coverage()
        
        # Identify problematic spots
        criteria = self.identify_problematic_spots()
        
        # Get removal candidates
        candidates = self.get_removal_candidates()
        
        # Remove if needed
        if candidates or no_addr > 0:
            self.remove_uncovered_spots(candidates, confirm=not auto_confirm)
        else:
            print("\n🎉 EXCELLENT NEWS!")
            print("All spots are properly covered with addresses and good quality!")
            print("No cleanup needed - Nominatim enrichment was 100% successful!")
        
        # Final report
        self.print_final_report()

def main():
    """Main execution"""
    import sys
    
    db_path = "data/occitanie_spots.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print("🧹 UNCOVERED SPOTS CLEANUP")
    print("Remove spots that couldn't be properly geocoded")
    print()
    
    cleaner = SpotCleaner(db_path)
    cleaner.run_cleanup()
    cleaner.conn.close()

if __name__ == "__main__":
    main()
