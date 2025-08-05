#!/usr/bin/env python3
import json
import glob
from pathlib import Path

def convert_spots_to_geojson(input_file):
    """Convert SPOTS JSON to GeoJSON format"""
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    features = []
    for spot in data.get('spots', []):
        # Skip spots without valid coordinates
        if not spot.get('coordinates') or spot['coordinates'].get('lat') is None:
            continue
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [spot['coordinates']['lon'], spot['coordinates']['lat']]
            },
            "properties": {
                "name": spot.get('name', 'Unknown'),
                "department": spot.get('department', ''),
                "caption": spot.get('caption', ''),
                "activities": ', '.join(spot.get('activities', [])),
                "type": spot.get('type', 'unknown'),
                "collected_at": spot.get('collected_at', ''),
                "source": data.get('source', 'Unknown')
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Save GeoJSON
    output_file = input_file.replace('.json', '.geojson')
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    return output_file, len(features)

# Convert all spots files
exports_dir = Path('/home/miko/projects/spots/exports')
converted_files = []

for json_file in exports_dir.glob('*_spots_*.json'):
    try:
        output_file, count = convert_spots_to_geojson(str(json_file))
        converted_files.append((output_file, count))
        print(f"Converted {json_file.name} -> {Path(output_file).name} ({count} features)")
    except Exception as e:
        print(f"Error converting {json_file.name}: {e}")

print(f"\nTotal files converted: {len(converted_files)}")