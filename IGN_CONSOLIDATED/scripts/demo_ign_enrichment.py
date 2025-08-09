#!/usr/bin/env python3
"""
Demo IGN data enrichment using simulated data
Shows how the enrichment would work if we had IGN data
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import random


class SimulatedIGNProcessor:
    """Simulated IGN data processor for demo purposes"""
    
    def __init__(self):
        # Simulated data for Occitanie region
        self.simulated_water_features = {
            "34": [  # Hérault
                {"name": "Lac du Salagou", "lat": 43.6508, "lon": 3.3857, "type": "Lac"},
                {"name": "Rivière Hérault", "lat": 43.75, "lon": 3.45, "type": "Cours d'eau"},
                {"name": "Étang de Thau", "lat": 43.42, "lon": 3.67, "type": "Plan d'eau"}
            ],
            "65": [  # Hautes-Pyrénées
                {"name": "Gave de Pau", "lat": 43.00, "lon": -0.10, "type": "Cours d'eau"},
                {"name": "Lac d'Artouste", "lat": 42.85, "lon": -0.35, "type": "Lac"}
            ]
        }
        
        self.simulated_trails = [
            {"name": "GR10", "type": "Sentier"},
            {"name": "Sentier du Lac", "type": "Sentier"},
            {"name": "Chemin de randonnée", "type": "Chemin"},
            {"name": "Voie verte du Canal du Midi", "type": "Voie verte"}
        ]
        
    def find_nearest_water(self, lat: float, lon: float, dept: str) -> Optional[Dict]:
        """Simulate finding nearest water feature"""
        if dept not in self.simulated_water_features:
            return None
            
        water_features = self.simulated_water_features[dept]
        if not water_features:
            return None
            
        # Find closest water feature (simplified distance)
        min_dist = float('inf')
        nearest = None
        
        for feature in water_features:
            # Simple euclidean distance (not accurate but good for demo)
            dist = ((lat - feature['lat'])**2 + (lon - feature['lon'])**2)**0.5
            dist_meters = dist * 111000  # Rough conversion to meters
            
            if dist_meters < min_dist:
                min_dist = dist_meters
                nearest = feature
                
        if nearest and min_dist < 5000:  # Within 5km
            return {
                'name': nearest['name'],
                'type': nearest['type'],
                'distance': round(min_dist, 1),
                'department': dept
            }
        return None
        
    def get_elevation(self, lat: float, lon: float) -> float:
        """Simulate elevation data"""
        # Simulate elevation based on location
        # Higher in Pyrénées, lower near coast
        base_elevation = 100
        
        # Pyrénées effect (south)
        if lat < 43.0:
            base_elevation += (43.0 - lat) * 500
            
        # Add some randomness
        variation = random.uniform(-50, 50)
        
        return round(base_elevation + variation, 1)
        
    def find_nearby_trails(self, lat: float, lon: float) -> List[Dict]:
        """Simulate finding nearby trails"""
        # Randomly select 1-3 trails
        num_trails = random.randint(1, 3)
        selected = random.sample(self.simulated_trails, num_trails)
        
        trails = []
        for trail in selected:
            trails.append({
                'type': trail['type'],
                'name': trail['name'],
                'distance': round(random.uniform(100, 2000), 1)
            })
            
        return sorted(trails, key=lambda x: x['distance'])
        
    def check_forest_coverage(self, lat: float, lon: float) -> Dict:
        """Simulate forest coverage check"""
        # 30% chance of being in forest
        in_forest = random.random() < 0.3
        
        forest_types = ["Forêt de feuillus", "Forêt de conifères", "Forêt mixte"]
        
        if in_forest:
            return {
                'in_forest': True,
                'forest_type': random.choice(forest_types)
            }
        return {'in_forest': False}
        
    def enrich_spot(self, spot: Dict) -> Dict:
        """Enrich a spot with simulated IGN data"""
        lat = spot.get('lat')
        lon = spot.get('lon')
        dept = spot.get('department', '')
        
        if not lat or not lon:
            return spot
            
        enriched = spot.copy()
        
        print(f"🔍 Enriching: {spot.get('name', 'Unknown')} ({lat}, {lon})")
        
        # Add elevation
        enriched['elevation_ign'] = self.get_elevation(lat, lon)
        print(f"  📏 Elevation: {enriched['elevation_ign']}m")
        
        # Find nearest water
        water = self.find_nearest_water(lat, lon, dept)
        if water:
            enriched['nearest_water'] = water
            print(f"  💧 Water: {water['name']} ({water['distance']}m)")
            
        # Find trails
        trails = self.find_nearby_trails(lat, lon)
        enriched['nearby_trails'] = trails
        print(f"  🥾 Trails: {len(trails)} found")
        
        # Check forest
        forest = self.check_forest_coverage(lat, lon)
        enriched['forest_info'] = forest
        if forest['in_forest']:
            print(f"  🌲 In forest: {forest['forest_type']}")
            
        return enriched


def main():
    """Run the demo enrichment"""
    print("🗺️ IGN Data Enrichment Demo for Occitanie Spots")
    print("=" * 60)
    print("ℹ️  Note: Using simulated data for demonstration purposes")
    print()
    
    # Load Instagram spots
    with open('exports/instagram_spots_20250803_195033.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    spots = data['spots']
    
    # Convert to processing format
    spots_for_processing = []
    for spot in spots:
        if spot['coordinates']['lat'] and spot['coordinates']['lon']:
            spots_for_processing.append({
                'name': spot['name'],
                'lat': spot['coordinates']['lat'],
                'lon': spot['coordinates']['lon'],
                'department': spot.get('department', ''),
                'caption': spot.get('caption', ''),
                'activities': spot.get('activities', []),
                'type': spot.get('type', 'unknown'),
                'collected_at': spot.get('collected_at', '')
            })
    
    print(f"📍 Processing {len(spots_for_processing)} spots with coordinates...")
    print()
    
    # Process with simulated data
    processor = SimulatedIGNProcessor()
    enriched_spots = []
    
    for i, spot in enumerate(spots_for_processing, 1):
        print(f"[{i}/{len(spots_for_processing)}]")
        enriched = processor.enrich_spot(spot)
        enriched_spots.append(enriched)
        print()
    
    # Save enriched data
    output_file = f"exports/instagram_spots_enriched_ign_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_data = {
        'export_date': datetime.now().isoformat(),
        'total_spots': len(enriched_spots),
        'enrichment_source': 'IGN Open Data (Simulated Demo)',
        'note': 'This is demo data showing how real IGN enrichment would work',
        'spots': enriched_spots
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print("✅ Demo enriched data saved to:", output_file)
    
    # Summary
    print("\n📊 Enrichment Summary:")
    print("=" * 40)
    
    spots_with_elevation = sum(1 for s in enriched_spots if 'elevation_ign' in s)
    spots_with_water = sum(1 for s in enriched_spots if s.get('nearest_water'))
    spots_with_trails = sum(1 for s in enriched_spots if s.get('nearby_trails'))
    spots_in_forest = sum(1 for s in enriched_spots if s.get('forest_info', {}).get('in_forest'))
    
    print(f"  📏 Elevation data: {spots_with_elevation}/{len(enriched_spots)} spots")
    print(f"  💧 Near water: {spots_with_water}/{len(enriched_spots)} spots")
    print(f"  🥾 Trail access: {spots_with_trails}/{len(enriched_spots)} spots")
    print(f"  🌲 In forest: {spots_in_forest}/{len(enriched_spots)} spots")
    
    # Show sample
    print("\n📋 Sample enriched spot:")
    print(json.dumps(enriched_spots[0], indent=2, ensure_ascii=False))
    
    print("\n💡 How to get real IGN data:")
    print("1. Visit https://geotribu.github.io/ign-fr-opendata-download-ui/")
    print("2. Select BDTOPO and RGEALTI products")
    print("3. Click on departments 34 and 65")
    print("4. Download and extract the .7z files")
    print("5. Run the full enrichment pipeline")


if __name__ == "__main__":
    main()