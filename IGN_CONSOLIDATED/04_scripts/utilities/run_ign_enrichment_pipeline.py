#!/usr/bin/env python3
"""
Run the complete IGN data enrichment pipeline for Instagram spots
Downloads IGN data and enriches spots with geographic information
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.process_ign_data_for_spots import IGNDataProcessor


def download_ign_data():
    """Download IGN data for key departments"""
    print("\n🚀 Starting IGN data download...")
    print("=" * 60)
    
    # We'll download data for departments with spots
    # From our data: 34 (Hérault), 65 (Hautes-Pyrénées)
    departments = ["034", "065"]
    
    # Use geoplateforme.fr URLs instead of deprecated wxs.ign.fr
    # Based on geotribu tool patterns
    base_urls = {
        "BDTOPO": "https://data.geopf.fr/telechargement/download/BDTOPO",
        "RGEALTI": "https://data.geopf.fr/telechargement/download/RGEALTI"
    }
    
    for product, base_url in base_urls.items():
        for dept in departments:
            # Try different URL patterns
            url_patterns = [
                f"{base_url}/{product}_3-3_SHP_LAMB93_D{dept}_2024-03-15/{product}_3-3_SHP_LAMB93_D{dept}_2024-03-15.7z",
                f"{base_url}/{product}_1-0_SHP_LAMB93_D{dept}_2024-01-01/{product}_1-0_SHP_LAMB93_D{dept}_2024-01-01.7z",
                f"https://wxs.ign.fr/{product.lower()}/telechargement/prepackage/{product}_D{dept}_latest.7z"
            ]
            
            output_file = f"data/ign_opendata/{product}/{product}_D{dept}_latest.7z"
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            print(f"\n📥 Downloading {product} for department {dept}...")
            
            downloaded = False
            for url in url_patterns:
                print(f"   Trying: {url}")
                cmd = ["wget", "-c", "--timeout=30", "--tries=1", url, "-O", output_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"   ✅ Downloaded: {output_file}")
                    downloaded = True
                    break
                    
            if not downloaded:
                print(f"   ⚠️  Failed to download {product} for dept {dept}")
                
    print("\n✅ Download phase complete!")
    

def extract_ign_data():
    """Extract downloaded 7z archives"""
    print("\n📦 Extracting IGN data archives...")
    
    ign_dir = Path("data/ign_opendata")
    archives = list(ign_dir.glob("**/*.7z"))
    
    if not archives:
        print("   ⚠️  No archives found to extract")
        return
        
    for archive in archives:
        extract_dir = archive.parent / archive.stem
        
        if extract_dir.exists():
            print(f"   ⏭️  Already extracted: {archive.name}")
            continue
            
        print(f"   📂 Extracting: {archive.name}")
        extract_dir.mkdir(exist_ok=True)
        
        cmd = ["7z", "x", "-y", f"-o{extract_dir}", str(archive)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Extracted to: {extract_dir}")
        else:
            print(f"   ❌ Extract failed: {result.stderr}")
            

def enrich_spots():
    """Enrich Instagram spots with IGN data"""
    print("\n🔍 Enriching spots with IGN data...")
    print("=" * 60)
    
    # Initialize processor
    processor = IGNDataProcessor()
    
    # Load Instagram spots
    spots_file = "exports/instagram_spots_20250803_195033.json"
    with open(spots_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    spots = data['spots']
    print(f"📍 Processing {len(spots)} spots...")
    
    # Convert to format expected by processor
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
    
    # Process each spot
    enriched_spots = []
    for i, spot in enumerate(spots_for_processing, 1):
        print(f"\n[{i}/{len(spots_for_processing)}] Processing {spot['name']}...")
        enriched = processor.enrich_spot_with_ign_data(spot)
        enriched_spots.append(enriched)
        
    # Save enriched data
    output_file = f"exports/instagram_spots_enriched_ign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_data = {
        'export_date': datetime.now().isoformat(),
        'total_spots': len(enriched_spots),
        'enrichment_source': 'IGN Open Data',
        'spots': enriched_spots
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Enriched data saved to: {output_file}")
    
    # Print summary
    print("\n📊 Enrichment Summary:")
    print("=" * 40)
    
    spots_with_elevation = sum(1 for s in enriched_spots if 'elevation_ign' in s)
    spots_with_water = sum(1 for s in enriched_spots if s.get('nearest_water', {}).get('distance') is not None)
    spots_with_trails = sum(1 for s in enriched_spots if s.get('nearby_trails'))
    spots_in_forest = sum(1 for s in enriched_spots if s.get('forest_info', {}).get('in_forest'))
    
    print(f"  📏 Elevation data: {spots_with_elevation}/{len(enriched_spots)} spots")
    print(f"  💧 Near water: {spots_with_water}/{len(enriched_spots)} spots")
    print(f"  🥾 Trail access: {spots_with_trails}/{len(enriched_spots)} spots")
    print(f"  🌲 In forest: {spots_in_forest}/{len(enriched_spots)} spots")
    
    # Show sample enriched spot
    if enriched_spots:
        print("\n📋 Sample enriched spot:")
        sample = enriched_spots[0]
        print(json.dumps(sample, indent=2, ensure_ascii=False))


def main():
    """Run the complete pipeline"""
    print("🗺️ IGN Data Enrichment Pipeline for Occitanie Spots")
    print("=" * 60)
    
    # Check dependencies
    print("\n🔧 Checking dependencies...")
    
    # Check for 7z
    result = subprocess.run(["which", "7z"], capture_output=True)
    if result.returncode != 0:
        print("❌ 7z not found. Please install: sudo apt install p7zip-full")
        return
        
    # Check for required Python packages
    try:
        import geopandas
        import rasterio
        print("✅ All dependencies found")
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        print("Install with: pip install geopandas rasterio")
        return
        
    # Run pipeline stages
    try:
        # Stage 1: Download (skip if data exists)
        ign_dir = Path("data/ign_opendata")
        if not any(ign_dir.glob("**/*.7z")):
            download_ign_data()
        else:
            print("\n⏭️  IGN data already downloaded")
            
        # Stage 2: Extract
        extract_ign_data()
        
        # Stage 3: Enrich spots
        enrich_spots()
        
        print("\n🎉 Pipeline completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()