#!/usr/bin/env python3
"""
Process IGN Open Data to enrich Occitanie spots
Uses BDTOPO, RGEALTI, and other IGN datasets
"""

import geopandas as gpd
import rasterio
from shapely.geometry import Point, box
from shapely.ops import nearest_points
import pandas as pd
import numpy as np
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional


class IGNDataProcessor:
    """Process IGN open data for spot enrichment"""
    
    def __init__(self, ign_data_dir: str = "data/ign_opendata"):
        self.data_dir = Path(ign_data_dir)
        self.occitanie_bounds = box(-0.5, 42.0, 4.5, 45.0)
        
        # Department codes for Occitanie
        self.occitanie_depts = [
            "009", "011", "012", "030", "031", "032", "034",
            "046", "048", "065", "066", "081", "082"
        ]
        
    def load_bdtopo_hydro(self, dept: str) -> Optional[gpd.GeoDataFrame]:
        """Load BDTOPO hydrography data for a department"""
        hydro_path = self.data_dir / "BDTOPO" / f"BDTOPO_D{dept}_latest" / "HYDROGRAPHIE.shp"
        
        if hydro_path.exists():
            return gpd.read_file(hydro_path)
        else:
            print(f"⚠️  No BDTOPO hydro data for department {dept}")
            return None
            
    def find_nearest_water(self, lat: float, lon: float, max_distance: float = 1000) -> Dict:
        """Find nearest water feature to a spot"""
        point = Point(lon, lat)
        nearest_water = None
        min_distance = float('inf')
        
        # Check each department's hydro data
        for dept in self.occitanie_depts:
            hydro = self.load_bdtopo_hydro(dept)
            if hydro is None:
                continue
                
            # Filter for significant water bodies
            water_bodies = hydro[hydro['NATURE'].isin([
                'Lac', 'Plan d\'eau', 'Retenue', 'Réservoir',
                'Cours d\'eau', 'Canal', 'Rivière'
            ])]
            
            if water_bodies.empty:
                continue
                
            # Find nearest
            for idx, feature in water_bodies.iterrows():
                dist = point.distance(feature.geometry)
                if dist < min_distance and dist < max_distance:
                    min_distance = dist
                    nearest_water = {
                        'name': feature.get('NOM', 'Unknown'),
                        'type': feature.get('NATURE', 'Unknown'),
                        'distance': round(dist, 1),
                        'department': dept
                    }
                    
        return nearest_water if nearest_water else {'distance': None}
        
    def get_elevation_from_rgealti(self, lat: float, lon: float) -> Optional[float]:
        """Get elevation from RGEALTI raster data"""
        point = Point(lon, lat)
        
        # Find relevant RGEALTI file
        for dept in self.occitanie_depts:
            rgealti_dir = self.data_dir / "RGEALTI" / f"RGEALTI_D{dept}_latest"
            if not rgealti_dir.exists():
                continue
                
            # Look for .tif files
            tif_files = list(rgealti_dir.glob("*.tif"))
            
            for tif_file in tif_files:
                try:
                    with rasterio.open(tif_file) as src:
                        # Check if point is within raster bounds
                        if point.within(box(*src.bounds)):
                            # Sample elevation at point
                            for val in src.sample([(lon, lat)]):
                                return float(val[0])
                except Exception as e:
                    print(f"Error reading {tif_file}: {e}")
                    
        return None
        
    def find_nearby_trails(self, lat: float, lon: float, radius: float = 2000) -> List[Dict]:
        """Find trails and paths from BDTOPO"""
        point = Point(lon, lat)
        nearby_trails = []
        
        for dept in self.occitanie_depts:
            # Look for transportation/paths layer
            transport_path = self.data_dir / "BDTOPO" / f"BDTOPO_D{dept}_latest" / "TRANSPORT.shp"
            
            if transport_path.exists():
                transport = gpd.read_file(transport_path)
                
                # Filter for trails and paths
                trails = transport[transport['NATURE'].isin([
                    'Sentier', 'Chemin', 'Piste cyclable', 'Voie verte'
                ])]
                
                # Find trails within radius
                buffer = point.buffer(radius)
                nearby = trails[trails.intersects(buffer)]
                
                for idx, trail in nearby.iterrows():
                    dist = point.distance(trail.geometry)
                    nearby_trails.append({
                        'type': trail.get('NATURE', 'Unknown'),
                        'name': trail.get('NOM', 'Unnamed trail'),
                        'distance': round(dist, 1),
                        'department': dept
                    })
                    
        return sorted(nearby_trails, key=lambda x: x['distance'])[:5]
        
    def check_forest_coverage(self, lat: float, lon: float) -> Dict:
        """Check if spot is in forest area using BDFORET"""
        point = Point(lon, lat)
        
        for dept in self.occitanie_depts:
            forest_path = self.data_dir / "BDFORET" / f"BDFORET_D{dept}_latest" / "FORMATION_VEGETALE.shp"
            
            if forest_path.exists():
                forests = gpd.read_file(forest_path)
                
                # Check if point is in any forest polygon
                for idx, forest in forests.iterrows():
                    if point.within(forest.geometry):
                        return {
                            'in_forest': True,
                            'forest_type': forest.get('ESSENCE', 'Unknown'),
                            'department': dept
                        }
                        
        return {'in_forest': False}
        
    def enrich_spot_with_ign_data(self, spot: Dict) -> Dict:
        """Enrich a single spot with all available IGN data"""
        lat = spot.get('lat')
        lon = spot.get('lon')
        
        if not lat or not lon:
            return spot
            
        enriched = spot.copy()
        
        print(f"🔍 Enriching: {spot.get('name', 'Unknown')} ({lat}, {lon})")
        
        # Get elevation
        elevation = self.get_elevation_from_rgealti(lat, lon)
        if elevation:
            enriched['elevation_ign'] = round(elevation, 1)
            print(f"  📏 Elevation: {enriched['elevation_ign']}m")
            
        # Find nearest water
        water = self.find_nearest_water(lat, lon)
        if water['distance'] is not None:
            enriched['nearest_water'] = water
            print(f"  💧 Water: {water['name']} ({water['distance']}m)")
            
        # Find nearby trails
        trails = self.find_nearby_trails(lat, lon)
        if trails:
            enriched['nearby_trails'] = trails
            print(f"  🥾 Trails: {len(trails)} found")
            
        # Check forest coverage
        forest = self.check_forest_coverage(lat, lon)
        enriched['forest_info'] = forest
        if forest['in_forest']:
            print(f"  🌲 In forest: {forest['forest_type']}")
            
        return enriched
        
    def batch_enrich_spots(self, spots_file: str, output_file: str):
        """Enrich multiple spots from a JSON file"""
        # Load spots
        with open(spots_file, 'r', encoding='utf-8') as f:
            spots = json.load(f)
            
        print(f"📍 Processing {len(spots)} spots with IGN data...")
        
        enriched_spots = []
        for i, spot in enumerate(spots, 1):
            print(f"\n[{i}/{len(spots)}] Processing...")
            enriched = self.enrich_spot_with_ign_data(spot)
            enriched_spots.append(enriched)
            
        # Save enriched data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_spots, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Saved enriched data to: {output_file}")
        
        # Summary statistics
        spots_with_elevation = sum(1 for s in enriched_spots if 'elevation_ign' in s)
        spots_with_water = sum(1 for s in enriched_spots if s.get('nearest_water', {}).get('distance') is not None)
        spots_with_trails = sum(1 for s in enriched_spots if s.get('nearby_trails'))
        spots_in_forest = sum(1 for s in enriched_spots if s.get('forest_info', {}).get('in_forest'))
        
        print("\n📊 Enrichment Summary:")
        print(f"  Elevation data: {spots_with_elevation}/{len(spots)} spots")
        print(f"  Near water: {spots_with_water}/{len(spots)} spots")
        print(f"  Trail access: {spots_with_trails}/{len(spots)} spots")
        print(f"  In forest: {spots_in_forest}/{len(spots)} spots")


def main():
    """Example usage"""
    processor = IGNDataProcessor()
    
    # Example spot
    test_spot = {
        'name': 'Lac de Salagou',
        'lat': 43.6508,
        'lon': 3.3857,
        'department': '34'
    }
    
    print("🧪 Testing IGN data enrichment...")
    enriched = processor.enrich_spot_with_ign_data(test_spot)
    
    print("\n📋 Enriched data:")
    print(json.dumps(enriched, indent=2, ensure_ascii=False))
    
    # Batch processing example
    # processor.batch_enrich_spots('spots.json', 'spots_enriched_ign.json')


if __name__ == "__main__":
    main()