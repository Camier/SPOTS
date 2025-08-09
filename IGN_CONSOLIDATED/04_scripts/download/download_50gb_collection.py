#!/usr/bin/env python3
"""
Download 50GB IGN tile collection for complete Occitanie coverage.
Expanded areas and zoom levels for comprehensive offline mapping.
"""

import os
import sys
import time
import math
import sqlite3
import requests
from pathlib import Path
from typing import Tuple, List, Dict
from datetime import datetime

class IGN50GBDownloader:
    """Download 50GB of IGN tiles systematically."""
    
    WMTS_BASE = "https://data.geopf.fr/wmts"
    
    LAYERS = {
        'cartes': {
            'layer': 'GEOGRAPHICALGRIDSYSTEMS.MAPS',
            'format': 'image/jpeg',
            'tilematrixset': 'PM',
            'style': 'normal',
            'max_zoom': 18
        },
        'plan': {
            'layer': 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2', 
            'format': 'image/png',
            'tilematrixset': 'PM',
            'style': 'normal',
            'max_zoom': 18
        },
        'ortho': {
            'layer': 'ORTHOIMAGERY.ORTHOPHOTOS',
            'format': 'image/jpeg',
            'tilematrixset': 'PM',
            'style': 'normal',
            'max_zoom': 20
        }
    }
    
    def __init__(self):
        self.base_dir = Path("/home/miko/Development/projects/spots/IGN_CONSOLIDATED/offline_tiles")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize databases
        self.dbs = {}
        for layer_key in self.LAYERS:
            db_path = self.base_dir / f"ign_{layer_key}.mbtiles"
            self.dbs[layer_key] = self._init_mbtiles(db_path, layer_key)
        
        # Global statistics
        self.global_stats = {
            'downloaded': 0,
            'cached': 0,
            'failed': 0,
            'size_mb': 0,
            'start_time': datetime.now()
        }
    
    def _init_mbtiles(self, db_path: Path, layer_key: str) -> sqlite3.Connection:
        """Initialize MBTiles database."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
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
        
        layer = self.LAYERS[layer_key]
        metadata = {
            'name': f'IGN {layer_key.upper()} 50GB Collection',
            'type': 'baselayer',
            'version': '2.0.0',
            'description': f'IGN {layer["layer"]} - Complete Occitanie',
            'format': layer['format'].split('/')[-1],
            'bounds': '-0.5,42.0,4.5,45.0',
            'center': '2.0,43.5,10',
            'minzoom': '8',
            'maxzoom': str(layer['max_zoom']),
            'attribution': '© IGN - 50GB Collection'
        }
        
        for key, value in metadata.items():
            cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
                          (key, value))
        
        conn.commit()
        return conn
    
    def deg2num(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile numbers."""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (x, y)
    
    def download_tile(self, layer_key: str, x: int, y: int, z: int) -> bool:
        """Download a single tile."""
        cursor = self.dbs[layer_key].cursor()
        tms_y = (2 ** z - 1) - y
        
        # Check if exists
        cursor.execute(
            "SELECT COUNT(*) FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, tms_y)
        )
        if cursor.fetchone()[0] > 0:
            self.global_stats['cached'] += 1
            return True
        
        # Build URL
        layer = self.LAYERS[layer_key]
        params = [
            "SERVICE=WMTS",
            "REQUEST=GetTile",
            "VERSION=1.0.0",
            f"LAYER={layer['layer']}",
            f"TILEMATRIXSET={layer['tilematrixset']}",
            f"TILEMATRIX={z}",
            f"TILECOL={x}",
            f"TILEROW={y}",
            f"STYLE={layer['style']}",
            f"FORMAT={layer['format']}"
        ]
        url = f"{self.WMTS_BASE}?{'&'.join(params)}"
        
        try:
            response = requests.get(url, headers={
                'User-Agent': 'SPOTS-50GB/1.0',
                'Referer': 'https://www.geoportail.gouv.fr/'
            }, timeout=10)
            
            if response.status_code == 200 and len(response.content) > 100:
                cursor.execute(
                    "INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                    (z, x, tms_y, response.content)
                )
                self.dbs[layer_key].commit()
                self.global_stats['downloaded'] += 1
                self.global_stats['size_mb'] += len(response.content) / (1024 * 1024)
                return True
        except:
            pass
        
        self.global_stats['failed'] += 1
        return False
    
    def download_region(self, name: str, layer_key: str, bbox: Tuple, zoom_levels: List[int]):
        """Download a complete region."""
        minlon, minlat, maxlon, maxlat = bbox
        
        print(f"\n🗺️ {name} - {layer_key.upper()}")
        print(f"   Bbox: ({minlon:.2f}, {minlat:.2f}, {maxlon:.2f}, {maxlat:.2f})")
        print(f"   Zoom levels: {zoom_levels}")
        
        total_tiles = 0
        for z in zoom_levels:
            x1, y1 = self.deg2num(maxlat, minlon, z)
            x2, y2 = self.deg2num(minlat, maxlon, z)
            
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self.download_tile(layer_key, x, y, z)
                    total_tiles += 1
                    
                    if total_tiles % 100 == 0:
                        current_size = self.global_stats['size_mb']
                        print(f"   Progress: {total_tiles} tiles, {current_size:.2f} MB total")
                        
                        # Stop if we reach 1GB for this session
                        if current_size > 1000:
                            print(f"   ⚠️ Reached 1GB limit for this session")
                            return False
                    
                    # Rate limiting
                    if self.global_stats['downloaded'] % 10 == 9:
                        time.sleep(0.5)
        
        return True
    
    def execute_50gb_plan(self):
        """Execute the 50GB download plan."""
        print("=" * 60)
        print("🚀 IGN 50GB COLLECTION DOWNLOAD")
        print("=" * 60)
        
        # Define the complete download plan
        regions = [
            # Phase 1: Urban centers (High detail)
            {
                'name': 'Toulouse Metropolitan',
                'bbox': (1.20, 43.45, 1.65, 43.75),
                'layers': {
                    'plan': [10, 11, 12, 13, 14, 15],
                    'ortho': [13, 14, 15],
                    'cartes': [10, 11, 12]
                }
            },
            {
                'name': 'Montpellier Metropolitan',
                'bbox': (3.70, 43.50, 4.00, 43.75),
                'layers': {
                    'plan': [10, 11, 12, 13, 14],
                    'ortho': [13, 14]
                }
            },
            # Phase 2: Natural areas
            {
                'name': 'Pyrenees National Parks',
                'bbox': (0.50, 42.50, 2.00, 43.20),
                'layers': {
                    'cartes': [9, 10, 11, 12],
                    'ortho': [12, 13]
                }
            },
            # Phase 3: Regional coverage
            {
                'name': 'Occitanie West',
                'bbox': (-0.50, 42.50, 2.00, 44.50),
                'layers': {
                    'cartes': [8, 9, 10, 11]
                }
            },
            {
                'name': 'Occitanie East',
                'bbox': (2.00, 42.50, 4.50, 44.50),
                'layers': {
                    'cartes': [8, 9, 10, 11]
                }
            }
        ]
        
        # Execute downloads
        for region in regions:
            for layer_key, zoom_levels in region['layers'].items():
                if layer_key in self.LAYERS:
                    continue_download = self.download_region(
                        region['name'], 
                        layer_key, 
                        region['bbox'], 
                        zoom_levels
                    )
                    
                    if not continue_download:
                        break
            
            # Show progress
            self.show_progress()
            
            # Stop if we've downloaded enough for this session
            if self.global_stats['size_mb'] > 1000:
                print("\n⚠️ Reached 1GB session limit. Resume later to continue.")
                break
    
    def show_progress(self):
        """Show download progress."""
        elapsed = (datetime.now() - self.global_stats['start_time']).total_seconds()
        rate = self.global_stats['size_mb'] / (elapsed / 60) if elapsed > 0 else 0
        
        print(f"\n📊 Progress Update:")
        print(f"   Downloaded: {self.global_stats['downloaded']:,} tiles")
        print(f"   Cached: {self.global_stats['cached']:,} tiles")
        print(f"   Failed: {self.global_stats['failed']:,} tiles")
        print(f"   Total size: {self.global_stats['size_mb']:.2f} MB")
        print(f"   Download rate: {rate:.2f} MB/min")
        print(f"   Progress to 50GB: {(self.global_stats['size_mb']/50000)*100:.3f}%")
    
    def get_current_size(self):
        """Calculate total size of all MBTiles."""
        total = 0
        for mbtiles in self.base_dir.glob("*.mbtiles"):
            total += mbtiles.stat().st_size
        return total / (1024 * 1024)

if __name__ == "__main__":
    print("Starting 50GB IGN tile collection download...")
    print("This will download tiles systematically to reach 50GB.")
    print("The process can be interrupted and resumed at any time.")
    
    downloader = IGN50GBDownloader()
    
    # Show current status
    current_size = downloader.get_current_size()
    print(f"\n📁 Current collection size: {current_size:.2f} MB")
    print(f"📊 Progress to 50GB: {(current_size/50000)*100:.3f}%")
    
    # Start download
    print("\n▶️ Starting download (1GB per session)...")
    downloader.execute_50gb_plan()
    
    # Final report
    print("\n" + "=" * 60)
    print("SESSION COMPLETE")
    print("=" * 60)
    downloader.show_progress()
    
    final_size = downloader.get_current_size()
    print(f"\n📁 Final collection size: {final_size:.2f} MB")
    print(f"📊 Progress to 50GB: {(final_size/50000)*100:.3f}%")
    
    if final_size < 50000:
        print("\n💡 Run this script again to continue downloading.")
    else:
        print("\n✅ 50GB collection complete!")