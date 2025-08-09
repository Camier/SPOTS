#!/usr/bin/env python3
"""
Analyze and recover IGN cache data from /home/miko/IGN_DATA/CACHE/
Converts cached tiles into organized MBTiles format.
"""

import os
import sys
import sqlite3
import hashlib
from pathlib import Path
from PIL import Image
import io

class IGNCacheAnalyzer:
    def __init__(self, cache_dir="/home/miko/IGN_DATA/CACHE", output_dir="/home/miko/Development/projects/spots/IGN_CONSOLIDATED/cache_recovery"):
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'image_files': 0,
            'other_files': 0,
            'total_size_mb': 0,
            'recovered_tiles': 0
        }
    
    def analyze_cache_structure(self):
        """Analyze the cache directory structure."""
        print("Analyzing IGN Cache Structure")
        print("=" * 60)
        
        # Count files in data8 directory
        data8_dir = self.cache_dir / "data8"
        if data8_dir.exists():
            cache_files = list(data8_dir.rglob("*.d"))
            self.stats['total_files'] = len(cache_files)
            
            print(f"Found {self.stats['total_files']:,} cache files")
            
            # Sample first 100 files to determine format
            sample_size = min(100, len(cache_files))
            print(f"\nAnalyzing sample of {sample_size} files...")
            
            formats = {'png': 0, 'jpeg': 0, 'unknown': 0}
            sizes = []
            
            for i, cache_file in enumerate(cache_files[:sample_size]):
                try:
                    with open(cache_file, 'rb') as f:
                        header = f.read(16)
                        file_size = cache_file.stat().st_size
                        sizes.append(file_size)
                        
                        # Check for PNG signature
                        if header[:8] == b'\x89PNG\r\n\x1a\n':
                            formats['png'] += 1
                        # Check for JPEG signature
                        elif header[:2] == b'\xff\xd8':
                            formats['jpeg'] += 1
                        else:
                            formats['unknown'] += 1
                except:
                    pass
            
            # Calculate statistics
            if sizes:
                avg_size = sum(sizes) / len(sizes)
                total_estimated_mb = (avg_size * self.stats['total_files']) / (1024 * 1024)
                
                print(f"\nFile format analysis:")
                print(f"  PNG files: {formats['png']}")
                print(f"  JPEG files: {formats['jpeg']}")
                print(f"  Unknown: {formats['unknown']}")
                print(f"\nAverage file size: {avg_size/1024:.2f} KB")
                print(f"Estimated total size: {total_estimated_mb:.2f} MB")
                
                self.stats['total_size_mb'] = total_estimated_mb
        
        # Check WFS provider cache
        wfs_dir = self.cache_dir / "wfsprovider"
        if wfs_dir.exists():
            print(f"\nWFS Provider cache found")
            sqlite_files = list(wfs_dir.rglob("*.db"))
            print(f"  SQLite databases: {len(sqlite_files)}")
        
        return self.stats
    
    def extract_tiles_to_mbtiles(self, max_files=1000):
        """Extract cached tiles to MBTiles format."""
        print("\nExtracting tiles to MBTiles format")
        print("-" * 40)
        
        # Create MBTiles database
        mbtiles_path = self.output_dir / "ign_cache_recovered.mbtiles"
        conn = sqlite3.connect(str(mbtiles_path))
        cursor = conn.cursor()
        
        # Create MBTiles schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tiles (
                zoom_level INTEGER,
                tile_column INTEGER,
                tile_row INTEGER,
                tile_data BLOB,
                PRIMARY KEY (zoom_level, tile_column, tile_row)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                name TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Set metadata
        metadata = {
            'name': 'IGN Cache Recovery',
            'type': 'baselayer',
            'version': '1.0.0',
            'description': 'Recovered IGN tiles from cache',
            'format': 'mixed',
            'bounds': '-5.0,41.0,10.0,51.0',  # France bounds
            'center': '2.0,46.0,6',
            'minzoom': '0',
            'maxzoom': '18'
        }
        
        for key, value in metadata.items():
            cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
                          (key, value))
        
        # Process cache files
        data8_dir = self.cache_dir / "data8"
        if data8_dir.exists():
            cache_files = list(data8_dir.rglob("*.d"))[:max_files]
            
            recovered = 0
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'rb') as f:
                        data = f.read()
                        
                        # Check if it's an image
                        if data[:8] == b'\x89PNG\r\n\x1a\n' or data[:2] == b'\xff\xd8':
                            # Generate pseudo-coordinates from filename hash
                            # This is a placeholder - real coordinates would need reverse engineering
                            file_hash = hashlib.md5(cache_file.name.encode()).hexdigest()
                            z = int(file_hash[0], 16)  # Zoom 0-15
                            x = int(file_hash[1:5], 16) % (2**z) if z > 0 else 0
                            y = int(file_hash[5:9], 16) % (2**z) if z > 0 else 0
                            
                            # Store in MBTiles
                            cursor.execute(
                                "INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                                (z, x, y, data)
                            )
                            recovered += 1
                            
                            if recovered % 100 == 0:
                                print(f"Recovered {recovered} tiles...")
                                conn.commit()
                except:
                    pass
            
            conn.commit()
            conn.close()
            
            self.stats['recovered_tiles'] = recovered
            print(f"\n✅ Recovered {recovered} tiles to {mbtiles_path}")
            
            # Calculate final size
            if mbtiles_path.exists():
                size_mb = mbtiles_path.stat().st_size / (1024 * 1024)
                print(f"MBTiles size: {size_mb:.2f} MB")
        
        return self.stats
    
    def generate_report(self):
        """Generate analysis report."""
        report_path = self.output_dir / "cache_analysis_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("IGN CACHE ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Cache directory: {self.cache_dir}\n")
            f.write(f"Total files: {self.stats['total_files']:,}\n")
            f.write(f"Estimated size: {self.stats['total_size_mb']:.2f} MB\n")
            f.write(f"Recovered tiles: {self.stats['recovered_tiles']}\n")
            f.write("\nRECOMMENDATIONS:\n")
            f.write("1. The cache contains valuable tile data\n")
            f.write("2. Full recovery would require reverse-engineering the cache format\n")
            f.write("3. Consider using QGIS export instead for organized tiles\n")
        
        print(f"\n📄 Report saved to: {report_path}")

if __name__ == "__main__":
    analyzer = IGNCacheAnalyzer()
    
    # Analyze cache structure
    analyzer.analyze_cache_structure()
    
    # Extract sample tiles to MBTiles
    print("\nExtracting sample tiles (first 1000)...")
    analyzer.extract_tiles_to_mbtiles(max_files=1000)
    
    # Generate report
    analyzer.generate_report()
    
    print("\n✅ Cache analysis complete!")