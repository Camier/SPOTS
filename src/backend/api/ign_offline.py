#!/usr/bin/env python3
"""API endpoints for IGN offline maps management and serving"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import sqlite3
import json
import io
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration
IGN_BASE = Path("/home/miko/Development/projects/spots/IGN_CONSOLIDATED")
MBTILES_DIR = IGN_BASE / "01_active_maps"
DOWNLOADS_DIR = IGN_BASE / "02_downloads"
CACHE_DIR = IGN_BASE / "03_cache_recovered"
SCRIPTS_DIR = IGN_BASE / "04_scripts"

# Active MBTiles databases
MBTILES_SOURCES = {
    "ign_plan": MBTILES_DIR / "ign_plan.mbtiles",
    "ign_ortho": MBTILES_DIR / "ign_ortho.mbtiles",
    "ign_parcelles": MBTILES_DIR / "ign_parcelles.mbtiles",
    "osm": MBTILES_DIR / "osm.mbtiles",
    "ign_cartes": DOWNLOADS_DIR / "ign_cartes.mbtiles",
    "cache_recovered": CACHE_DIR / "recovered_tiles.mbtiles"
}

class MBTilesManager:
    """Manager for MBTiles offline map databases"""
    
    def __init__(self):
        self.connections = {}
        self._init_connections()
    
    def _init_connections(self):
        """Initialize connections to all available MBTiles"""
        for name, path in MBTILES_SOURCES.items():
            if path.exists():
                try:
                    conn = sqlite3.connect(str(path), check_same_thread=False)
                    conn.row_factory = sqlite3.Row
                    self.connections[name] = conn
                    logger.info(f"Connected to {name}: {path}")
                except Exception as e:
                    logger.error(f"Failed to connect to {name}: {e}")
    
    def get_tile(self, source: str, z: int, x: int, y: int) -> Optional[bytes]:
        """Get a tile from specified MBTiles source"""
        if source not in self.connections:
            return None
        
        conn = self.connections[source]
        cursor = conn.cursor()
        
        # MBTiles uses TMS scheme, we need to flip Y
        tms_y = (2 ** z) - 1 - y
        
        cursor.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
            (z, x, tms_y)
        )
        row = cursor.fetchone()
        
        if row:
            return row[0]
        return None
    
    def get_metadata(self, source: str) -> Dict:
        """Get metadata from MBTiles source"""
        if source not in self.connections:
            return {}
        
        conn = self.connections[source]
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, value FROM metadata")
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_stats(self, source: str) -> Dict:
        """Get statistics for MBTiles source"""
        if source not in self.connections:
            return {}
        
        conn = self.connections[source]
        cursor = conn.cursor()
        
        stats = {
            "total_tiles": cursor.execute("SELECT COUNT(*) FROM tiles").fetchone()[0],
            "zoom_levels": cursor.execute(
                "SELECT DISTINCT zoom_level FROM tiles ORDER BY zoom_level"
            ).fetchall(),
            "bounds": None
        }
        
        # Get bounds
        cursor.execute("""
            SELECT MIN(tile_column) as min_x, MAX(tile_column) as max_x,
                   MIN(tile_row) as min_y, MAX(tile_row) as max_y,
                   zoom_level
            FROM tiles
            GROUP BY zoom_level
            ORDER BY zoom_level DESC
            LIMIT 1
        """)
        bounds = cursor.fetchone()
        if bounds:
            stats["bounds"] = dict(bounds)
        
        return stats

# Initialize manager
mbtiles_manager = MBTilesManager()

@router.get("/status")
async def get_offline_maps_status():
    """Get status of all offline map sources"""
    status = {
        "sources": {},
        "total_size_mb": 0,
        "total_tiles": 0,
        "download_progress": None
    }
    
    for name, path in MBTILES_SOURCES.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            stats = mbtiles_manager.get_stats(name)
            
            status["sources"][name] = {
                "path": str(path),
                "size_mb": round(size_mb, 2),
                "tiles": stats.get("total_tiles", 0),
                "zoom_levels": [z[0] for z in stats.get("zoom_levels", [])],
                "available": True
            }
            status["total_size_mb"] += size_mb
            status["total_tiles"] += stats.get("total_tiles", 0)
        else:
            status["sources"][name] = {
                "path": str(path),
                "available": False
            }
    
    # Check for download progress
    progress_file = DOWNLOADS_DIR / "download_progress.json"
    if progress_file.exists():
        with open(progress_file) as f:
            status["download_progress"] = json.load(f)
    
    status["total_size_mb"] = round(status["total_size_mb"], 2)
    
    return status

@router.get("/tiles/{source}/{z}/{x}/{y}")
async def get_tile(
    source: str,
    z: int,
    x: int,
    y: int,
    fallback: Optional[str] = Query(None, description="Fallback source if tile not found")
):
    """Get a tile from offline MBTiles source"""
    
    # Try primary source
    tile_data = mbtiles_manager.get_tile(source, z, x, y)
    
    # Try fallback if specified and primary failed
    if not tile_data and fallback:
        tile_data = mbtiles_manager.get_tile(fallback, z, x, y)
    
    if not tile_data:
        raise HTTPException(status_code=404, detail="Tile not found")
    
    # Determine content type based on data
    content_type = "image/jpeg"
    if tile_data[:4] == b'\x89PNG':
        content_type = "image/png"
    elif tile_data[:2] == b'\x1f\x8b':  # gzip compressed
        content_type = "application/x-protobuf"  # Likely vector tiles
    
    return Response(content=tile_data, media_type=content_type)

@router.get("/metadata/{source}")
async def get_source_metadata(source: str):
    """Get metadata for a specific MBTiles source"""
    
    if source not in mbtiles_manager.connections:
        raise HTTPException(status_code=404, detail=f"Source '{source}' not found")
    
    metadata = mbtiles_manager.get_metadata(source)
    stats = mbtiles_manager.get_stats(source)
    
    return {
        "source": source,
        "metadata": metadata,
        "statistics": stats
    }

@router.get("/coverage")
async def get_coverage_map():
    """Get combined coverage of all offline maps"""
    
    coverage = {
        "type": "FeatureCollection",
        "features": [],
        "sources": {}
    }
    
    for source in mbtiles_manager.connections.keys():
        stats = mbtiles_manager.get_stats(source)
        if stats.get("bounds"):
            bounds = stats["bounds"]
            # Convert tile coordinates to lat/lon (simplified)
            # This would need proper mercator projection conversion
            coverage["sources"][source] = {
                "tiles": stats["total_tiles"],
                "zoom_range": [
                    min(z[0] for z in stats["zoom_levels"]),
                    max(z[0] for z in stats["zoom_levels"])
                ]
            }
    
    return coverage

@router.get("/layers")
async def get_available_layers():
    """Get configuration for all available offline layers"""
    
    layers = {}
    
    for source, path in MBTILES_SOURCES.items():
        if path.exists() and source in mbtiles_manager.connections:
            metadata = mbtiles_manager.get_metadata(source)
            stats = mbtiles_manager.get_stats(source)
            
            # Determine layer type and style
            layer_config = {
                "name": metadata.get("name", source.replace("_", " ").title()),
                "description": metadata.get("description", ""),
                "type": "raster",
                "source": source,
                "url_template": f"/api/ign-offline/tiles/{source}/{{z}}/{{x}}/{{y}}",
                "attribution": metadata.get("attribution", "© IGN"),
                "minzoom": metadata.get("minzoom", 5),
                "maxzoom": metadata.get("maxzoom", 18),
                "bounds": metadata.get("bounds", "-180,-85,180,85").split(","),
                "tile_count": stats.get("total_tiles", 0),
                "size_mb": round(path.stat().st_size / (1024 * 1024), 2)
            }
            
            # Set appropriate category
            if "ortho" in source:
                layer_config["category"] = "satellite"
                layer_config["opacity"] = 1.0
            elif "plan" in source:
                layer_config["category"] = "base"
                layer_config["opacity"] = 1.0
            elif "parcelles" in source:
                layer_config["category"] = "cadastre"
                layer_config["opacity"] = 0.6
            elif "osm" in source:
                layer_config["category"] = "base"
                layer_config["opacity"] = 1.0
            else:
                layer_config["category"] = "overlay"
                layer_config["opacity"] = 0.8
            
            layers[source] = layer_config
    
    return {
        "layers": layers,
        "categories": {
            "base": "Fonds de carte",
            "satellite": "Images satellite",
            "cadastre": "Cadastre",
            "overlay": "Couches supplémentaires"
        },
        "offline": True,
        "last_update": datetime.now().isoformat()
    }

@router.post("/download/start")
async def start_download(
    layer: str = Query(..., description="Layer to download"),
    region: str = Query(..., description="Region to download"),
    zoom_min: int = Query(5, ge=0, le=20),
    zoom_max: int = Query(15, ge=0, le=20)
):
    """Start downloading tiles for offline use"""
    
    import subprocess
    
    script_path = SCRIPTS_DIR / "download" / "download_50gb_collection.py"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Download script not found")
    
    # Start download process in background
    try:
        process = subprocess.Popen(
            ["python3", str(script_path), "--layer", layer, "--region", region,
             "--zoom-min", str(zoom_min), "--zoom-max", str(zoom_max)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(SCRIPTS_DIR / "download")
        )
        
        return {
            "status": "started",
            "pid": process.pid,
            "layer": layer,
            "region": region,
            "zoom_range": [zoom_min, zoom_max]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/progress")
async def get_download_progress():
    """Get progress of ongoing downloads"""
    
    progress_file = DOWNLOADS_DIR / "download_progress.json"
    if not progress_file.exists():
        return {"status": "no_downloads", "downloads": []}
    
    with open(progress_file) as f:
        progress = json.load(f)
    
    # Calculate overall progress
    total_tiles = sum(d.get("total_tiles", 0) for d in progress.get("downloads", []))
    downloaded_tiles = sum(d.get("downloaded", 0) for d in progress.get("downloads", []))
    
    return {
        "status": "downloading" if any(d.get("status") == "active" for d in progress.get("downloads", [])) else "idle",
        "overall_progress": {
            "tiles_downloaded": downloaded_tiles,
            "tiles_total": total_tiles,
            "percentage": round((downloaded_tiles / total_tiles * 100) if total_tiles > 0 else 0, 2),
            "size_mb": round(progress.get("total_size_mb", 0), 2),
            "target_size_mb": 50000
        },
        "downloads": progress.get("downloads", []),
        "last_update": progress.get("last_update", "")
    }

@router.post("/cache/optimize")
async def optimize_cache():
    """Optimize MBTiles databases (VACUUM and ANALYZE)"""
    
    results = {}
    
    for source, conn in mbtiles_manager.connections.items():
        try:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            conn.commit()
            
            # Get new size
            path = MBTILES_SOURCES[source]
            new_size = path.stat().st_size / (1024 * 1024)
            
            results[source] = {
                "status": "optimized",
                "size_mb": round(new_size, 2)
            }
        except Exception as e:
            results[source] = {
                "status": "error",
                "error": str(e)
            }
    
    return {"optimization_results": results}

@router.get("/statistics")
async def get_detailed_statistics():
    """Get detailed statistics about offline maps"""
    
    stats = {
        "summary": {
            "total_sources": len(mbtiles_manager.connections),
            "total_tiles": 0,
            "total_size_mb": 0,
            "coverage_percentage": 0
        },
        "by_source": {},
        "by_zoom_level": {},
        "regions_covered": []
    }
    
    for source in mbtiles_manager.connections.keys():
        source_stats = mbtiles_manager.get_stats(source)
        path = MBTILES_SOURCES[source]
        
        stats["by_source"][source] = {
            "tiles": source_stats.get("total_tiles", 0),
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "zoom_levels": [z[0] for z in source_stats.get("zoom_levels", [])]
        }
        
        stats["summary"]["total_tiles"] += source_stats.get("total_tiles", 0)
        stats["summary"]["total_size_mb"] += path.stat().st_size / (1024 * 1024)
        
        # Aggregate by zoom level
        for zoom in source_stats.get("zoom_levels", []):
            z = str(zoom[0])
            if z not in stats["by_zoom_level"]:
                stats["by_zoom_level"][z] = {"sources": [], "total_tiles": 0}
            stats["by_zoom_level"][z]["sources"].append(source)
    
    stats["summary"]["total_size_mb"] = round(stats["summary"]["total_size_mb"], 2)
    stats["summary"]["coverage_percentage"] = round(
        (stats["summary"]["total_size_mb"] / 50000) * 100, 2
    )
    
    # Add regions (based on actual coverage)
    if stats["summary"]["total_tiles"] > 0:
        stats["regions_covered"] = [
            {"name": "Toulouse", "coverage": "partial"},
            {"name": "Montpellier", "coverage": "partial"},
            {"name": "Pyrénées", "coverage": "minimal"}
        ]
    
    return stats