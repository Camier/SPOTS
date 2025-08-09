#!/usr/bin/env python3
"""
Unified IGN System Launcher
Central access point for all IGN data and operations.
"""

import os
import sys
from pathlib import Path
import subprocess

class IGNSystemLauncher:
    def __init__(self):
        self.base_dir = Path("/home/miko/Development/projects/spots/IGN_CONSOLIDATED")
        self.cache_dir = Path("/home/miko/IGN_DATA/CACHE")
        
    def show_menu(self):
        """Display main menu."""
        print("\n" + "=" * 60)
        print("🗺️  IGN CONSOLIDATED SYSTEM")
        print("=" * 60)
        print("\n📊 Current Status:")
        self.show_status()
        
        print("\n📋 Available Operations:")
        print("1. Open QGIS with offline project")
        print("2. Continue tile downloads")
        print("3. Analyze cache (848 MB available)")
        print("4. View inventory")
        print("5. Export maps")
        print("6. Show statistics")
        print("0. Exit")
        
        return input("\nSelect operation (0-6): ")
    
    def show_status(self):
        """Show system status."""
        # Count MBTiles
        mbtiles_dir = self.base_dir / "offline_tiles"
        mbtiles_files = list(mbtiles_dir.glob("*.mbtiles"))
        total_size = sum(f.stat().st_size for f in mbtiles_files) / (1024*1024)
        
        print(f"  • Offline tiles: {len(mbtiles_files)} files, {total_size:.2f} MB")
        print(f"  • Cache available: 848 MB (10,401 files)")
        print(f"  • QGIS projects: 9 configurations")
        print(f"  • Coverage: Toulouse, Montpellier, Pyrenees, Carcassonne")
    
    def open_qgis_project(self):
        """Open QGIS with the consolidated project."""
        project_file = self.base_dir / "projects/spots_offline_complete.qgz"
        if project_file.exists():
            print(f"\n🚀 Launching QGIS with {project_file.name}...")
            subprocess.run(["qgis", str(project_file)], stderr=subprocess.DEVNULL)
        else:
            print("❌ Project file not found")
    
    def continue_downloads(self):
        """Continue tile downloads."""
        script = self.base_dir / "scripts/download_ign_wmts.py"
        if script.exists():
            print("\n📥 Starting tile download...")
            subprocess.run(["python3", str(script)])
        else:
            print("❌ Download script not found")
    
    def analyze_cache(self):
        """Analyze and recover cache."""
        script = self.base_dir / "scripts/analyze_ign_cache.py"
        if script.exists():
            print("\n🔍 Analyzing 848 MB cache...")
            subprocess.run(["python3", str(script)])
        else:
            print("❌ Analysis script not found")
    
    def view_inventory(self):
        """Display inventory."""
        inventory = self.base_dir / "documentation/IGN_INVENTORY.md"
        if inventory.exists():
            with open(inventory, 'r') as f:
                content = f.read()
            print("\n" + content[:2000] + "\n...\n[Full document at: " + str(inventory) + "]")
        else:
            print("❌ Inventory not found")
    
    def export_maps(self):
        """Export maps interface."""
        print("\n📤 Export Options:")
        print("1. Export as PDF")
        print("2. Export as GeoPackage")
        print("3. Export as Web Map")
        print("\nFeature coming soon...")
    
    def show_statistics(self):
        """Show detailed statistics."""
        print("\n📈 Detailed Statistics")
        print("-" * 40)
        
        # MBTiles details
        mbtiles_dir = self.base_dir / "offline_tiles"
        print("\nMBTiles Files:")
        for mbtiles in sorted(mbtiles_dir.glob("*.mbtiles")):
            size_mb = mbtiles.stat().st_size / (1024*1024)
            print(f"  • {mbtiles.name:25} {size_mb:7.2f} MB")
        
        # Cache statistics
        if self.cache_dir.exists():
            cache_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file())
            cache_size_mb = cache_size / (1024*1024)
            cache_files = sum(1 for _ in self.cache_dir.rglob("*.d"))
            print(f"\nCache Statistics:")
            print(f"  • Total size: {cache_size_mb:.2f} MB")
            print(f"  • Cache files: {cache_files:,}")
        
        # Project count
        projects = list((self.base_dir / "projects").glob("*.qgz"))
        print(f"\nQGIS Projects: {len(projects)}")
        
        # Download progress
        target_gb = 50
        current_mb = sum(f.stat().st_size for f in mbtiles_dir.glob("*.mbtiles")) / (1024*1024)
        progress = (current_mb / (target_gb * 1024)) * 100
        print(f"\nDownload Progress:")
        print(f"  • Current: {current_mb:.2f} MB")
        print(f"  • Target: {target_gb} GB")
        print(f"  • Progress: {progress:.3f}%")
    
    def run(self):
        """Main loop."""
        while True:
            choice = self.show_menu()
            
            if choice == '0':
                print("\n👋 Exiting IGN System")
                break
            elif choice == '1':
                self.open_qgis_project()
            elif choice == '2':
                self.continue_downloads()
            elif choice == '3':
                self.analyze_cache()
            elif choice == '4':
                self.view_inventory()
            elif choice == '5':
                self.export_maps()
            elif choice == '6':
                self.show_statistics()
            else:
                print("❌ Invalid option")

if __name__ == "__main__":
    launcher = IGNSystemLauncher()
    launcher.run()