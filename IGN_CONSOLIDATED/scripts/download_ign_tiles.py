#!/usr/bin/env python3
"""
Download IGN tiles using proper Géoplateforme endpoints.
Handles authentication and uses the correct tile services.
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

class IGNGeoplatformeDownloader:
    """Download IGN tiles from Géoplateforme services."""
    
    # Géoplateforme WMTS endpoints
    WMTS_ENDPOINTS = {
        'public': 'https://data.geopf.fr/wmts',
        'private': 'https://data.geopf.fr/private/wmts'
    }
    
    # Available layers from Géoplateforme
    LAYERS = {
        'scan25': {
            'id': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR.L93',
            'format': 'image/jpeg',
            'style': 'normal',
            'tilematrixset': 'LAMB93',
            'max_zoom': 16,
            'auth_required': False
        },
        'plan': {
            'id': 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
            'format': 'image/png',
            'style': 'normal',
            'tilematrixset': 'PM',
            'max_zoom': 18,
            'auth_required': False
        },
        'ortho': {
            'id': 'ORTHOIMAGERY.ORTHOPHOTOS',
            'format': 'image/jpeg',
            'style': 'normal',
            'tilematrixset': 'PM',
            'max_zoom': 20,
            'auth_required': True
        },
        'carte': {
            'id': 'GEOGRAPHICALGRIDSYSTEMS.MAPS',
            'format': 'image/jpeg',
            'style': 'normal', 
            'tilematrixset': 'PM',
            'max_zoom': 18,
            'auth_required': False
        }
    }
    
    def __init__(self, api_key: str = None, base_dir: str = "/home/miko/Development/projects/spots/offline_tiles"):
        """Initialize with optional API key for authenticated layers."""
        self.api_key = api_key or "essentiels"  # Use 'essentiels' key for public layers
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize databases
        self.dbs = {}
        for layer_key in self.LAYERS:
            db_path = self.base_dir / f"ign_{layer_key}.mbtiles"
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
        layer = self.LAYERS[layer_key]
        metadata = {
            'name': f'IGN {layer_key.upper()} Occitanie',
            'type': 'baselayer',
            'version': '1.0.0',
            'description': f'IGN {layer_key} tiles for Occitanie via Géoplateforme',
            'format': layer['format'].split('/')[-1],
            'bounds': '-0.5,42.0,4.5,45.0',  # Occitanie bounds
            'center': '2.0,43.5,8',
            'minzoom': '8',
            'maxzoom': str(layer['max_zoom'])
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
        """Generate tile URL for Géoplateforme WMTS."""
        layer = self.LAYERS[layer_key]
        
        # Use private endpoint if auth required, public otherwise
        if layer['auth_required'] and self.api_key != "essentiels":
            base_url = f"https://data.geopf.fr/private/wmts"
        else:
            base_url = f"https://wxs.ign.fr/{self.api_key}/geoportail/wmts"
        
        # Build WMTS GetTile request
        params = [
            f"SERVICE=WMTS",
            f"REQUEST=GetTile",
            f"VERSION=1.0.0",
            f"LAYER={layer['id']}",
            f"STYLE={layer['style']}",
            f"TILEMATRIXSET={layer['tilematrixset']}",
            f"TILEMATRIX={z}",
            f"TILEROW={y}",
            f"TILECOL={x}",
            f"FORMAT={layer['format']}"
        ]
        
        return f"{base_url}?{'&'.join(params)}"
    
    def download_tile(self, layer_key: str, x: int, y: int, z: int) -> bool:
        """Download a single tile."""
        # Check if already exists
        cursor = self.dbs[layer_key].cursor()
        tms_y = (2 ** z - 1) - y
        cursor.execute(
            "SELECT COUNT(*) FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, tms_y)
        )
        if cursor.fetchone()[0] > 0:
            return True  # Already have it
        
        url = self.get_tile_url(layer_key, x, y, z)
        
        try:
            headers = {
                'User-Agent': 'SPOTS-QGIS/1.0',
                'Referer': 'https://www.geoportail.gouv.fr/'
            }
            
            # Add auth header if we have a real API key
            if self.api_key and self.api_key != "essentiels":
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200 and len(response.content) > 100:
                # Valid tile data (not an error image)
                cursor.execute(
                    "INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                    (z, x, tms_y, response.content)
                )
                self.dbs[layer_key].commit()
                return True
            elif response.status_code == 401:
                print(f"⚠️ Authentication required for {layer_key}")
                return False
                
        except Exception as e:
            if "Name or service not known" not in str(e):
                print(f"Error: {e}")
        
        return False
    
    def test_connectivity(self) -> bool:
        """Test if IGN services are accessible."""
        test_urls = [
            "https://www.geoportail.gouv.fr/",
            "https://wxs.ign.fr/essentiels/geoportail/wmts?SERVICE=WMTS&REQUEST=GetCapabilities",
            "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetCapabilities"
        ]
        
        print("Testing IGN/Géoplateforme connectivity...")
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {url.split('/')[2]} is accessible")
                    return True
            except:
                print(f"❌ {url.split('/')[2]} is not accessible")
        
        return False
    
    def download_area(self, layer_key: str, bbox: Tuple[float, float, float, float], 
                     zoom_levels: List[int], max_tiles: int = 100) -> Dict:
        """Download tiles for an area."""
        minlon, minlat, maxlon, maxlat = bbox
        stats = {'downloaded': 0, 'failed': 0, 'skipped': 0, 'size_mb': 0}
        
        print(f"\n📍 Downloading {layer_key.upper()} tiles")
        print(f"   Bbox: ({minlon:.2f}, {minlat:.2f}, {maxlon:.2f}, {maxlat:.2f})")
        print(f"   Zoom levels: {zoom_levels}")
        
        tile_count = 0
        for z in zoom_levels:
            x1, y1 = self.deg2num(maxlat, minlon, z)
            x2, y2 = self.deg2num(minlat, maxlon, z)
            
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    if self.download_tile(layer_key, x, y, z):
                        stats['downloaded'] += 1
                    else:
                        stats['failed'] += 1
                    
                    tile_count += 1
                    if tile_count % 10 == 0:
                        print(f"   Progress: {tile_count} tiles...")
                    
                    time.sleep(0.2)  # Rate limiting
                    
                    if tile_count >= max_tiles:
                        break
                if tile_count >= max_tiles:
                    break
            if tile_count >= max_tiles:
                break
        
        # Calculate size
        cursor = self.dbs[layer_key].cursor()
        cursor.execute("SELECT SUM(LENGTH(tile_data)) FROM tiles")
        total_bytes = cursor.fetchone()[0] or 0
        stats['size_mb'] = total_bytes / (1024 * 1024)
        
        print(f"   ✅ Downloaded: {stats['downloaded']} tiles ({stats['size_mb']:.2f} MB)")
        if stats['failed'] > 0:
            print(f"   ❌ Failed: {stats['failed']} tiles")
        
        return stats

    def download_occitanie_spots(self):
        """Download IGN tiles for Occitanie spots."""
        
        # Key areas with spots
        areas = [
            {'name': 'Toulouse', 'bbox': (1.3, 43.5, 1.6, 43.7), 'layers': ['plan', 'carte']},
            {'name': 'Montpellier', 'bbox': (3.7, 43.5, 3.95, 43.7), 'layers': ['plan']},
            {'name': 'Pyrénées', 'bbox': (1.4, 42.7, 1.7, 42.9), 'layers': ['scan25', 'carte']}
        ]
        
        print("=" * 60)
        print("IGN GÉOPLATEFORME TILE DOWNLOAD")
        print("=" * 60)
        
        total_stats = {'downloaded': 0, 'size_mb': 0}
        
        for area in areas:
            print(f"\n🗺️  Area: {area['name']}")
            print("-" * 40)
            
            for layer in area['layers']:
                if layer in self.LAYERS:
                    # Download at appropriate zoom levels
                    if layer == 'scan25':
                        zooms = [10, 11, 12]
                    elif layer == 'plan':
                        zooms = [12, 13, 14]
                    else:
                        zooms = [11, 12]
                    
                    stats = self.download_area(layer, area['bbox'], zooms, max_tiles=50)
                    total_stats['downloaded'] += stats['downloaded']
                    total_stats['size_mb'] += stats['size_mb']
        
        print("\n" + "=" * 60)
        print(f"TOTAL: {total_stats['downloaded']} tiles, {total_stats['size_mb']:.2f} MB")
        print(f"📁 Files saved in: {self.base_dir}")
        print("=" * 60)

if __name__ == "__main__":
    # Initialize downloader
    downloader = IGNGeoplatformeDownloader()
    
    # Test connectivity first
    if not downloader.test_connectivity():
        print("\n⚠️ Cannot reach IGN services. Check internet connection.")
        sys.exit(1)
    
    # Test with small area
    print("\n🧪 Testing with Toulouse center...")
    test_bbox = (1.44, 43.6, 1.45, 43.61)  # Very small area
    stats = downloader.download_area('carte', test_bbox, [11], max_tiles=5)
    
    if stats['downloaded'] > 0:
        print("\n✅ Test successful! IGN tiles are downloading.")
        print("\nStarting full download for spot areas...")
        downloader.download_occitanie_spots()
    else:
        print("\n⚠️ Could not download IGN tiles. They may require authentication.")
        print("Try using OpenStreetMap tiles instead with:")
        print("  python3 scripts/download_osm_tiles.py")