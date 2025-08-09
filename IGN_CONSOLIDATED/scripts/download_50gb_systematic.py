#!/usr/bin/env python3
"""
Systematic 50GB IGN Download using correct layer names
Targets all of Occitanie with proper WMTS identifiers
"""

import sqlite3
import requests
import time
import os
from pathlib import Path
import json
from typing import Tuple, List, Dict
import logging
from datetime import datetime
import math

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class IGN50GBDownloader:
    def __init__(self):
        self.base_url = "https://data.geopf.fr/wmts"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IGN-50GB-Downloader/3.0',
            'Accept': 'image/png,image/jpeg,*/*'
        })
        
        # Output directory
        self.output_dir = Path("../01_active_maps")
        self.output_dir.mkdir(exist_ok=True)
        
        # Stats
        self.stats = {
            'downloaded': 0,
            'cached': 0,
            'failed': 0,
            'total_size': 0,
            'start_time': time.time()
        }
        
        # Target: 50GB
        self.target_size = 50 * 1024 * 1024 * 1024  # 50GB in bytes
        
        # MBTiles databases for different layers
        self.databases = {}
        
    def init_mbtiles(self, name: str) -> sqlite3.Connection:
        """Initialize MBTiles database for a layer"""
        db_path = self.output_dir / f"ign_{name}.mbtiles"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables
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
                name TEXT,
                value TEXT
            )
        """)
        
        # Set metadata
        cursor.execute("DELETE FROM metadata")
        cursor.execute(f"INSERT INTO metadata VALUES ('name', 'IGN {name}')")
        cursor.execute("INSERT INTO metadata VALUES ('type', 'baselayer')")
        cursor.execute("INSERT INTO metadata VALUES ('format', 'png')")
        cursor.execute("INSERT INTO metadata VALUES ('bounds', '-1,41,5,45')")
        
        conn.commit()
        return conn
        
    def get_occitanie_regions(self) -> List[Dict]:
        """Define Occitanie regions with different zoom strategies"""
        return [
            # Major cities - highest detail
            {
                'name': 'Toulouse Metropolitan',
                'bbox': (1.20, 43.45, 1.65, 43.75),
                'layers': {
                    'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2': [12, 13, 14, 15, 16, 17, 18],
                    'ORTHOIMAGERY.ORTHOPHOTOS': [14, 15, 16, 17, 18],
                    'HR.ORTHOIMAGERY.ORTHOPHOTOS': [16, 17, 18, 19]
                }
            },
            {
                'name': 'Montpellier Metropolitan',
                'bbox': (3.70, 43.50, 4.00, 43.75),
                'layers': {
                    'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2': [12, 13, 14, 15, 16, 17, 18],
                    'ORTHOIMAGERY.ORTHOPHOTOS': [14, 15, 16, 17, 18],
                    'ORTHOIMAGERY.ORTHOPHOTOS.IRC-EXPRESS.2025': [16, 17, 18]
                }
            },
            {
                'name': 'Perpignan Area',
                'bbox': (2.80, 42.60, 3.00, 42.80),
                'layers': {
                    'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2': [12, 13, 14, 15, 16],
                    'ORTHOIMAGERY.ORTHOPHOTOS': [14, 15, 16, 17]
                }
            },
            {
                'name': 'Carcassonne Area',
                'bbox': (2.25, 43.15, 2.45, 43.25),
                'layers': {
                    'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2': [12, 13, 14, 15, 16],
                    'ORTHOIMAGERY.ORTHOPHOTOS.BDORTHO': [14, 15, 16]
                }
            },
            # Regional coverage - medium detail
            {
                'name': 'Haute-Garonne',
                'bbox': (0.40, 42.70, 2.10, 43.90),
                'layers': {
                    'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2': [10, 11, 12, 13, 14],
                    'ORTHOIMAGERY.ORTHOPHOTOS': [12, 13, 14]
                }
            },
            {
                'name': 'Hérault',
                'bbox': (2.50, 43.20, 4.00, 44.00),
                'layers': {
                    'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2': [10, 11, 12, 13, 14],
                    'ORTHOIMAGERY.ORTHOPHOTOS': [12, 13, 14]
                }
            },
            # Pyrenees - special layers
            {
                'name': 'Pyrenees Mountains',
                'bbox': (-0.50, 42.30, 3.20, 43.00),
                'layers': {
                    'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN50.1950': [10, 11, 12],
                    'ORTHOIMAGERY.ORTHOPHOTOS': [11, 12, 13, 14]
                }
            }
        ]
    
    def lat_lon_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile coordinates"""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y
    
    def download_tile(self, layer: str, z: int, x: int, y: int) -> Tuple[bool, int]:
        """Download a single tile and return success status and size"""
        url = f"{self.base_url}?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
        url += f"&LAYER={layer}&STYLE=normal&TILEMATRIXSET=PM"
        url += f"&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200 and len(response.content) > 100:
                # Store in appropriate database
                layer_key = layer.split('.')[0].lower()
                if layer_key not in self.databases:
                    self.databases[layer_key] = self.init_mbtiles(layer_key)
                
                conn = self.databases[layer_key]
                cursor = conn.cursor()
                
                # Convert XYZ to TMS
                tms_y = (2 ** z) - 1 - y
                
                cursor.execute(
                    "INSERT OR REPLACE INTO tiles VALUES (?, ?, ?, ?)",
                    (z, x, tms_y, response.content)
                )
                conn.commit()
                
                return True, len(response.content)
        except Exception as e:
            pass
        
        return False, 0
    
    def download_region(self, region: Dict):
        """Download all layers for a region"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📍 {region['name']}")
        logger.info(f"{'='*60}")
        
        min_lon, min_lat, max_lon, max_lat = region['bbox']
        
        for layer, zoom_levels in region['layers'].items():
            logger.info(f"\n🗺️ Layer: {layer}")
            
            for z in zoom_levels:
                # Calculate tile bounds
                min_x, max_y = self.lat_lon_to_tile(min_lat, min_lon, z)
                max_x, min_y = self.lat_lon_to_tile(max_lat, max_lon, z)
                
                total_tiles = (max_x - min_x + 1) * (max_y - min_y + 1)
                logger.info(f"   Zoom {z}: {total_tiles} tiles")
                
                tiles_downloaded = 0
                tiles_failed = 0
                size_downloaded = 0
                
                for x in range(min_x, max_x + 1):
                    for y in range(min_y, max_y + 1):
                        success, size = self.download_tile(layer, z, x, y)
                        
                        if success:
                            tiles_downloaded += 1
                            size_downloaded += size
                            self.stats['downloaded'] += 1
                            self.stats['total_size'] += size
                        else:
                            tiles_failed += 1
                            self.stats['failed'] += 1
                        
                        # Progress update
                        if (tiles_downloaded + tiles_failed) % 100 == 0:
                            progress = (tiles_downloaded + tiles_failed) / total_tiles * 100
                            logger.info(f"      {progress:.1f}% - {tiles_downloaded} downloaded, {size_downloaded/(1024*1024):.1f} MB")
                        
                        # Check if we've reached target
                        if self.stats['total_size'] >= self.target_size:
                            logger.info(f"\n🎯 TARGET REACHED: 50GB!")
                            return True
                        
                        # Rate limiting
                        time.sleep(0.02)  # 50 tiles per second
                
                logger.info(f"      ✅ {tiles_downloaded}/{total_tiles} tiles, {size_downloaded/(1024*1024):.1f} MB")
        
        return False
    
    def run(self):
        """Main download loop"""
        logger.info("🚀 Starting 50GB IGN Collection Download")
        logger.info(f"Target: {self.target_size / (1024*1024*1024):.1f} GB")
        
        for region in self.get_occitanie_regions():
            if self.download_region(region):
                break
            
            # Progress report
            elapsed = time.time() - self.stats['start_time']
            rate = self.stats['total_size'] / elapsed if elapsed > 0 else 0
            eta = (self.target_size - self.stats['total_size']) / rate if rate > 0 else 0
            
            logger.info(f"\n📊 Overall Progress:")
            logger.info(f"   Downloaded: {self.stats['downloaded']} tiles")
            logger.info(f"   Failed: {self.stats['failed']} tiles")
            logger.info(f"   Total size: {self.stats['total_size'] / (1024*1024*1024):.2f} GB")
            logger.info(f"   Progress: {self.stats['total_size'] / self.target_size * 100:.2f}%")
            logger.info(f"   Rate: {rate / (1024*1024):.1f} MB/s")
            logger.info(f"   ETA: {eta / 3600:.1f} hours")
        
        # Close all databases
        for conn in self.databases.values():
            conn.close()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Download Complete!")
        logger.info(f"   Final size: {self.stats['total_size'] / (1024*1024*1024):.2f} GB")
        logger.info(f"   Total tiles: {self.stats['downloaded']}")
        logger.info(f"   Failed tiles: {self.stats['failed']}")
        logger.info(f"{'='*60}")

if __name__ == "__main__":
    downloader = IGN50GBDownloader()
    downloader.run()