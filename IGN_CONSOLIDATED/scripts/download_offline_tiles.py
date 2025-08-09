#!/usr/bin/env python3
"""
Download offline IGN tiles for SPOTS Occitanie project.
Implements the 50GB multi-scale strategy for offline map collection.
"""

import os
import sys
import time
import math
import sqlite3
import requests
from pathlib import Path
from typing import Tuple, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

class IGNTileDownloader:
    """Download IGN tiles for offline usage."""
    
    # IGN WMTS endpoints (public access for basic layers)
    WMTS_BASE = "https://wxs.ign.fr/essentiels/geoportail/wmts"
    
    # Layer configurations
    LAYERS = {
        'scan25': {
            'name': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR',
            'format': 'image/jpeg',
            'style': 'normal',
            'tilematrixset': 'PM',
            'max_zoom': 16
        },
        'plan': {
            'name': 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
            'format': 'image/png',
            'style': 'normal',
            'tilematrixset': 'PM',
            'max_zoom': 18
        },
        'ortho': {
            'name': 'ORTHOIMAGERY.ORTHOPHOTOS',
            'format': 'image/jpeg',
            'style': 'normal',
            'tilematrixset': 'PM',
            'max_zoom': 20
        }
    }
    
    def __init__(self, base_dir: str = "/home/miko/Development/projects/spots/offline_tiles"):
        """Initialize the downloader."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create MBTiles databases for each layer
        self.dbs = {}
        for layer_key in self.LAYERS:
            db_path = self.base_dir / f"{layer_key}.mbtiles"
            self.dbs[layer_key] = self._init_mbtiles(db_path, layer_key)
    
    def _init_mbtiles(self, db_path: Path, layer_key: str) -> sqlite3.Connection:
        """Initialize MBTiles database."""
        conn = sqlite3.connect(str(db_path))
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
            'name': f'IGN {layer_key.upper()} Occitanie',
            'type': 'baselayer',
            'version': '1.0.0',
            'description': f'IGN {layer_key} tiles for Occitanie region',
            'format': self.LAYERS[layer_key]['format'].split('/')[-1],
            'bounds': '-0.5,42.0,4.5,45.0',  # Approximate Occitanie bounds
            'center': '2.0,43.5,8',
            'minzoom': '8',
            'maxzoom': str(self.LAYERS[layer_key]['max_zoom'])
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
    
    def get_tile_url(self, layer_key: str, x: int, y: int, z: int) -> str:
        """Generate tile URL for IGN WMTS."""
        layer = self.LAYERS[layer_key]
        params = {
            'SERVICE': 'WMTS',
            'REQUEST': 'GetTile',
            'VERSION': '1.0.0',
            'LAYER': layer['name'],
            'STYLE': layer['style'],
            'TILEMATRIXSET': layer['tilematrixset'],
            'TILEMATRIX': str(z),
            'TILEROW': str(y),
            'TILECOL': str(x),
            'FORMAT': layer['format']
        }
        return f"{self.WMTS_BASE}?{urlencode(params)}"
    
    def download_tile(self, layer_key: str, x: int, y: int, z: int) -> bool:
        """Download a single tile."""
        url = self.get_tile_url(layer_key, x, y, z)
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and len(response.content) > 0:
                # Store in MBTiles (TMS scheme - flip Y)
                tms_y = (2 ** z - 1) - y
                cursor = self.dbs[layer_key].cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                    (z, x, tms_y, response.content)
                )
                self.dbs[layer_key].commit()
                return True
        except Exception as e:
            print(f"Error downloading tile {layer_key} z{z}/{x}/{y}: {e}")
        
        return False
    
    def download_area(self, layer_key: str, bbox: Tuple[float, float, float, float], 
                     zoom_levels: List[int], max_tiles: int = None) -> Dict:
        """Download tiles for an area at specified zoom levels."""
        minlon, minlat, maxlon, maxlat = bbox
        stats = {'downloaded': 0, 'failed': 0, 'skipped': 0, 'size_mb': 0}
        
        print(f"\nDownloading {layer_key} tiles for bbox: {bbox}")
        print(f"Zoom levels: {zoom_levels}")
        
        tasks = []
        for z in zoom_levels:
            x1, y1 = self.deg2num(maxlat, minlon, z)
            x2, y2 = self.deg2num(minlat, maxlon, z)
            
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    # Check if tile already exists
                    cursor = self.dbs[layer_key].cursor()
                    tms_y = (2 ** z - 1) - y
                    cursor.execute(
                        "SELECT COUNT(*) FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
                        (z, x, tms_y)
                    )
                    if cursor.fetchone()[0] > 0:
                        stats['skipped'] += 1
                        continue
                    
                    tasks.append((z, x, y))
                    
                    if max_tiles and len(tasks) >= max_tiles:
                        break
                if max_tiles and len(tasks) >= max_tiles:
                    break
            if max_tiles and len(tasks) >= max_tiles:
                break
        
        print(f"Total tiles to download: {len(tasks)} (skipped {stats['skipped']} existing)")
        
        # Download with thread pool
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.download_tile, layer_key, x, y, z): (z, x, y)
                for z, x, y in tasks
            }
            
            for i, future in enumerate(as_completed(futures), 1):
                z, x, y = futures[future]
                if future.result():
                    stats['downloaded'] += 1
                else:
                    stats['failed'] += 1
                
                if i % 100 == 0:
                    print(f"Progress: {i}/{len(tasks)} tiles...")
        
        # Calculate total size
        cursor = self.dbs[layer_key].cursor()
        cursor.execute("SELECT SUM(LENGTH(tile_data)) FROM tiles")
        total_bytes = cursor.fetchone()[0] or 0
        stats['size_mb'] = total_bytes / (1024 * 1024)
        
        print(f"✅ Downloaded: {stats['downloaded']} tiles")
        print(f"❌ Failed: {stats['failed']} tiles")
        print(f"⏭️  Skipped: {stats['skipped']} tiles")
        print(f"💾 Total size: {stats['size_mb']:.2f} MB")
        
        return stats

    def download_spots_areas(self):
        """Download tiles around spot locations."""
        # Define spot clusters with their bounding boxes
        spot_clusters = [
            # Pyrenees caves cluster
            {'name': 'Pyrenees Caves', 'bbox': (1.0, 42.7, 1.8, 43.1), 'priority': 1},
            # Toulouse urban exploration
            {'name': 'Toulouse Urbex', 'bbox': (1.2, 43.5, 1.6, 43.7), 'priority': 1},
            # Montpellier & Salagou
            {'name': 'Montpellier Area', 'bbox': (3.2, 43.5, 3.9, 43.8), 'priority': 2},
            # Carcassonne area
            {'name': 'Carcassonne', 'bbox': (2.2, 43.1, 2.5, 43.3), 'priority': 2},
            # Lot valley (Padirac, Pech Merle)
            {'name': 'Lot Valley', 'bbox': (1.5, 44.4, 1.9, 44.9), 'priority': 3}
        ]
        
        print("=" * 60)
        print("SPOTS OFFLINE TILE DOWNLOAD PLAN")
        print("=" * 60)
        
        # Phase 1: Base coverage (SCAN25)
        print("\n📍 PHASE 1: Base Coverage (IGN SCAN25)")
        print("-" * 40)
        occitanie_bbox = (-0.5, 42.0, 4.5, 45.0)
        self.download_area('scan25', occitanie_bbox, [8, 9, 10], max_tiles=5000)
        
        # Phase 2: Priority spots detail
        print("\n📍 PHASE 2: Priority Spots Detail")
        print("-" * 40)
        for cluster in spot_clusters:
            if cluster['priority'] == 1:
                print(f"\n🎯 {cluster['name']}:")
                # High detail for priority areas
                self.download_area('plan', cluster['bbox'], [12, 13, 14], max_tiles=2000)
                self.download_area('ortho', cluster['bbox'], [14, 15], max_tiles=1000)
        
        # Phase 3: Secondary areas
        print("\n📍 PHASE 3: Secondary Areas")
        print("-" * 40)
        for cluster in spot_clusters:
            if cluster['priority'] == 2:
                print(f"\n🎯 {cluster['name']}:")
                self.download_area('plan', cluster['bbox'], [11, 12], max_tiles=1000)
        
        # Final statistics
        print("\n" + "=" * 60)
        print("DOWNLOAD COMPLETE - SUMMARY")
        print("=" * 60)
        
        total_size = 0
        for layer_key, conn in self.dbs.items():
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(LENGTH(tile_data)) FROM tiles")
            count, size = cursor.fetchone()
            if size:
                size_mb = size / (1024 * 1024)
                total_size += size_mb
                print(f"{layer_key.upper():8} - {count:6,} tiles - {size_mb:8.2f} MB")
        
        print(f"{'TOTAL':8} - {'-':>6} tiles - {total_size:8.2f} MB")
        print("\n✅ Offline tiles ready for use in QGIS!")
        print(f"📁 Location: {self.base_dir}")

if __name__ == "__main__":
    downloader = IGNTileDownloader()
    
    # Quick test download - small area around Toulouse
    print("Starting test download for Toulouse area...")
    test_bbox = (1.4, 43.5, 1.5, 43.6)  # Small area in Toulouse
    stats = downloader.download_area('plan', test_bbox, [12], max_tiles=20)
    
    if stats['downloaded'] > 0:
        print("\n✅ Test successful! Ready for full download.")
        print("\nTo start full 50GB download, uncomment the line below:")
        print("# downloader.download_spots_areas()")
        
        # Uncomment to start full download:
        # downloader.download_spots_areas()
    else:
        print("\n❌ Test failed. Check network connection and IGN service availability.")