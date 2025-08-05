#!/usr/bin/env python3
"""
Immediate Data Enrichment for SPOTS Project
Enriches data using coordinate analysis, pattern recognition, and internal logic
"""

import sqlite3
import math
import re
from typing import Dict, List, Tuple, Optional

class ImmediateEnricher:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Geographic references for Occitanie
        self.geographic_features = {
            'mountain_ranges': {
                'Pyrénées': {'lat_range': (42.5, 43.0), 'lng_range': (-1.0, 2.5), 'min_elevation': 800},
                'Montagne Noire': {'lat_range': (43.4, 43.7), 'lng_range': (2.0, 2.8), 'min_elevation': 600},
                'Causses': {'lat_range': (43.8, 44.5), 'lng_range': (1.8, 3.0), 'min_elevation': 400},
                'Cévennes': {'lat_range': (43.9, 44.3), 'lng_range': (3.2, 4.0), 'min_elevation': 500}
            },
            'river_valleys': {
                'Garonne': {'lat_range': (43.2, 44.2), 'lng_range': (0.5, 1.5)},
                'Lot': {'lat_range': (44.2, 44.6), 'lng_range': (1.0, 2.5)},
                'Tarn': {'lat_range': (43.7, 44.1), 'lng_range': (1.8, 2.8)},
                'Ariège': {'lat_range': (42.8, 43.2), 'lng_range': (1.3, 1.8)}
            }
        }
        
        # Department mapping with enhanced info
        self.departments = {
            '09': {
                'name': 'Ariège', 'region': 'Pyrénées', 
                'bounds': ((42.5, 0.8), (43.2, 2.2)),
                'features': ['mountains', 'caves', 'thermal_springs'],
                'elevation_avg': 1200
            },
            '12': {
                'name': 'Aveyron', 'region': 'Causses', 
                'bounds': ((43.7, 1.8), (44.9, 3.1)),
                'features': ['plateaus', 'gorges', 'historical_sites'],
                'elevation_avg': 600
            },
            '31': {
                'name': 'Haute-Garonne', 'region': 'Mixed', 
                'bounds': ((42.9, 0.4), (43.9, 2.0)),
                'features': ['plains', 'foothills', 'urban_areas'],
                'elevation_avg': 400
            },
            '32': {
                'name': 'Gers', 'region': 'Gascogne', 
                'bounds': ((43.3, -0.1), (44.1, 1.2)),
                'features': ['rolling_hills', 'vineyards', 'bastides'],
                'elevation_avg': 200
            },
            '46': {
                'name': 'Lot', 'region': 'Causses', 
                'bounds': ((44.2, 0.9), (45.1, 2.2)),
                'features': ['limestone_plateaus', 'river_valleys', 'medieval_towns'],
                'elevation_avg': 300
            },
            '65': {
                'name': 'Hautes-Pyrénées', 'region': 'Pyrénées', 
                'bounds': ((42.7, -0.3), (43.5, 0.6)),
                'features': ['high_mountains', 'lakes', 'thermal_springs'],
                'elevation_avg': 1500
            },
            '81': {
                'name': 'Tarn', 'region': 'Montagne Noire', 
                'bounds': ((43.4, 1.5), (44.2, 2.8)),
                'features': ['forests', 'mountains', 'rivers'],
                'elevation_avg': 500
            },
            '82': {
                'name': 'Tarn-et-Garonne', 'region': 'Quercy', 
                'bounds': ((43.7, 0.7), (44.4, 1.8)),
                'features': ['river_valleys', 'orchards', 'medieval_sites'],
                'elevation_avg': 150
            }
        }
        
        self.stats = {
            'estimated_elevation': 0,
            'assigned_departments': 0,
            'enhanced_names': 0,
            'added_geographic_context': 0,
            'classified_terrain': 0
        }

    def estimate_elevation_from_coordinates(self):
        """Estimate elevation based on coordinate patterns and regional data"""
        print("🏔️ ESTIMATING ELEVATION FROM GEOGRAPHIC PATTERNS...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude, type 
            FROM spots 
            WHERE elevation IS NULL OR elevation = 0
        """)
        
        spots_to_estimate = cursor.fetchall()
        print(f"📍 Estimating elevation for {len(spots_to_estimate)} spots...")
        
        for spot in spots_to_estimate:
            spot_id, lat, lng, spot_type = spot
            estimated_elevation = self._estimate_elevation_by_region(lat, lng, spot_type)
            
            if estimated_elevation:
                cursor.execute(
                    "UPDATE spots SET elevation = ? WHERE id = ?",
                    (estimated_elevation, spot_id)
                )
                self.stats['estimated_elevation'] += 1
        
        self.conn.commit()
        print(f"✅ Estimated elevation for {self.stats['estimated_elevation']} spots")

    def _estimate_elevation_by_region(self, lat: float, lng: float, spot_type: str) -> Optional[int]:
        """Estimate elevation based on geographic region and spot type"""
        
        # Check mountain ranges
        for range_name, range_data in self.geographic_features['mountain_ranges'].items():
            lat_range = range_data['lat_range']
            lng_range = range_data['lng_range']
            
            if lat_range[0] <= lat <= lat_range[1] and lng_range[0] <= lng <= lng_range[1]:
                base_elevation = range_data['min_elevation']
                
                # Adjust based on spot type
                if spot_type == 'cave':
                    return base_elevation + 50  # Caves often at moderate elevation
                elif spot_type == 'waterfall':
                    return base_elevation + 200  # Waterfalls often higher up
                elif spot_type == 'natural_spring':
                    return base_elevation - 100  # Springs often in valleys
                else:
                    return base_elevation
        
        # Check river valleys (lower elevation)
        for valley_name, valley_data in self.geographic_features['river_valleys'].items():
            lat_range = valley_data['lat_range']
            lng_range = valley_data['lng_range']
            
            if lat_range[0] <= lat <= lat_range[1] and lng_range[0] <= lng <= lng_range[1]:
                if spot_type == 'natural_spring':
                    return 150  # Springs common in valleys
                elif spot_type == 'historical_ruins':
                    return 200  # Ruins often on slight elevations
                else:
                    return 180  # General valley elevation
        
        # Default regional estimates
        for dept_code, dept_info in self.departments.items():
            bounds = dept_info['bounds']
            min_bounds, max_bounds = bounds
            
            if (min_bounds[0] <= lat <= max_bounds[0] and 
                min_bounds[1] <= lng <= max_bounds[1]):
                return dept_info['elevation_avg']
        
        return None

    def assign_departments_by_coordinates(self):
        """Assign departments based on coordinate bounds"""
        print("🗺️ ASSIGNING DEPARTMENTS BY COORDINATES...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude 
            FROM spots 
            WHERE department IS NULL OR department = ''
        """)
        
        spots_to_assign = cursor.fetchall()
        print(f"🏛️ Processing {len(spots_to_assign)} spots for department assignment...")
        
        for spot in spots_to_assign:
            spot_id, lat, lng = spot
            
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
                    self.stats['assigned_departments'] += 1
                    break
        
        self.conn.commit()
        print(f"✅ Assigned departments to {self.stats['assigned_departments']} spots")

    def enhance_names_with_geographic_context(self):
        """Enhance spot names with geographic and regional context"""
        print("✨ ENHANCING NAMES WITH GEOGRAPHIC CONTEXT...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, latitude, longitude, elevation, department, type 
            FROM spots 
            WHERE name NOT LIKE '%(%' OR name NOT LIKE '%alt.%'
        """)
        
        spots_to_enhance = cursor.fetchall()
        print(f"📛 Enhancing {len(spots_to_enhance)} spot names...")
        
        for spot in spots_to_enhance:
            spot_id, current_name, lat, lng, elevation, department, spot_type = spot
            
            enhanced_name = self._create_enhanced_name(
                current_name, lat, lng, elevation, department, spot_type
            )
            
            if enhanced_name != current_name:
                cursor.execute(
                    "UPDATE spots SET name = ? WHERE id = ?",
                    (enhanced_name, spot_id)
                )
                self.stats['enhanced_names'] += 1
        
        self.conn.commit()
        print(f"✅ Enhanced {self.stats['enhanced_names']} spot names")

    def _create_enhanced_name(self, current_name: str, lat: float, lng: float, 
                            elevation: int, department: str, spot_type: str) -> str:
        """Create enhanced name with geographic context"""
        
        name_parts = [current_name]
        
        # Add geographic region context
        region_context = self._get_geographic_region(lat, lng)
        if region_context and region_context not in current_name:
            name_parts.append(f"({region_context})")
        
        # Add department if not already present
        if department and department in self.departments:
            dept_name = self.departments[department]['name']
            if dept_name not in current_name and not any(f"({region}" in current_name for region in [dept_name]):
                name_parts.append(f"({dept_name})")
        
        # Add elevation context for mountain features
        if elevation and elevation > 800 and 'alt.' not in current_name:
            name_parts.append(f"alt. {elevation}m")
        
        # Add terrain type for specific features
        terrain_type = self._get_terrain_type(lat, lng, elevation, spot_type)
        if terrain_type and terrain_type not in current_name:
            name_parts.append(f"- {terrain_type}")
        
        return ' '.join(name_parts)

    def _get_geographic_region(self, lat: float, lng: float) -> Optional[str]:
        """Identify the geographic region for coordinates"""
        
        # Check mountain ranges
        for range_name, range_data in self.geographic_features['mountain_ranges'].items():
            lat_range = range_data['lat_range']
            lng_range = range_data['lng_range']
            
            if lat_range[0] <= lat <= lat_range[1] and lng_range[0] <= lng <= lng_range[1]:
                return range_name
        
        # Check river valleys
        for valley_name, valley_data in self.geographic_features['river_valleys'].items():
            lat_range = valley_data['lat_range']
            lng_range = valley_data['lng_range']
            
            if lat_range[0] <= lat <= lat_range[1] and lng_range[0] <= lng <= lng_range[1]:
                return f"Vallée de la {valley_name}"
        
        return None

    def _get_terrain_type(self, lat: float, lng: float, elevation: int, spot_type: str) -> Optional[str]:
        """Determine terrain type based on location and elevation"""
        
        if elevation:
            if elevation > 1500:
                return "haute montagne"
            elif elevation > 800:
                return "montagne"
            elif elevation > 400:
                return "collines"
            elif elevation > 200:
                return "plateau"
            else:
                return "plaine"
        
        # Fallback based on geographic features
        for range_name, range_data in self.geographic_features['mountain_ranges'].items():
            lat_range = range_data['lat_range']
            lng_range = range_data['lng_range']
            
            if lat_range[0] <= lat <= lat_range[1] and lng_range[0] <= lng <= lng_range[1]:
                return "zone montagneuse"
        
        return None

    def add_activity_recommendations(self):
        """Add detailed activity recommendations based on spot characteristics"""
        print("🎯 ADDING ACTIVITY RECOMMENDATIONS...")
        
        cursor = self.conn.cursor()
        
        # Create enhanced descriptions with activity recommendations
        activity_templates = {
            'cave': {
                'mountain': "Grotte en zone montagneuse. Activités: spéléologie avancée, exploration géologique, photographie souterraine. Équipement spécialisé requis.",
                'plateau': "Grotte de plateau calcaire. Idéale pour initiation spéléologie, géologie amateur, sorties éducatives.",
                'valley': "Grotte de vallée. Accessible pour découverte familiale, observation formations rocheuses, activités pédagogiques."
            },
            'waterfall': {
                'mountain': "Cascade de montagne. Randonnée sportive, alpinisme, photographie de nature sauvage. Vue panoramique exceptionnelle.",
                'plateau': "Cascade de plateau. Randonnée modérée, pique-nique, observation faune/flore, détente nature.",
                'valley': "Cascade de vallée. Accès facile, promenade familiale, baignade possible (selon saison), relaxation."
            },
            'natural_spring': {
                'mountain': "Source de montagne. Randonnée d'altitude, hydrogéologie, observation écosystèmes d'altitude.",
                'plateau': "Source de plateau. Découverte nature, géologie, observation oiseaux, ressourcement.",
                'valley': "Source de vallée. Promenade tranquille, pique-nique, observation nature, détente."
            },
            'historical_ruins': {
                'mountain': "Ruines en site montagnard. Randonnée historique, photographie patrimoine, découverte archéologique.",
                'plateau': "Vestiges historiques de plateau. Visite culturelle, histoire régionale, architecture ancienne.",
                'valley': "Site historique de vallée. Découverte patrimoniale accessible, histoire locale, promenade éducative."
            }
        }
        
        cursor.execute("SELECT id, type, elevation, latitude, longitude FROM spots")
        all_spots = cursor.fetchall()
        
        for spot in all_spots:
            spot_id, spot_type, elevation, lat, lng = spot
            
            # Determine terrain context
            terrain_context = self._get_terrain_context(elevation, lat, lng)
            
            if spot_type in activity_templates and terrain_context in activity_templates[spot_type]:
                enhanced_description = activity_templates[spot_type][terrain_context]
                
                cursor.execute("""
                    UPDATE spots 
                    SET description = ?,
                        access_info = ?
                    WHERE id = ? AND (description IS NULL OR LENGTH(description) < 100)
                """, (
                    enhanced_description,
                    self._generate_access_info(elevation, spot_type),
                    spot_id
                ))
                
                self.stats['added_geographic_context'] += 1
        
        self.conn.commit()
        print(f"✅ Added geographic context to {self.stats['added_geographic_context']} spots")

    def _get_terrain_context(self, elevation: int, lat: float, lng: float) -> str:
        """Determine terrain context for activity recommendations"""
        
        if elevation:
            if elevation > 800:
                return 'mountain'
            elif elevation > 300:
                return 'plateau'
            else:
                return 'valley'
        
        # Fallback to geographic analysis
        for range_name, range_data in self.geographic_features['mountain_ranges'].items():
            lat_range = range_data['lat_range']
            lng_range = range_data['lng_range']
            
            if lat_range[0] <= lat <= lat_range[1] and lng_range[0] <= lng <= lng_range[1]:
                return 'mountain'
        
        return 'valley'

    def _generate_access_info(self, elevation: int, spot_type: str) -> str:
        """Generate access information based on elevation and type"""
        
        difficulty_info = []
        
        if elevation:
            if elevation > 1200:
                difficulty_info.append("Randonnée de montagne exigeante")
            elif elevation > 600:
                difficulty_info.append("Randonnée modérée en terrain vallonné")
            else:
                difficulty_info.append("Accès relativement facile")
        
        if spot_type == 'cave':
            difficulty_info.append("Équipement spéléo recommandé")
        elif spot_type == 'waterfall':
            difficulty_info.append("Chaussures antidérapantes conseillées")
        
        return ". ".join(difficulty_info) + "." if difficulty_info else "Accès à vérifier localement."

    def run_immediate_enrichment(self):
        """Run all immediate enrichment processes"""
        print("🚀 STARTING IMMEDIATE DATA ENRICHMENT")
        print("=" * 60)
        
        # Step 1: Geographic data enrichment
        self.estimate_elevation_from_coordinates()
        self.assign_departments_by_coordinates()
        
        # Step 2: Name and context enrichment
        self.enhance_names_with_geographic_context()
        self.add_activity_recommendations()
        
        # Step 3: Update confidence scores
        self.update_confidence_scores()
        
        # Step 4: Generate report
        self.print_enrichment_report()

    def update_confidence_scores(self):
        """Update confidence scores based on enriched data"""
        print("\n⭐ UPDATING CONFIDENCE SCORES...")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE spots 
            SET confidence_score = CASE 
                WHEN elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL 
                 AND LENGTH(description) > 50 THEN 0.8
                WHEN elevation IS NOT NULL AND elevation > 0 
                 AND department IS NOT NULL THEN 0.7
                WHEN elevation IS NOT NULL AND elevation > 0 THEN 0.6
                ELSE confidence_score
            END
        """)
        
        self.conn.commit()
        print("✅ Updated confidence scores")

    def print_enrichment_report(self):
        """Print enrichment completion report"""
        print("\n" + "="*60)
        print("📊 IMMEDIATE ENRICHMENT COMPLETED")
        print("="*60)
        
        cursor = self.conn.cursor()
        
        # Get final statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(confidence_score) as avg_confidence,
                SUM(CASE WHEN elevation IS NOT NULL AND elevation > 0 THEN 1 ELSE 0 END) as has_elevation,
                SUM(CASE WHEN department IS NOT NULL THEN 1 ELSE 0 END) as has_department,
                SUM(CASE WHEN LENGTH(description) > 50 THEN 1 ELSE 0 END) as enhanced_descriptions
            FROM spots
        """)
        
        stats = cursor.fetchone()
        total, avg_conf, has_elev, has_dept, enhanced_desc = stats
        
        print(f"📈 ENRICHMENT STATISTICS:")
        print(f"  Estimated elevations: {self.stats['estimated_elevation']}")
        print(f"  Assigned departments: {self.stats['assigned_departments']}")
        print(f"  Enhanced names: {self.stats['enhanced_names']}")
        print(f"  Added geographic context: {self.stats['added_geographic_context']}")
        
        print(f"\n✅ FINAL DATA STATE:")
        print(f"  Total spots: {total}")
        print(f"  Average confidence: {avg_conf:.2f}")
        print(f"  With elevation: {has_elev} ({has_elev/total*100:.1f}%)")
        print(f"  With departments: {has_dept} ({has_dept/total*100:.1f}%)")
        print(f"  Enhanced descriptions: {enhanced_desc} ({enhanced_desc/total*100:.1f}%)")
        
        print(f"\n🎯 IMMEDIATE ENRICHMENT COMPLETE - READY FOR EXTERNAL API ENRICHMENT!")

def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python immediate_enrichment.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    # Create backup
    import shutil
    backup_path = db_path.replace('.db', '_backup_before_immediate_enrichment.db')
    shutil.copy2(db_path, backup_path)
    print(f"💾 Backup created: {backup_path}")
    
    # Run immediate enrichment
    enricher = ImmediateEnricher(db_path)
    enricher.run_immediate_enrichment()
    enricher.conn.close()

if __name__ == "__main__":
    main()
