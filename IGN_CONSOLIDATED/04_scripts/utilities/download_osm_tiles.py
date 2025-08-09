#!/usr/bin/env python3
"""
Download OpenStreetMap tiles for offline usage as fallback.
Since IGN requires authentication, we'll use OSM for the base layer.
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

class OSMTileDownloader:
    """Download OSM tiles for offline usage."""
    
    def __init__(self, base_dir: str = "/home/miko/Development/projects/spots/offline_tiles"):
        """Initialize the downloader."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create MBTiles database
        self.db_path = self.base_dir / "osm.mbtiles"
        self.conn = self._init_mbtiles()
    
    def _init_mbtiles(self) -> sqlite3.Connection:
        """Initialize MBTiles database."""
        conn = sqlite3.connect(str(self.db_path))
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
            'name': 'OSM Occitanie',
            'type': 'baselayer',
            'version': '1.0.0',
            'description': 'OpenStreetMap tiles for Occitanie region',
            'format': 'png',
            'bounds': '-0.5,42.0,4.5,45.0',
            'center': '2.0,43.5,8',
            'minzoom': '8',
            'maxzoom': '16'
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
    
    def download_tile(self, x: int, y: int, z: int) -> bool:
        """Download a single tile from OSM."""
        # Use multiple tile servers for load balancing
        servers = ['a', 'b', 'c']
        server = servers[hash(f"{x},{y},{z}") % len(servers)]
        url = f"https://{server}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        
        headers = {
            'User-Agent': 'SPOTS-QGIS-Offline/1.0'
        }
        
        try:
            # Check if tile already exists
            cursor = self.conn.cursor()
            tms_y = (2 ** z - 1) - y
            cursor.execute(
                "SELECT COUNT(*) FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
                (z, x, tms_y)
            )
            if cursor.fetchone()[0] > 0:
                return True  # Already have it
            
            # Download the tile
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200 and len(response.content) > 0:
                # Store in MBTiles (TMS scheme - flip Y)
                cursor.execute(
                    "INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                    (z, x, tms_y, response.content)
                )
                self.conn.commit()
                time.sleep(0.5)  # Be nice to OSM servers
                return True
            
        except Exception as e:
            print(f"Error downloading tile z{z}/{x}/{y}: {e}")
        
        return False
    
    def download_area(self, bbox: Tuple[float, float, float, float], 
                     zoom_levels: List[int], max_tiles: int = None) -> Dict:
        """Download tiles for an area at specified zoom levels."""
        minlon, minlat, maxlon, maxlat = bbox
        stats = {'downloaded': 0, 'failed': 0, 'skipped': 0, 'size_mb': 0}
        
        print(f"\nDownloading OSM tiles for bbox: {bbox}")
        print(f"Zoom levels: {zoom_levels}")
        
        total_tiles = 0
        for z in zoom_levels:
            x1, y1 = self.deg2num(maxlat, minlon, z)
            x2, y2 = self.deg2num(minlat, maxlon, z)
            
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    if self.download_tile(x, y, z):
                        stats['downloaded'] += 1
                    else:
                        stats['failed'] += 1
                    
                    total_tiles += 1
                    if total_tiles % 10 == 0:
                        print(f"Progress: {total_tiles} tiles processed...")
                    
                    if max_tiles and total_tiles >= max_tiles:
                        break
                if max_tiles and total_tiles >= max_tiles:
                    break
            if max_tiles and total_tiles >= max_tiles:
                break
        
        # Calculate total size
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(LENGTH(tile_data)) FROM tiles")
        total_bytes = cursor.fetchone()[0] or 0
        stats['size_mb'] = total_bytes / (1024 * 1024)
        
        print(f"\n✅ Downloaded: {stats['downloaded']} tiles")
        print(f"❌ Failed: {stats['failed']} tiles")
        print(f"💾 Total size: {stats['size_mb']:.2f} MB")
        
        return stats

    def download_spots_areas(self):
        """Download tiles around spot locations with conservative limits."""
        # Key spot areas in Occitanie
        spot_areas = [
            {'name': 'Toulouse', 'center': (43.6, 1.44), 'radius': 0.1},
            {'name': 'Montpellier', 'center': (43.61, 3.88), 'radius': 0.1},
            {'name': 'Pyrenees Caves', 'center': (42.82, 1.59), 'radius': 0.05}
        ]
        
        print("=" * 60)
        print("OSM OFFLINE TILE DOWNLOAD")
        print("=" * 60)
        
        for area in spot_areas:
            lat, lon = area['center']
            r = area['radius']
            bbox = (lon - r, lat - r, lon + r, lat + r)
            
            print(f"\n📍 Downloading {area['name']} area...")
            self.download_area(bbox, [12, 13, 14], max_tiles=50)
        
        print("\n✅ Download complete!")
        print(f"📁 MBTiles file: {self.db_path}")

if __name__ == "__main__":
    downloader = OSMTileDownloader()
    
    # Test with very small area
    print("Starting minimal test download...")
    test_bbox = (1.43, 43.59, 1.45, 43.61)  # Tiny area in Toulouse
    stats = downloader.download_area(test_bbox, [12], max_tiles=5)
    
    if stats['downloaded'] > 0:
        print("\n✅ Test successful!")
        print("Starting full download...")
        downloader.download_spots_areas()
    else:
        print("\n❌ Download failed. Check network connection.")