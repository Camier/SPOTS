#!/usr/bin/env python3
"""
Reorganize IGN_CONSOLIDATED for optimal structure and efficiency.
Consolidates duplicates, creates clear hierarchy, and optimizes access.
"""

import os
import shutil
from pathlib import Path
import sqlite3
import json

class IGNReorganizer:
    def __init__(self):
        self.base_dir = Path("/home/miko/Development/projects/spots/IGN_CONSOLIDATED")
        self.stats = {
            'removed_duplicates': 0,
            'consolidated_files': 0,
            'created_directories': 0
        }
    
    def create_optimized_structure(self):
        """Create the optimized directory structure."""
        print("Creating optimized structure...")
        
        # New structure
        new_dirs = [
            "01_active_maps",      # Currently used maps
            "02_downloads",        # Active downloads
            "03_cache_recovered",  # Recovered from cache
            "04_scripts",          # All scripts
            "05_projects",         # QGIS projects
            "06_documentation",    # Docs and guides
            "07_archive"          # Old/duplicate files
        ]
        
        for dir_name in new_dirs:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            self.stats['created_directories'] += 1
        
        print(f"✅ Created {len(new_dirs)} directories")
    
    def consolidate_mbtiles(self):
        """Consolidate and organize MBTiles files."""
        print("\nConsolidating MBTiles files...")
        
        # Move active maps
        active_maps = [
            ("offline_tiles/ign_plan.mbtiles", "01_active_maps/"),
            ("offline_tiles/ign_ortho.mbtiles", "01_active_maps/"),
            ("offline_tiles/ign_parcelles.mbtiles", "01_active_maps/"),
            ("offline_tiles/osm.mbtiles", "01_active_maps/"),
            ("cache_recovery/ign_cache_extracted.mbtiles", "03_cache_recovered/")
        ]
        
        for src, dst in active_maps:
            src_path = self.base_dir / src
            if src_path.exists():
                dst_path = self.base_dir / dst / src_path.name
                if not dst_path.exists():
                    shutil.move(str(src_path), str(dst_path))
                    self.stats['consolidated_files'] += 1
                    size_mb = dst_path.stat().st_size / (1024*1024)
                    print(f"  ✓ {src_path.name}: {size_mb:.2f} MB → {dst}")
        
        # Archive empty/duplicate files
        empty_files = [
            "offline_tiles/ign_carte.mbtiles",
            "offline_tiles/ign_scan25.mbtiles",
            "offline_tiles/ortho.mbtiles",
            "offline_tiles/scan25.mbtiles",
            "offline_tiles/plan.mbtiles",
            "cache_recovery/ign_cache_recovered.mbtiles"
        ]
        
        archive_dir = self.base_dir / "07_archive/empty_mbtiles"
        archive_dir.mkdir(exist_ok=True)
        
        for file in empty_files:
            src_path = self.base_dir / file
            if src_path.exists() and src_path.stat().st_size < 25000:  # < 25KB
                dst_path = archive_dir / src_path.name
                if not dst_path.exists():
                    shutil.move(str(src_path), str(dst_path))
                    self.stats['removed_duplicates'] += 1
    
    def organize_scripts(self):
        """Organize scripts by function."""
        print("\nOrganizing scripts...")
        
        script_categories = {
            "download": ["download_*.py"],
            "analysis": ["analyze_*.py", "extract_*.py"],
            "utilities": ["*.py"]  # Catch-all
        }
        
        scripts_dir = self.base_dir / "scripts"
        new_scripts_dir = self.base_dir / "04_scripts"
        
        if scripts_dir.exists():
            for category, patterns in script_categories.items():
                cat_dir = new_scripts_dir / category
                cat_dir.mkdir(exist_ok=True)
                
                for pattern in patterns:
                    for script in scripts_dir.glob(pattern):
                        if script.is_file():
                            dst = cat_dir / script.name
                            if not dst.exists():
                                shutil.copy2(str(script), str(dst))
                                self.stats['consolidated_files'] += 1
    
    def create_master_index(self):
        """Create a master index file."""
        print("\nCreating master index...")
        
        index = {
            "IGN_CONSOLIDATED": {
                "total_size_mb": 0,
                "active_maps": [],
                "downloads_in_progress": [],
                "cache_recovered": [],
                "scripts": {
                    "download": [],
                    "analysis": [],
                    "utilities": []
                },
                "projects": [],
                "statistics": {}
            }
        }
        
        # Scan active maps
        active_dir = self.base_dir / "01_active_maps"
        for mbtiles in active_dir.glob("*.mbtiles"):
            size_mb = mbtiles.stat().st_size / (1024*1024)
            index["IGN_CONSOLIDATED"]["active_maps"].append({
                "name": mbtiles.name,
                "size_mb": round(size_mb, 2),
                "tiles": self.count_tiles(mbtiles)
            })
            index["IGN_CONSOLIDATED"]["total_size_mb"] += size_mb
        
        # Scan cache recovered
        cache_dir = self.base_dir / "03_cache_recovered"
        for mbtiles in cache_dir.glob("*.mbtiles"):
            size_mb = mbtiles.stat().st_size / (1024*1024)
            index["IGN_CONSOLIDATED"]["cache_recovered"].append({
                "name": mbtiles.name,
                "size_mb": round(size_mb, 2),
                "tiles": self.count_tiles(mbtiles)
            })
            index["IGN_CONSOLIDATED"]["total_size_mb"] += size_mb
        
        # Save index
        index_file = self.base_dir / "MASTER_INDEX.json"
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
        
        print(f"✅ Master index created: {index_file}")
        
        # Create README
        self.create_readme(index)
    
    def count_tiles(self, mbtiles_path):
        """Count tiles in an MBTiles file."""
        try:
            conn = sqlite3.connect(str(mbtiles_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tiles")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    def create_readme(self, index):
        """Create an organized README."""
        readme_content = f"""# IGN CONSOLIDATED - Optimized Structure

## 📊 Quick Stats
- **Total Size:** {index['IGN_CONSOLIDATED']['total_size_mb']:.2f} MB
- **Active Maps:** {len(index['IGN_CONSOLIDATED']['active_maps'])}
- **Cache Recovered:** {len(index['IGN_CONSOLIDATED']['cache_recovered'])}

## 📁 Directory Structure

```
IGN_CONSOLIDATED/
├── 01_active_maps/        # Ready-to-use maps
├── 02_downloads/          # Downloads in progress
├── 03_cache_recovered/    # Recovered from cache (241 MB!)
├── 04_scripts/            # Organized scripts
│   ├── download/         # Download scripts
│   ├── analysis/         # Analysis tools
│   └── utilities/        # Other utilities
├── 05_projects/          # QGIS projects
├── 06_documentation/     # Guides and docs
├── 07_archive/           # Old/duplicate files
└── MASTER_INDEX.json     # Complete inventory
```

## 🗺️ Active Maps

"""
        
        for map_info in index['IGN_CONSOLIDATED']['active_maps']:
            readme_content += f"- **{map_info['name']}**: {map_info['size_mb']} MB ({map_info['tiles']:,} tiles)\n"
        
        readme_content += """

## 🚀 Quick Start

```bash
# Launch unified system
python3 launch_ign_system.py

# Continue downloads
python3 04_scripts/download/download_50gb_collection.py

# Open in QGIS
qgis 05_projects/spots_offline_complete.qgz
```

## 📈 Progress to 50GB
Current: {:.2f} MB ({:.3f}%)
Target: 50,000 MB

---
*Optimized structure for maximum efficiency*
""".format(
            index['IGN_CONSOLIDATED']['total_size_mb'],
            (index['IGN_CONSOLIDATED']['total_size_mb']/50000)*100
        )
        
        readme_file = self.base_dir / "README_ORGANIZED.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"✅ README created: {readme_file}")
    
    def cleanup_empty_dirs(self):
        """Remove empty directories."""
        print("\nCleaning up empty directories...")
        
        for dir_path in self.base_dir.rglob("*"):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()
                print(f"  ✓ Removed empty: {dir_path.name}")
    
    def run(self):
        """Execute the reorganization."""
        print("=" * 60)
        print("🔧 IGN CONSOLIDATED REORGANIZATION")
        print("=" * 60)
        
        self.create_optimized_structure()
        self.consolidate_mbtiles()
        self.organize_scripts()
        self.create_master_index()
        self.cleanup_empty_dirs()
        
        print("\n" + "=" * 60)
        print("✅ REORGANIZATION COMPLETE")
        print("=" * 60)
        print(f"📁 Removed duplicates: {self.stats['removed_duplicates']}")
        print(f"📂 Consolidated files: {self.stats['consolidated_files']}")
        print(f"📁 Created directories: {self.stats['created_directories']}")
        
        return self.stats

if __name__ == "__main__":
    reorganizer = IGNReorganizer()
    reorganizer.run()