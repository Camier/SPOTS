#!/usr/bin/env python3
"""
Refactored Main API - Cleaner, more maintainable code
"""

from fastapi import FastAPI, HTTPException, Query, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict
from dotenv import load_dotenv
from src.backend.core.logging_config import logger

# Load environment variables
load_dotenv()

# Import API routers
from src.backend.api import mapping_france
# Temporarily disabled due to missing dependencies
# from src.backend.api import ign_data, code_analysis

# Create FastAPI app
app = FastAPI(
    title="Spots Secrets Occitanie API",
    description="Discover secret spots across Occitanie departments",
    version="2.3.0",
)

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
}


# Database connection helper
@contextmanager
def get_db():
    """Database connection context manager with connection reuse"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        # Enable query optimization
        conn.execute("PRAGMA optimize")
        yield conn
    finally:
        conn.close()


def build_where_clause(bounds: Dict) -> str:
    """Build WHERE clause from boundary conditions"""
    conditions = []
    if "lat_min" in bounds:
        conditions.append(f"latitude > {bounds['lat_min']}")
    if "lat_max" in bounds:
        conditions.append(f"latitude < {bounds['lat_max']}")
    if "lng_min" in bounds:
        conditions.append(f"longitude > {bounds['lng_min']}")
    if "lng_max" in bounds:
        conditions.append(f"longitude < {bounds['lng_max']}")

    return " AND ".join(conditions) if conditions else "1=1"


# Include API routers
app.include_router(mapping_france.router, prefix="/api/mapping", tags=["mapping"])
# Temporarily disabled due to missing dependencies
# app.include_router(ign_data.router, prefix="/api/ign", tags=["IGN OpenData"])
# app.include_router(code_analysis.router, prefix="/api/code", tags=["Code Analysis"])


@app.on_event("startup")
async def startup_event():
    """Create database indexes on startup"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Create indexes if they don't exist
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_spots_location 
            ON spots(latitude, longitude)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_spots_type 
            ON spots(type)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_spots_department 
            ON spots(department)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_spots_confidence 
            ON spots(confidence_score)
        """
        )
        conn.commit()
        logger.info("✅ Database indexes created/verified")


@app.get("/")
def read_root():
    return {
        "message": "Spots Secrets Occitanie API",
        "version": "2.3.0",
        "coverage": "8 departments",
        "total_spots": 817,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            count = cursor.execute("SELECT COUNT(*) FROM spots").fetchone()[0]
        return {"status": "healthy", "spots_count": count}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/api/config")
def get_config():
    """Get frontend configuration (without exposing sensitive data)"""
    return {
        "geocoding": {"service": "BAN", "premium_enabled": False},
        "api_base_url": "http://localhost:8000",
        "map_providers": ["IGN", "OpenStreetMap", "Satellite"],
    }


@app.get("/api/spots")
async def get_spots(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    type: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
):
    """Get all spots with filtering and pagination"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Build query with filters
        where_conditions = []
        params = []

        if type:
            where_conditions.append("type = ?")
            params.append(type)

        if min_confidence is not None:
            where_conditions.append("confidence_score >= ?")
            params.append(min_confidence)

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM spots{where_clause}"
        total = cursor.execute(count_query, params).fetchone()["total"]

        # Get spots with pagination
        query = f"""
            SELECT id, name, latitude, longitude, type, description, 
                   weather_sensitive, confidence_score, elevation, 
                   address, department
            FROM spots
            {where_clause}
            ORDER BY confidence_score DESC, id
            LIMIT ? OFFSET ?
        """

        cursor.execute(query, params + [limit, offset])
        spots = [dict(row) for row in cursor.fetchall()]

    return {"total": total, "limit": limit, "offset": offset, "spots": spots}


@app.get("/api/spots/quality")
async def get_quality_spots(
    min_confidence: float = Query(0.7, ge=0, le=1), exclude_unknown: bool = True, limit: int = Query(500, ge=1, le=1000)
):
    """Get high-quality filtered spots with scoring"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Build query with quality filters
        query = """
            SELECT id, name, latitude, longitude, type, description, 
                   weather_sensitive, confidence_score, elevation,
                   address, department,
                   CASE 
                       WHEN description IS NOT NULL THEN length(description)
                       ELSE 0
                   END as description_length,
                   -- Calculate quality score in SQL
                   (confidence_score * 100 + 
                    CASE WHEN description IS NOT NULL THEN MIN(20, length(description) / 10) ELSE 0 END +
                    CASE WHEN type != 'unknown' THEN 10 ELSE 0 END +
                    CASE WHEN elevation IS NOT NULL THEN 5 ELSE 0 END +
                    CASE WHEN address IS NOT NULL THEN 5 ELSE 0 END
                   ) as quality_score
            FROM spots
            WHERE confidence_score >= ?
        """

        params = [min_confidence]

        if exclude_unknown:
            query += " AND type != 'unknown'"

        query += " ORDER BY quality_score DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        spots = [dict(row) for row in cursor.fetchall()]

        # Add boolean flags
        for spot in spots:
            spot["has_description"] = bool(spot.get("description"))
            spot["has_elevation"] = spot.get("elevation") is not None

    return {
        "total": len(spots),
        "filters": {"min_confidence": min_confidence, "exclude_unknown": exclude_unknown},
        "spots": spots,
    }


@app.get("/api/spots/{spot_id}")
async def get_spot(spot_id: int = PathParam(..., ge=1)):
    """Get specific spot by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM spots WHERE id = ?", (spot_id,))
        spot = cursor.fetchone()

        if spot:
            return dict(spot)
        else:
            raise HTTPException(status_code=404, detail="Spot not found")


@app.get("/api/stats")
async def get_stats():
    """Get regional statistics by department"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Initialize stats
        stats = {
            "total_spots": cursor.execute("SELECT COUNT(*) FROM spots").fetchone()[0],
            "departments": {},
            "spots_by_type": {},
            "weather_sensitive": 0,
        }

        # Count spots by department using unified logic
        for dept_code, dept_info in DEPARTMENT_INFO.items():
            where_clause = build_where_clause(dept_info["bounds"])
            count = cursor.execute(f"SELECT COUNT(*) FROM spots WHERE {where_clause}").fetchone()[0]

            stats["departments"][dept_code] = {"name": dept_info["name"], "count": count}

        # Spots by type
        type_counts = cursor.execute(
            """
            SELECT type, COUNT(*) as count 
            FROM spots 
            GROUP BY type 
            ORDER BY count DESC
        """
        ).fetchall()
        stats["spots_by_type"] = {row[0]: row[1] for row in type_counts}

        # Weather sensitive spots
        stats["weather_sensitive"] = cursor.execute(
            "SELECT COUNT(*) FROM spots WHERE weather_sensitive = 1"
        ).fetchone()[0]

        # Average confidence score
        avg_confidence = cursor.execute("SELECT AVG(confidence_score) FROM spots").fetchone()[0]
        stats["average_confidence"] = round(avg_confidence, 2) if avg_confidence else 0

    return stats


@app.get("/api/spots/department/{dept_code}")
async def get_spots_by_department(
    dept_code: str = PathParam(..., regex="^(09|12|31|32|46|65|81|82)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get spots for a specific department"""
    if dept_code not in DEPARTMENT_INFO:
        raise HTTPException(status_code=404, detail="Department not found")

    dept_info = DEPARTMENT_INFO[dept_code]
    where_clause = build_where_clause(dept_info["bounds"])

    with get_db() as conn:
        cursor = conn.cursor()

        # Get total count
        total = cursor.execute(f"SELECT COUNT(*) FROM spots WHERE {where_clause}").fetchone()[0]

        # Get spots with pagination
        cursor.execute(
            f"""
            SELECT id, name, latitude, longitude, type, description, 
                   weather_sensitive, confidence_score, elevation, address
            FROM spots
            WHERE {where_clause}
            ORDER BY confidence_score DESC, id
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )

        spots = [dict(row) for row in cursor.fetchall()]

    return {
        "department": {"code": dept_code, "name": dept_info["name"]},
        "total": total,
        "limit": limit,
        "offset": offset,
        "spots": spots,
    }


@app.get("/api/spots/search")
async def search_spots(q: str = Query(..., min_length=2), limit: int = Query(50, ge=1, le=200)):
    """Search spots by name or description"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Search in name and description
        search_pattern = f"%{q}%"
        cursor.execute(
            """
            SELECT id, name, latitude, longitude, type, description,
                   confidence_score, department
            FROM spots
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY 
                CASE WHEN name LIKE ? THEN 1 ELSE 2 END,
                confidence_score DESC
            LIMIT ?
        """,
            (search_pattern, search_pattern, search_pattern, limit),
        )

        spots = [dict(row) for row in cursor.fetchall()]

    return {"query": q, "count": len(spots), "spots": spots}


# Error handler
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return {"error": "Internal server error", "detail": str(exc)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
