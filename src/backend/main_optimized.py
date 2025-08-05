#!/usr/bin/env python3
"""
Optimized Main API with compression, caching, and performance improvements
"""

from fastapi import FastAPI, HTTPException, Query, Path as PathParam, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from pathlib import Path
import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict
from dotenv import load_dotenv
from src.backend.core.logging_config import logger
from src.backend.db_utils import get_db_connection, init_db_optimizations
import time
from datetime import datetime, timedelta
import hashlib
import orjson

# Load environment variables
load_dotenv()

# Import API routers
from src.backend.api import mapping_france, ign_data, code_analysis

# Create FastAPI app with optimized JSON response
app = FastAPI(
    title="Spots Secrets Occitanie API",
    description="Discover secret spots across Occitanie departments",
    version="2.4.0",
    default_response_class=ORJSONResponse,  # Faster JSON serialization
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS (keep open for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_PATH = Path(__file__).parent.parent.parent / "data" / "occitanie_spots.db"

# Initialize database optimizations
init_db_optimizations(str(DB_PATH))

# Department boundaries configuration
DEPARTMENT_INFO = {
    "09": {"name": "Ariège", "bounds": {"lat_max": 43.2, "lng_max": 2.0}},
    "12": {"name": "Aveyron", "bounds": {"lat_min": 44.2, "lng_min": 2.2}},
    "46": {"name": "Lot", "bounds": {"lat_min": 44.3, "lng_max": 2.0}},
    "81": {"name": "Tarn", "bounds": {"lat_min": 43.7, "lng_min": 1.8, "lng_max": 2.5}},
    "65": {"name": "Hautes-Pyrénées", "bounds": {"lat_max": 43.5, "lng_max": 0.5}},
    "32": {"name": "Gers", "bounds": {"lat_min": 43.5, "lng_max": 1.0}},
    "82": {"name": "Tarn-et-Garonne", "bounds": {"lat_min": 43.8, "lng_min": 1.0, "lng_max": 1.7}},
    "31": {"name": "Haute-Garonne", "bounds": {}},  # No bounds = all remaining spots
    "30": {"name": "Gard", "bounds": {"lat_min": 43.8, "lng_min": 3.5}},
    "34": {"name": "Hérault", "bounds": {"lat_min": 43.2, "lng_min": 2.8}},
}

# Simple in-memory cache
cache = {}
cache_ttl = 300  # 5 minutes

def get_cache_key(endpoint: str, params: dict) -> str:
    """Generate cache key from endpoint and params"""
    param_str = orjson.dumps(params, option=orjson.OPT_SORT_KEYS).decode()
    return hashlib.md5(f"{endpoint}:{param_str}".encode()).hexdigest()

def get_cached_response(key: str) -> Optional[dict]:
    """Get cached response if valid"""
    if key in cache:
        entry = cache[key]
        if time.time() - entry["timestamp"] < cache_ttl:
            return entry["data"]
    return None

def set_cache(key: str, data: dict):
    """Set cache entry"""
    cache[key] = {
        "timestamp": time.time(),
        "data": data
    }

def build_where_clause(spot_type: Optional[str] = None, department: Optional[str] = None) -> str:
    """Build WHERE clause for queries"""
    conditions = []
    
    if spot_type:
        conditions.append(f"type = '{spot_type}'")
    
    if department and department in DEPARTMENT_INFO:
        bounds = DEPARTMENT_INFO[department]["bounds"]
        if bounds:
            if "lat_min" in bounds:
                conditions.append(f"latitude >= {bounds['lat_min']}")
            if "lat_max" in bounds:
                conditions.append(f"latitude <= {bounds['lat_max']}")
            if "lng_min" in bounds:
                conditions.append(f"longitude >= {bounds['lng_min']}")
            if "lng_max" in bounds:
                conditions.append(f"longitude <= {bounds['lng_max']}")
    
    return " AND ".join(conditions) if conditions else "1=1"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    with get_db_connection(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM spots")
        count = cursor.fetchone()[0]
    
    return {"status": "healthy", "spots_count": count}

@app.get("/api/spots/quality", response_class=ORJSONResponse)
async def get_quality_spots(
    response: Response,
    type: Optional[str] = Query(None, description="Filter by spot type"),
    department: Optional[str] = Query(None, description="Filter by department code"),
    limit: int = Query(50, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get quality spots with caching and pagination"""
    
    # Check cache
    cache_key = get_cache_key("quality_spots", {
        "type": type, "department": department, "limit": limit, "offset": offset
    })
    cached = get_cached_response(cache_key)
    if cached:
        response.headers["X-Cache"] = "HIT"
        return cached
    
    response.headers["X-Cache"] = "MISS"
    
    # Build query
    where_clause = build_where_clause(type, department)
    
    query = f"""
        SELECT 
            id, name, type, latitude, longitude, description,
            difficulty, beauty_rating, popularity, best_season,
            department, region, activities, date_added
        FROM spots 
        WHERE {where_clause}
        ORDER BY beauty_rating DESC, popularity DESC
        LIMIT ? OFFSET ?
    """
    
    with get_db_connection(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (limit, offset))
        
        spots = []
        for row in cursor.fetchall():
            spot = {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "description": row[5],
                "difficulty": row[6],
                "beauty_rating": row[7],
                "popularity": row[8],
                "best_season": row[9],
                "department": row[10],
                "region": row[11],
                "activities": row[12].split(",") if row[12] else [],
                "date_added": row[13]
            }
            spots.append(spot)
        
        # Get total count for pagination
        cursor.execute(f"SELECT COUNT(*) FROM spots WHERE {where_clause}")
        total = cursor.fetchone()[0]
    
    result = {
        "spots": spots,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total
        }
    }
    
    # Cache the result
    set_cache(cache_key, result)
    
    return result

@app.get("/api/spots/search", response_class=ORJSONResponse)
async def search_spots(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100)
):
    """Search spots by name or description"""
    
    # Check cache
    cache_key = get_cache_key("search", {"q": q, "limit": limit})
    cached = get_cached_response(cache_key)
    if cached:
        return cached
    
    query = """
        SELECT id, name, type, latitude, longitude, description, department
        FROM spots 
        WHERE name LIKE ? OR description LIKE ?
        ORDER BY 
            CASE 
                WHEN name LIKE ? THEN 1 
                ELSE 2 
            END,
            beauty_rating DESC
        LIMIT ?
    """
    
    search_pattern = f"%{q}%"
    
    with get_db_connection(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (search_pattern, search_pattern, search_pattern, limit))
        
        spots = []
        for row in cursor.fetchall():
            spots.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "description": row[5],
                "department": row[6]
            })
    
    result = {"results": spots, "query": q}
    set_cache(cache_key, result)
    
    return result

@app.get("/api/spots/nearby", response_class=ORJSONResponse)
async def get_nearby_spots(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(10, ge=0.1, le=50, description="Radius in km"),
    limit: int = Query(10, ge=1, le=50)
):
    """Get spots near a location using Haversine formula"""
    
    # Haversine SQL calculation
    query = """
        SELECT 
            id, name, type, latitude, longitude, description,
            (6371 * acos(cos(radians(?)) * cos(radians(latitude)) * 
            cos(radians(longitude) - radians(?)) + sin(radians(?)) * 
            sin(radians(latitude)))) AS distance
        FROM spots
        HAVING distance < ?
        ORDER BY distance
        LIMIT ?
    """
    
    with get_db_connection(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (lat, lng, lat, radius, limit))
        
        spots = []
        for row in cursor.fetchall():
            spots.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "description": row[5],
                "distance_km": round(row[6], 2)
            })
    
    return {"spots": spots, "center": {"lat": lat, "lng": lng}, "radius_km": radius}

@app.get("/api/stats", response_class=ORJSONResponse)
async def get_stats(response: Response):
    """Get statistics with caching"""
    
    cache_key = "stats"
    cached = get_cached_response(cache_key)
    if cached:
        response.headers["X-Cache"] = "HIT"
        return cached
    
    response.headers["X-Cache"] = "MISS"
    
    with get_db_connection(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        
        # Get counts by type
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM spots 
            GROUP BY type 
            ORDER BY count DESC
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get counts by department
        cursor.execute("""
            SELECT department, COUNT(*) as count 
            FROM spots 
            GROUP BY department 
            ORDER BY count DESC
        """)
        by_department = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM spots")
        total = cursor.fetchone()[0]
        
        # Get average ratings
        cursor.execute("""
            SELECT 
                AVG(beauty_rating) as avg_beauty,
                AVG(popularity) as avg_popularity,
                AVG(difficulty) as avg_difficulty
            FROM spots
        """)
        row = cursor.fetchone()
        
        stats = {
            "total_spots": total,
            "by_type": by_type,
            "by_department": by_department,
            "averages": {
                "beauty_rating": round(row[0], 2) if row[0] else 0,
                "popularity": round(row[1], 2) if row[1] else 0,
                "difficulty": round(row[2], 2) if row[2] else 0
            }
        }
    
    set_cache(cache_key, stats)
    return stats

# Department-specific endpoints (simplified)
for dept_code, dept_info in DEPARTMENT_INFO.items():
    dept_name = dept_info["name"].lower().replace("-", "_")
    
    @app.get(f"/api/spots/{dept_name}", 
             response_class=ORJSONResponse,
             tags=["Departments"],
             name=f"get_{dept_name}_spots")
    async def get_department_spots(
        department=dept_code,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0)
    ):
        """Get spots for a specific department"""
        return await get_quality_spots(
            response=Response(),
            department=department,
            limit=limit,
            offset=offset
        )

# Include routers
app.include_router(mapping_france.router, prefix="/api", tags=["mapping"])
app.include_router(ign_data.router, prefix="/api", tags=["ign"])
app.include_router(code_analysis.router, prefix="/api", tags=["analysis"])

# Cache cleanup task
@app.on_event("startup")
async def startup_event():
    """Initialize app"""
    logger.info(f"API starting up - Database: {DB_PATH}")
    logger.info(f"Compression: Enabled, Cache TTL: {cache_ttl}s")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)