#!/usr/bin/env python3
"""
Remove Unverified Low-Confidence Spots
Filter out spots that are both unverified and have low confidence scores
"""

import sqlite3
import shutil
from datetime import datetime

class QualityFilter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def analyze_before_filtering(self):
        """Analyze database before filtering"""
        print("📊 PRE-FILTERING ANALYSIS")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        
        # Overall stats
        cursor.execute("SELECT COUNT(*) FROM spots")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE verified = 1")
        verified = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(confidence_score) FROM spots")
        avg_conf = cursor.fetchone()[0]
        
        # Target removal group
        cursor.execute("SELECT COUNT(*) FROM spots WHERE verified = 0 AND confidence_score <= 0.75")
        to_remove = cursor.fetchone()[0]
        
        print(f"📈 CURRENT STATE:")
        print(f"  Total spots: {total}")
        print(f"  Verified: {verified} ({verified/total*100:.1f}%)")
        print(f"  Unverified: {total-verified} ({(total-verified)/total*100:.1f}%)")
        print(f"  Average confidence: {avg_conf:.3f}")
        print(f"  Target removal (unverified + low conf): {to_remove}")
        
        return total, verified, to_remove
    
    def get_removal_targets(self):
        """Get spots to be removed"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, name, type, latitude, longitude, confidence_score, verified, source
            FROM spots 
            WHERE verified = 0 AND confidence_score <= 0.75
            ORDER BY confidence_score ASC, id ASC
        """)
        
        targets = cursor.fetchall()
        return targets
    
    def show_removal_preview(self, targets):
        """Show preview of spots to be removed"""
        print(f"\n🎯 REMOVAL PREVIEW: {len(targets)} spots")
        print("=" * 50)
        
        # Group by source
        source_counts = {}
        for spot in targets:
            source = spot[7] or 'unknown'
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print("📍 BY SOURCE:")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} spots")
        
        # Group by type
        type_counts = {}
        for spot in targets:
            spot_type = spot[2] or 'unknown'
            type_counts[spot_type] = type_counts.get(spot_type, 0) + 1
        
        print("\n🏷️ BY TYPE:")
        for spot_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {spot_type}: {count} spots")
        
        print(f"\n📋 SAMPLE SPOTS TO REMOVE:")
        for i, spot in enumerate(targets[:10]):
            print(f"  {i+1}. ID {spot[0]}: {spot[1][:40]}...")
            print(f"      Type: {spot[2]} | Source: {spot[7]} | Conf: {spot[5]:.3f}")
        
        if len(targets) > 10:
            print(f"  ... and {len(targets) - 10} more")
    
    def remove_low_quality_spots(self, targets):
        """Remove the unverified low-confidence spots"""
        print(f"\n🗑️ REMOVING {len(targets)} LOW-QUALITY SPOTS")
        print("=" * 50)
        
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_path.replace('.db', f'_backup_before_quality_filter_{timestamp}.db')
        shutil.copy2(self.db_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        
        # Remove spots
        cursor = self.conn.cursor()
        removal_ids = [spot[0] for spot in targets]
        
        if removal_ids:
            placeholders = ','.join(['?'] * len(removal_ids))
            cursor.execute(f"DELETE FROM spots WHERE id IN ({placeholders})", removal_ids)
            self.conn.commit()
            
            print(f"✅ Successfully removed {len(targets)} spots")
        else:
            print("ℹ️ No spots to remove")
    
    def analyze_after_filtering(self):
        """Analyze database after filtering"""
        print(f"\n📊 POST-FILTERING ANALYSIS")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        
        # New stats
        cursor.execute("SELECT COUNT(*) FROM spots")
        new_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE verified = 1")
        verified = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(confidence_score) FROM spots")
        new_avg_conf = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(confidence_score), MAX(confidence_score) FROM spots")
        conf_range = cursor.fetchone()
        
        # Source distribution
        cursor.execute("SELECT source, COUNT(*) FROM spots GROUP BY source ORDER BY COUNT(*) DESC LIMIT 5")
        top_sources = cursor.fetchall()
        
        print(f"✨ IMPROVED QUALITY:")
        print(f"  Remaining spots: {new_total}")
        print(f"  Verified: {verified} ({verified/new_total*100:.1f}%)")
        print(f"  Unverified: {new_total-verified} ({(new_total-verified)/new_total*100:.1f}%)")
        print(f"  Average confidence: {new_avg_conf:.3f}")
        print(f"  Confidence range: {conf_range[0]:.3f} - {conf_range[1]:.3f}")
        
        print(f"\n📍 TOP SOURCES REMAINING:")
        for source, count in top_sources:
            print(f"  {source or 'unknown'}: {count} spots")
        
        # Quality assessment
        verified_pct = verified / new_total * 100
        if verified_pct > 25:
            quality_rating = "🏆 EXCELLENT"
        elif verified_pct > 15:
            quality_rating = "🎯 VERY GOOD"
        else:
            quality_rating = "📈 IMPROVED"
        
        print(f"\n{quality_rating} - Database quality significantly improved!")
        
    def run_quality_filter(self):
        """Run complete quality filtering process"""
        print("🔧 QUALITY FILTERING: Remove Unverified + Low Confidence")
        print("Improving database quality by removing questionable spots")
        print()
        
        # Pre-analysis
        total_before, verified_before, removal_count = self.analyze_before_filtering()
        
        if removal_count == 0:
            print("\n✅ No low-quality spots found - database already optimized!")
            return
        
        # Get targets and preview
        targets = self.get_removal_targets()
        self.show_removal_preview(targets)
        
        # Confirm removal
        expected_remaining = total_before - len(targets)
        verified_pct_after = verified_before / expected_remaining * 100
        
        print(f"\n📈 EXPECTED IMPROVEMENT:")
        print(f"  Spots: {total_before} → {expected_remaining} ({len(targets)} removed)")
        print(f"  Verified %: {verified_before/total_before*100:.1f}% → {verified_pct_after:.1f}%")
        
        response = input(f"\nProceed with removing {len(targets)} low-quality spots? (y/n): ").lower()
        if response != 'y':
            print("❌ Filtering cancelled - database unchanged")
            return
        
        # Execute removal
        self.remove_low_quality_spots(targets)
        
        # Post-analysis
        self.analyze_after_filtering()
        
        print(f"\n🚀 QUALITY FILTERING COMPLETE!")
        print(f"Database is now production-ready with higher quality standards")

def main():
    """Main execution"""
    db_path = "data/occitanie_spots.db"
    
    print("🔧 SPOT DATABASE QUALITY FILTER")
    print("Remove unverified + low confidence spots")
    print()
    
    filter_tool = QualityFilter(db_path)
    filter_tool.run_quality_filter()
    filter_tool.conn.close()

if __name__ == "__main__":
    main()
