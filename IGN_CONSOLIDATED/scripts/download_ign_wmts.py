#!/usr/bin/env python3
"""
Download IGN WMTS tiles using the correct Géoservices endpoints.
Uses the 'essentiels' key for public access to basic layers.
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

class IGNWMTSDownloader:
    """Download IGN tiles using official WMTS service."""
    
    # IGN WMTS endpoint - new Géoplateforme domain
    WMTS_BASE = "https://data.geopf.fr/wmts"
    
    # Available layers with the essentiels key
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
        },
        'parcelles': {
            'layer': 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS',
            'format': 'image/png',
            'tilematrixset': 'PM',
            'style': 'normal',
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
            db_path = self.base_dir / f"ign_{layer_key}.mbtiles"
            self.dbs[layer_key] = self._init_mbtiles(db_path, layer_key)
        
        # Statistics
        self.stats = {'downloaded': 0, 'failed': 0, 'cached': 0, 'size_mb': 0}
    
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
        layer = self.LAYERS[layer_key]
        metadata = {
            'name': f'IGN {layer_key.upper()}',
            'type': 'baselayer',
            'version': '1.0.0',
            'description': f'IGN {layer["layer"]} for Occitanie',
            'format': layer['format'].split('/')[-1],
            'bounds': '-0.5,42.0,4.5,45.0',  # Occitanie
            'center': '2.0,43.5,10',
            'minzoom': '8',
            'maxzoom': str(layer['max_zoom']),
            'attribution': '© IGN'
        }
        
        for key, value in metadata.items():
            cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
                          (key, value))
        
        conn.commit()
        return conn
    
    def deg2num(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile numbers (Spherical Mercator)."""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (x, y)
    
    def get_tile_url(self, layer_key: str, x: int, y: int, z: int) -> str:
        """Build WMTS GetTile URL."""
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
        
        return f"{self.WMTS_BASE}?{'&'.join(params)}"
    
    def download_tile(self, layer_key: str, x: int, y: int, z: int) -> bool:
        """Download a single tile."""
        # Check if already cached
        cursor = self.dbs[layer_key].cursor()
        tms_y = (2 ** z - 1) - y  # Convert to TMS scheme
        
        cursor.execute(
            "SELECT COUNT(*) FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, tms_y)
        )
        if cursor.fetchone()[0] > 0:
            self.stats['cached'] += 1
            return True
        
        # Download the tile
        url = self.get_tile_url(layer_key, x, y, z)
        
        try:
            headers = {
                'User-Agent': 'SPOTS-QGIS/1.0',
                'Referer': 'https://www.geoportail.gouv.fr/'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200 and len(response.content) > 100:
                # Store in database
                cursor.execute(
                    "INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                    (z, x, tms_y, response.content)
                )
                self.dbs[layer_key].commit()
                self.stats['downloaded'] += 1
                self.stats['size_mb'] += len(response.content) / (1024 * 1024)
                return True
            else:
                self.stats['failed'] += 1
                return False
                
        except Exception as e:
            self.stats['failed'] += 1
            if "Connection" not in str(e):
                print(f"Error z{z}/{x}/{y}: {e}")
            return False
    
    def download_area(self, layer_key: str, bbox: Tuple[float, float, float, float],
                     zoom_levels: List[int], max_tiles: int = 100) -> Dict:
        """Download tiles for an area."""
        minlon, minlat, maxlon, maxlat = bbox
        
        print(f"\n📦 Downloading {layer_key.upper()}")
        print(f"   Area: ({minlon:.2f}, {minlat:.2f}) to ({maxlon:.2f}, {maxlat:.2f})")
        print(f"   Zoom levels: {zoom_levels}")
        
        tiles_to_download = []
        
        for z in zoom_levels:
            x1, y1 = self.deg2num(maxlat, minlon, z)
            x2, y2 = self.deg2num(minlat, maxlon, z)
            
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    tiles_to_download.append((z, x, y))
                    if len(tiles_to_download) >= max_tiles:
                        break
                if len(tiles_to_download) >= max_tiles:
                    break
            if len(tiles_to_download) >= max_tiles:
                break
        
        print(f"   Tiles to process: {len(tiles_to_download)}")
        
        # Download with progress
        for i, (z, x, y) in enumerate(tiles_to_download, 1):
            self.download_tile(layer_key, x, y, z)
            
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(tiles_to_download)} "
                      f"(↓ {self.stats['downloaded']} ✓ {self.stats['cached']} ✗ {self.stats['failed']})")
            
            # Rate limiting to be nice to IGN servers
            if self.stats['downloaded'] % 5 == 4:
                time.sleep(0.5)
        
        return self.stats
    
    def test_connectivity(self) -> bool:
        """Test if IGN WMTS service is accessible."""
        test_url = f"{self.WMTS_BASE}?SERVICE=WMTS&REQUEST=GetCapabilities"
        
        try:
            print("Testing IGN WMTS connectivity...")
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print("✅ IGN WMTS service is accessible")
                return True
            else:
                print(f"❌ IGN WMTS returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach IGN WMTS: {e}")
            return False
    
    def download_spots_collection(self):
        """Download IGN tiles for SPOTS areas with 50GB strategy."""
        
        # Priority areas for SPOTS
        collections = [
            {
                'name': 'Toulouse Urban',
                'bbox': (1.35, 43.55, 1.50, 43.65),
                'layers': ['plan', 'ortho'],
                'zooms': {'plan': [12, 13, 14], 'ortho': [14, 15]}
            },
            {
                'name': 'Pyrenees Caves',
                'bbox': (1.45, 42.75, 1.65, 42.85),
                'layers': ['cartes', 'ortho'],
                'zooms': {'cartes': [11, 12, 13], 'ortho': [13, 14]}
            },
            {
                'name': 'Montpellier & Salagou',
                'bbox': (3.30, 43.55, 3.45, 43.70),
                'layers': ['plan'],
                'zooms': {'plan': [11, 12, 13]}
            },
            {
                'name': 'Carcassonne',
                'bbox': (2.30, 43.18, 2.40, 43.25),
                'layers': ['plan', 'parcelles'],
                'zooms': {'plan': [12, 13], 'parcelles': [14, 15]}
            }
        ]
        
        print("=" * 60)
        print("IGN WMTS TILE COLLECTION FOR SPOTS")
        print("=" * 60)
        
        for collection in collections:
            print(f"\n🗺️  {collection['name']}")
            print("-" * 40)
            
            for layer in collection['layers']:
                if layer in self.LAYERS:
                    zooms = collection['zooms'].get(layer, [11, 12])
                    self.download_area(layer, collection['bbox'], zooms, max_tiles=100)
        
        # Final statistics
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"✅ Downloaded: {self.stats['downloaded']} new tiles")
        print(f"💾 Cached: {self.stats['cached']} existing tiles")
        print(f"❌ Failed: {self.stats['failed']} tiles")
        print(f"📊 Total size: {self.stats['size_mb']:.2f} MB")
        print(f"📁 Saved to: {self.base_dir}")
        
        # List all MBTiles files
        print("\n📦 MBTiles files created:")
        for db_name, conn in self.dbs.items():
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(LENGTH(tile_data)) FROM tiles")
            count, size = cursor.fetchone()
            if count and size:
                print(f"   - ign_{db_name}.mbtiles: {count} tiles, {size/(1024*1024):.2f} MB")

if __name__ == "__main__":
    downloader = IGNWMTSDownloader()
    
    # Test connectivity
    if not downloader.test_connectivity():
        print("\n⚠️ IGN WMTS service not accessible")
        print("This might be a temporary issue. Try again later.")
        sys.exit(1)
    
    # Test with one tile
    print("\n🧪 Testing single tile download...")
    test_success = downloader.download_tile('plan', 8180, 5905, 14)
    
    if test_success:
        print("✅ Test successful! Starting collection download...")
        downloader.download_spots_collection()
    else:
        print("⚠️ Test failed. Check if 'essentiels' key is still valid.")
        print("Visit https://geoservices.ign.fr/ for API key information.")