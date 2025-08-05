#!/usr/bin/env python3
"""
Consolidate all SPOTS JSON files into a single deduplicated file.
Handles different JSON structures and removes duplicates based on coordinates and name similarity.
"""

import json
import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import math
from difflib import SequenceMatcher

@dataclass
class Spot:
    """Standardized spot representation"""
    name: str
    latitude: float
    longitude: float
    spot_type: str = "unknown"
    address: str = ""
    confidence: float = 1.0
    verified: bool = False
    source: str = ""
    source_url: str = ""
    elevation: float = None
    description: str = ""
    tags: List[str] = None
    id: int = None
    original_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.original_data is None:
            self.original_data = {}

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon/2) * math.sin(delta_lon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalize_spot(data: Dict[str, Any], source_file: str) -> Spot:
    """Convert various JSON formats to standardized Spot"""
    
    # Handle different coordinate field names
    lat = data.get('latitude') or data.get('lat') or data.get('y')
    lon = data.get('longitude') or data.get('lon') or data.get('lng') or data.get('x')
    
    if lat is None or lon is None:
        raise ValueError(f"Missing coordinates in {source_file}: {data}")
    
    # Handle different name field variations
    name = (data.get('name') or 
            data.get('title') or 
            data.get('spot_name') or 
            data.get('location_name') or 
            "Unknown")
    
    # Handle type field variations
    spot_type = (data.get('type') or 
                data.get('spot_type') or 
                data.get('category') or 
                "unknown")
    
    return Spot(
        name=name,
        latitude=float(lat),
        longitude=float(lon),
        spot_type=spot_type,
        address=data.get('address', ''),
        confidence=float(data.get('confidence', 1.0)),
        verified=bool(data.get('verified', False)),
        source=data.get('source', source_file),
        source_url=data.get('source_url', ''),
        elevation=float(data.get('elevation')) if data.get('elevation') is not None else None,
        description=data.get('description', ''),
        tags=data.get('tags', []) if isinstance(data.get('tags'), list) else [],
        id=data.get('id'),
        original_data=data
    )

def load_all_spots(project_dir: str) -> List[Spot]:
    """Load spots from all JSON files in the project"""
    spots = []
    json_files = glob.glob(os.path.join(project_dir, "**/*.json"), recursive=True)
    
    # Filter out node_modules and package.json files
    json_files = [f for f in json_files if 'node_modules' not in f and 'package.json' not in f]
    
    print(f"Found {len(json_files)} JSON files to process...")
    
    for file_path in json_files:
        print(f"Processing: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_spots = []
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Direct array of spots
                for item in data:
                    try:
                        spot = normalize_spot(item, os.path.basename(file_path))
                        file_spots.append(spot)
                    except (ValueError, KeyError) as e:
                        print(f"  Warning: Skipping invalid spot in {file_path}: {e}")
                        continue
            
            elif isinstance(data, dict):
                # Check for nested spots structure
                if 'spots' in data and isinstance(data['spots'], list):
                    for item in data['spots']:
                        try:
                            spot = normalize_spot(item, os.path.basename(file_path))
                            file_spots.append(spot)
                        except (ValueError, KeyError) as e:
                            print(f"  Warning: Skipping invalid spot in {file_path}: {e}")
                            continue
                else:
                    # Single spot or try to parse as spot
                    try:
                        spot = normalize_spot(data, os.path.basename(file_path))
                        file_spots.append(spot)
                    except (ValueError, KeyError) as e:
                        print(f"  Warning: Could not parse {file_path} as spot data: {e}")
                        continue
            
            spots.extend(file_spots)
            print(f"  Loaded {len(file_spots)} spots")
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  Error reading {file_path}: {e}")
            continue
        except Exception as e:
            print(f"  Unexpected error processing {file_path}: {e}")
            continue
    
    print(f"\nTotal spots loaded: {len(spots)}")
    return spots

def deduplicate_spots(spots: List[Spot], distance_threshold: float = 100.0, name_similarity_threshold: float = 0.8) -> List[Spot]:
    """Remove duplicate spots based on proximity and name similarity"""
    print(f"\nDeduplicating {len(spots)} spots...")
    print(f"Distance threshold: {distance_threshold}m")
    print(f"Name similarity threshold: {name_similarity_threshold}")
    
    deduplicated = []
    duplicates_removed = 0
    
    for i, current_spot in enumerate(spots):
        is_duplicate = False
        
        for existing_spot in deduplicated:
            # Calculate distance
            distance = calculate_distance(
                current_spot.latitude, current_spot.longitude,
                existing_spot.latitude, existing_spot.longitude
            )
            
            # Calculate name similarity
            name_sim = similarity(current_spot.name, existing_spot.name)
            
            # Check if it's a duplicate
            if distance <= distance_threshold and name_sim >= name_similarity_threshold:
                is_duplicate = True
                duplicates_removed += 1
                
                # Merge data from duplicate (keep the one with more data/higher confidence)
                if current_spot.confidence > existing_spot.confidence:
                    # Update existing spot with better data
                    if not existing_spot.verified and current_spot.verified:
                        existing_spot.verified = current_spot.verified
                    if not existing_spot.address and current_spot.address:
                        existing_spot.address = current_spot.address
                    if existing_spot.elevation is None and current_spot.elevation is not None:
                        existing_spot.elevation = current_spot.elevation
                    if not existing_spot.description and current_spot.description:
                        existing_spot.description = current_spot.description
                    existing_spot.tags.extend([tag for tag in current_spot.tags if tag not in existing_spot.tags])
                
                print(f"  Duplicate found: '{current_spot.name}' ~= '{existing_spot.name}' ({distance:.1f}m, {name_sim:.2f} similarity)")
                break
        
        if not is_duplicate:
            deduplicated.append(current_spot)
    
    print(f"Removed {duplicates_removed} duplicates")
    print(f"Final count: {len(deduplicated)} unique spots")
    
    return deduplicated

def export_consolidated_spots(spots: List[Spot], output_file: str):
    """Export consolidated spots to JSON file"""
    
    # Convert spots back to dictionaries
    export_data = []
    
    for i, spot in enumerate(spots, 1):
        spot_dict = {
            "id": i,
            "name": spot.name,
            "latitude": spot.latitude,
            "longitude": spot.longitude,
            "type": spot.spot_type,
            "address": spot.address,
            "confidence": spot.confidence,
            "verified": spot.verified,
            "source": spot.source,
        }
        
        # Add optional fields if they exist
        if spot.source_url:
            spot_dict["source_url"] = spot.source_url
        if spot.elevation is not None:
            spot_dict["elevation"] = spot.elevation
        if spot.description:
            spot_dict["description"] = spot.description
        if spot.tags:
            spot_dict["tags"] = spot.tags
        
        export_data.append(spot_dict)
    
    # Create metadata wrapper
    consolidated_data = {
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "total_spots": len(spots),
            "consolidation_info": {
                "description": "Consolidated and deduplicated spots from all JSON files",
                "distance_threshold_meters": 100.0,
                "name_similarity_threshold": 0.8
            }
        },
        "spots": export_data
    }
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nConsolidated spots exported to: {output_file}")

def main():
    project_dir = "/home/miko/projects/spots"
    output_file = os.path.join(project_dir, "consolidated_spots.json")
    
    print("SPOTS Consolidation and Deduplication Tool")
    print("=" * 50)
    
    # Load all spots
    all_spots = load_all_spots(project_dir)
    
    if not all_spots:
        print("No spots found to consolidate!")
        return
    
    # Deduplicate
    unique_spots = deduplicate_spots(all_spots)
    
    # Export
    export_consolidated_spots(unique_spots, output_file)
    
    print(f"\nConsolidation complete!")
    print(f"Original spots: {len(all_spots)}")
    print(f"Unique spots: {len(unique_spots)}")
    print(f"Duplicates removed: {len(all_spots) - len(unique_spots)}")

if __name__ == "__main__":
    main()