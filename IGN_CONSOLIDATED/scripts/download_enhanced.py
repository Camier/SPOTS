#!/usr/bin/env python3
"""
Enhanced IGN Download Script - Targets new zoom levels and avoids cached tiles
Based on sequential thinking analysis
"""

import sqlite3
import requests
import time
import os
from pathlib import Path
import json
from typing import Tuple, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedIGNDownloader:
    def __init__(self):
        self.base_url = "https://data.geopf.fr/wmts"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IGN-Enhanced-Downloader/2.0',
            'Accept': 'image/jpeg,image/png,*/*'
        })
        
        # Output MBTiles file for new downloads
        self.output_file = Path("../01_active_maps/ign_hd_zoom18plus.mbtiles")
        self.conn = None
        self.init_output_mbtiles()
        
        # Load existing MBTiles to check for cached tiles
        self.mbtiles_dir = Path("../01_active_maps")
        self.cached_tiles = set()
        self.load_cached_tiles()
        
        # Stats
        self.downloaded = 0
        self.cached = 0
        self.failed = 0
        self.total_size = 0
        
    def init_output_mbtiles(self):
        """Initialize output MBTiles database"""
        self.conn = sqlite3.connect(str(self.output_file))
        cursor = self.conn.cursor()
        
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
        cursor.execute("INSERT INTO metadata VALUES ('name', 'IGN HD Zoom 18+')")
        cursor.execute("INSERT INTO metadata VALUES ('type', 'baselayer')")
        cursor.execute("INSERT INTO metadata VALUES ('format', 'jpg')")
        cursor.execute("INSERT INTO metadata VALUES ('bounds', '-180,-85,180,85')")
        cursor.execute("INSERT INTO metadata VALUES ('minzoom', '18')")
        cursor.execute("INSERT INTO metadata VALUES ('maxzoom', '20')")
        
        self.conn.commit()
    
    def load_cached_tiles(self):
        """Load all cached tile coordinates to avoid re-downloading"""
        for mbtiles_file in self.mbtiles_dir.glob("*.mbtiles"):
            # Skip our own output file
            if mbtiles_file == self.output_file:
                continue
                
            # Skip loading zoom 18+ since we want to download those
            try:
                conn = sqlite3.connect(str(mbtiles_file))
                cursor = conn.cursor()
                cursor.execute("SELECT zoom_level, tile_column, tile_row FROM tiles WHERE zoom_level < 18")
                for z, x, y in cursor.fetchall():
                    self.cached_tiles.add((z, x, y))
                conn.close()
                logger.info(f"Loaded cached tiles from {mbtiles_file.name}")
            except Exception as e:
                logger.warning(f"Could not load cache from {mbtiles_file}: {e}")
        logger.info(f"Total cached tiles (< zoom 18): {len(self.cached_tiles)}")
    
    def is_cached(self, z: int, x: int, y: int) -> bool:
        """Check if tile is already cached"""
        # Convert XYZ to TMS for cache check
        tms_y = (2 ** z) - 1 - y
        return (z, x, tms_y) in self.cached_tiles
    
    def download_high_detail_tiles(self):
        """Download zoom levels 18-20 for ultra high detail"""
        
        # Ultra high-priority small areas with HIGHEST zoom levels
        targets = [
            {
                'name': 'Toulouse Capitol Square UHD',
                'bbox': (1.441, 43.603, 1.445, 43.605),  # Very small area - just the square
                'layers': ['GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2', 'ORTHOIMAGERY.ORTHOPHOTOS'],
                'zoom_levels': [18, 19, 20]  # ULTRA high detail
            },
            {
                'name': 'Montpellier Place Comédie UHD',
                'bbox': (3.878, 43.608, 3.882, 43.610),  # Just the plaza
                'layers': ['GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2', 'HR.ORTHOIMAGERY.ORTHOPHOTOS'],
                'zoom_levels': [18, 19, 20]
            },
            {
                'name': 'Carcassonne Castle UHD',
                'bbox': (2.361, 43.205, 2.365, 43.207),  # Just the castle
                'layers': ['ORTHOIMAGERY.ORTHOPHOTOS.IRC-EXPRESS.2025', 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2'],
                'zoom_levels': [18, 19, 20]
            }
        ]
        
        for target in targets:
            logger.info(f"\n🎯 Downloading {target['name']}")
            logger.info(f"   Zoom levels: {target['zoom_levels']}")
            
            for layer in target['layers']:
                self.download_region(
                    layer=layer,
                    bbox=target['bbox'],
                    zoom_levels=target['zoom_levels'],
                    region_name=target['name']
                )
                
                # Report progress
                logger.info(f"   Progress: {self.downloaded} new, {self.cached} cached, {self.failed} failed")
                logger.info(f"   Total size: {self.total_size / (1024*1024):.2f} MB")
                
                if self.total_size > 1024 * 1024 * 1024:  # Stop at 1GB per session
                    logger.info("Reached 1GB session limit")
                    return
    
    def download_region(self, layer: str, bbox: Tuple, zoom_levels: List[int], region_name: str):
        """Download tiles for a specific region"""
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        for z in zoom_levels:
            # Calculate tile bounds - note that Y increases from north to south
            min_x, max_y = self.lat_lon_to_tile(min_lat, min_lon, z)
            max_x, min_y = self.lat_lon_to_tile(max_lat, max_lon, z)
            
            total_tiles = (max_x - min_x + 1) * (max_y - min_y + 1)
            logger.info(f"   Level {z}: {total_tiles} tiles to check")
            
            tiles_downloaded = 0
            
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    # Skip if cached
                    if self.is_cached(z, x, y):
                        self.cached += 1
                        continue
                    
                    # Download tile
                    success = self.download_tile(layer, z, x, y)
                    
                    if success:
                        self.downloaded += 1
                        tiles_downloaded += 1
                    else:
                        self.failed += 1
                    
                    # Progress update every 100 tiles
                    if (self.downloaded + self.cached + self.failed) % 100 == 0:
                        logger.info(f"      {tiles_downloaded}/{total_tiles} new tiles at zoom {z}")
                    
                    # Rate limiting
                    time.sleep(0.05)  # 20 tiles per second max
    
    def download_tile(self, layer: str, z: int, x: int, y: int) -> bool:
        """Download and store a single tile"""
        
        url = f"{self.base_url}?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
        url += f"&LAYER={layer}&STYLE=normal&TILEMATRIXSET=PM"
        url += f"&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg"
        
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200 and len(response.content) > 0:
                self.total_size += len(response.content)
                
                # Store tile in MBTiles (convert XYZ to TMS)
                tms_y = (2 ** z) - 1 - y
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO tiles VALUES (?, ?, ?, ?)",
                    (z, x, tms_y, response.content)
                )
                self.conn.commit()
                
                return True
        except Exception as e:
            pass
        
        return False
    
    def lat_lon_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile coordinates"""
        import math
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y

def main():
    logger.info("🚀 Enhanced IGN Download - Targeting NEW zoom levels")
    logger.info("=" * 60)
    
    downloader = EnhancedIGNDownloader()
    downloader.download_high_detail_tiles()
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ Session Complete")
    logger.info(f"   Downloaded: {downloader.downloaded} new tiles")
    logger.info(f"   Skipped: {downloader.cached} cached tiles")
    logger.info(f"   Failed: {downloader.failed} tiles")
    logger.info(f"   Total size: {downloader.total_size / (1024*1024):.2f} MB")
    logger.info(f"   Progress to 50GB: {downloader.total_size / (50*1024*1024*1024) * 100:.3f}%")

if __name__ == "__main__":
    main()