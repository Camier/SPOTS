#!/usr/bin/env python3
"""Examples of downloading IGN datasets for the SPOTS project"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from backend.scrapers.ign_downloader import IGNDatasetDownloader, download_ign_dataset, list_ign_datasets


def example_1_toulouse_communes():
    """Download administrative boundaries for Toulouse area"""
    print("\n=== Example 1: Toulouse Communes ===")
    
    path = download_ign_dataset(
        dataset_id="ADMINEXPRESS-COG-CARTO.LATEST:commune",
        bbox=[1.2, 43.5, 1.5, 43.7],  # Toulouse bbox
        format="geojson"
    )
    
    print(f"Downloaded Toulouse communes to: {path}")
    return path


def example_2_occitanie_departments():
    """Download all departments in Occitanie"""
    print("\n=== Example 2: Occitanie Departments ===")
    
    downloader = IGNDatasetDownloader()
    path = downloader.download_occitanie_boundaries(level="departement")
    
    print(f"Downloaded Occitanie departments to: {path}")
    return path


def example_3_protected_areas():
    """Download protected areas for a specific region"""
    print("\n=== Example 3: Protected Areas ===")
    
    # Pyrénées area
    path = download_ign_dataset(
        dataset_id="PROTECTEDAREAS.ALL",
        bbox=[0.0, 42.5, 3.0, 43.5],  # Pyrénées bbox
        format="geojson"
    )
    
    print(f"Downloaded protected areas to: {path}")
    return path


def example_4_hydrography():
    """Download water features (rivers, lakes)"""
    print("\n=== Example 4: Hydrography ===")
    
    # Area around Toulouse
    path = download_ign_dataset(
        dataset_id="HYDROGRAPHIE.THEME",
        bbox=[1.0, 43.3, 1.8, 43.8],
        format="geojson"
    )
    
    print(f"Downloaded hydrography to: {path}")
    return path


def example_5_forest_inventory():
    """Download forest data"""
    print("\n=== Example 5: Forest Inventory ===")
    
    # Montagne Noire area
    path = download_ign_dataset(
        dataset_id="LANDCOVER.FORESTINVENTORY.V2",
        bbox=[2.0, 43.3, 2.5, 43.6],
        format="geojson"
    )
    
    print(f"Downloaded forest data to: {path}")
    return path


def example_6_roads_network():
    """Download road network"""
    print("\n=== Example 6: Road Network ===")
    
    # Small area for testing
    path = download_ign_dataset(
        dataset_id="BDTOPO_V3:troncon_de_route",
        bbox=[1.4, 43.6, 1.45, 43.65],  # Small area in Toulouse
        format="geojson"
    )
    
    print(f"Downloaded road network to: {path}")
    return path


def integrate_with_spots():
    """Example of how to integrate downloaded data with SPOTS database"""
    print("\n=== Integration Example ===")
    
    # Download communes
    communes_path = download_ign_dataset(
        dataset_id="ADMINEXPRESS-COG-CARTO.LATEST:commune",
        bbox=[1.3, 43.5, 1.5, 43.7],
        format="geojson"
    )
    
    # Load the GeoJSON
    import json
    with open(communes_path) as f:
        communes_data = json.load(f)
    
    print(f"\nDownloaded {len(communes_data['features'])} communes")
    
    # Example: Find which commune each spot belongs to
    # This would use spatial queries with the spots database
    print("\nYou can now use this data to:")
    print("- Find which commune each spot belongs to")
    print("- Calculate distances to administrative boundaries")
    print("- Filter spots by administrative region")
    print("- Create choropleth maps by commune")
    
    return communes_data


def download_all_occitanie_data():
    """Download comprehensive dataset for Occitanie region"""
    print("\n=== Downloading All Occitanie Data ===")
    
    downloader = IGNDatasetDownloader(download_dir="data/ign_downloads/occitanie")
    
    datasets_to_download = [
        ("ADMINEXPRESS-COG-CARTO.LATEST:region", "regions"),
        ("ADMINEXPRESS-COG-CARTO.LATEST:departement", "departments"),
        ("PROTECTEDAREAS.ALL", "protected_areas"),
        ("HYDROGRAPHIE.THEME", "water_features"),
        ("LANDCOVER.FORESTINVENTORY.V2", "forests")
    ]
    
    occitanie_bbox = [-0.5, 42.5, 4.5, 45.0]
    downloaded_files = []
    
    for dataset_id, name in datasets_to_download:
        try:
            print(f"\nDownloading {name}...")
            path = downloader.download_dataset(
                dataset_id=dataset_id,
                bbox=occitanie_bbox,
                format="geojson",
                output_file=f"occitanie_{name}.geojson"
            )
            downloaded_files.append(path)
            print(f"✓ Downloaded {name}")
        except Exception as e:
            print(f"✗ Error downloading {name}: {e}")
    
    print(f"\n✅ Downloaded {len(downloaded_files)} datasets to: {downloader.download_dir}")
    return downloaded_files


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="IGN data download examples")
    parser.add_argument("--example", type=int, help="Run specific example (1-6)")
    parser.add_argument("--list", action="store_true", help="List available datasets")
    parser.add_argument("--all", action="store_true", help="Download all Occitanie data")
    parser.add_argument("--integrate", action="store_true", help="Show integration example")
    
    args = parser.parse_args()
    
    if args.list:
        list_ign_datasets()
    elif args.all:
        download_all_occitanie_data()
    elif args.integrate:
        integrate_with_spots()
    elif args.example:
        examples = {
            1: example_1_toulouse_communes,
            2: example_2_occitanie_departments,
            3: example_3_protected_areas,
            4: example_4_hydrography,
            5: example_5_forest_inventory,
            6: example_6_roads_network
        }
        
        if args.example in examples:
            examples[args.example]()
        else:
            print(f"Unknown example: {args.example}")
    else:
        # Run all examples
        print("IGN Dataset Download Examples")
        print("=" * 50)
        
        example_1_toulouse_communes()
        example_2_occitanie_departments()
        example_3_protected_areas()
        
        print("\n\nTo run a specific example:")
        print("  python download_ign_data.py --example 1")
        print("\nTo list all available datasets:")
        print("  python download_ign_data.py --list")
        print("\nTo download all Occitanie data:")
        print("  python download_ign_data.py --all")