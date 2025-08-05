"""
Spot Verification System
Ensures only high-quality, verified spots are shown to users
"""

import sqlite3
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class VerificationStatus(Enum):
    VERIFIED = "verified"          # 100% sure, documented
    PENDING = "pending"            # Needs verification
    SUSPICIOUS = "suspicious"      # Likely fake/duplicate
    REJECTED = "rejected"          # Confirmed bad data


@dataclass
class SpotQualityIssue:
    issue_type: str
    severity: str  # high, medium, low
    description: str


class SpotVerifier:
    """Analyzes spots for quality issues"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def analyze_spot_quality(self, spot: Dict) -> Tuple[List[SpotQualityIssue], float]:
        """Analyze a single spot and return issues + quality score (0-1)"""
        issues = []
        score = 1.0
        
        # Check name quality
        name = spot.get('name', '')
        
        # Generic name patterns
        if re.search(r'alt\.\s*\d+', name):
            issues.append(SpotQualityIssue(
                "generic_name", "high", 
                "Name contains generic altitude pattern"
            ))
            score -= 0.3
            
        if name.startswith('Unknown'):
            issues.append(SpotQualityIssue(
                "unknown_name", "high",
                "Name is 'Unknown'"
            ))
            score -= 0.4
            
        if len(name) < 5:
            issues.append(SpotQualityIssue(
                "short_name", "medium",
                "Name too short"
            ))
            score -= 0.2
            
        # Check description quality
        desc = spot.get('description', '')
        
        if not desc:
            issues.append(SpotQualityIssue(
                "no_description", "medium",
                "No description"
            ))
            score -= 0.2
            
        # Generic description patterns
        generic_patterns = [
            "Visite culturelle, histoire régionale",
            "Promenade tranquille, pique-nique",
            "Vestiges historiques de plateau",
            "Site historique de vallée"
        ]
        
        if any(pattern in desc for pattern in generic_patterns):
            issues.append(SpotQualityIssue(
                "generic_description", "high",
                "Generic template description"
            ))
            score -= 0.3
            
        # Check coordinates
        lat = spot.get('latitude', 0)
        lon = spot.get('longitude', 0)
        
        # Suspiciously round coordinates
        if lat % 0.1 == 0 and lon % 0.1 == 0:
            issues.append(SpotQualityIssue(
                "round_coordinates", "medium",
                "Coordinates are suspiciously round"
            ))
            score -= 0.2
            
        # Check source
        source = spot.get('source', '')
        if source.startswith('osm_'):
            # OSM data often needs verification
            issues.append(SpotQualityIssue(
                "osm_source", "low",
                "From OpenStreetMap - needs field verification"
            ))
            score -= 0.1
            
        return issues, max(0, score)
    
    def audit_all_spots(self) -> Dict[str, List[Dict]]:
        """Audit all spots and categorize them"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, latitude, longitude, 
                   type, source, confidence_score, verified, department
            FROM spots
        """)
        
        results = {
            'verified': [],
            'suspicious': [],
            'needs_review': [],
            'duplicates': []
        }
        
        spots = cursor.fetchall()
        
        # First pass: find exact duplicates
        seen_coords = {}
        
        for spot in spots:
            spot_dict = dict(spot)
            coord_key = f"{spot['latitude']:.6f},{spot['longitude']:.6f}"
            
            if coord_key in seen_coords:
                results['duplicates'].append({
                    'spot': spot_dict,
                    'duplicate_of': seen_coords[coord_key]
                })
                continue
                
            seen_coords[coord_key] = spot['id']
            
            # Analyze quality
            issues, score = self.analyze_spot_quality(spot_dict)
            
            if score < 0.3:
                results['suspicious'].append({
                    'spot': spot_dict,
                    'issues': issues,
                    'score': score
                })
            elif score < 0.7:
                results['needs_review'].append({
                    'spot': spot_dict,
                    'issues': issues,
                    'score': score
                })
            else:
                results['verified'].append({
                    'spot': spot_dict,
                    'score': score
                })
                
        conn.close()
        return results
    
    def create_verified_spots_table(self):
        """Create a new table for verified spots only"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verified_spots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                type TEXT NOT NULL,
                department TEXT,
                beauty_rating INTEGER,
                popularity INTEGER,
                difficulty INTEGER,
                best_season TEXT,
                instagram_url TEXT,
                verification_status TEXT DEFAULT 'pending',
                verified_by TEXT,
                verified_date TIMESTAMP,
                verification_notes TEXT,
                photos TEXT,
                user_ratings_count INTEGER DEFAULT 0,
                user_rating_avg REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(latitude, longitude)
            )
        """)
        
        # Add verification history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spot_verification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spot_id INTEGER,
                action TEXT,
                notes TEXT,
                verified_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spot_id) REFERENCES verified_spots(id)
            )
        """)
        
        conn.commit()
        conn.close()


def generate_quality_report(db_path: str):
    """Generate a quality audit report"""
    verifier = SpotVerifier(db_path)
    results = verifier.audit_all_spots()
    
    print("🔍 SPOTS QUALITY AUDIT REPORT")
    print("=" * 50)
    print(f"✅ Verified (high quality): {len(results['verified'])}")
    print(f"⚠️  Needs Review: {len(results['needs_review'])}")
    print(f"❌ Suspicious: {len(results['suspicious'])}")
    print(f"🔁 Duplicates: {len(results['duplicates'])}")
    print("=" * 50)
    
    # Show examples of suspicious spots
    print("\n❌ Examples of Suspicious Spots:")
    for item in results['suspicious'][:5]:
        spot = item['spot']
        print(f"\n- {spot['name']}")
        print(f"  Source: {spot['source']}")
        print(f"  Issues:")
        for issue in item['issues']:
            print(f"    • {issue.description} ({issue.severity})")
    
    return results


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../../data/occitanie_spots.db"
    
    results = generate_quality_report(db_path)
    
    # Create verified spots table
    verifier = SpotVerifier(db_path)
    verifier.create_verified_spots_table()
    
    print("\n✅ Created 'verified_spots' table for quality data!")