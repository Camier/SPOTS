#!/usr/bin/env python3
"""API endpoints for mapping features using Ola Maps"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
import os
import logging
from pydantic import BaseModel, Field

from ..scrapers.geocoding_mixin import GeocodingMixin

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize geocoding service
geocoder = GeocodingMixin()


# Pydantic models
class GeocodingRequest(BaseModel):
    address: str = Field(..., description="Address to geocode")


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class GeocodingResponse(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str
    confidence: float


class ElevationRequest(BaseModel):
    latitude: float
    longitude: float


class ElevationResponse(BaseModel):
    latitude: float
    longitude: float
    elevation: float


class NearbySearchRequest(BaseModel):
    latitude: float
    longitude: float
    radius: int = Field(default=1000, le=5000, description="Search radius in meters")
    category: Optional[str] = Field(None, description="Category to filter by")


class DirectionsRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    mode: str = Field(default="driving", description="Travel mode: driving, walking, cycling")


@router.post("/geocode", response_model=GeocodingResponse)
async def geocode_address(request: GeocodingRequest):
    """Convert an address to coordinates"""
    if not geocoder.ola_api_key:
        raise HTTPException(status_code=503, detail="Geocoding service not configured")

    result = geocoder.geocode_address(request.address)
    if not result:
        raise HTTPException(status_code=404, detail="Address not found")

    return GeocodingResponse(
        latitude=result["latitude"],
        longitude=result["longitude"],
        formatted_address=result["formatted_address"],
        confidence=result["confidence"],
    )


@router.post("/reverse-geocode")
async def reverse_geocode(coords: Coordinates):
    """Convert coordinates to an address"""
    if not geocoder.ola_api_key:
        raise HTTPException(status_code=503, detail="Geocoding service not configured")

    address = geocoder.reverse_geocode(coords.latitude, coords.longitude)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found for coordinates")

    return {"address": address, "latitude": coords.latitude, "longitude": coords.longitude}


@router.post("/elevation", response_model=ElevationResponse)
async def get_elevation(request: ElevationRequest):
    """Get elevation for coordinates"""
    if not geocoder.ola_api_key:
        raise HTTPException(status_code=503, detail="Elevation service not configured")

    elevation = geocoder.get_elevation(request.latitude, request.longitude)
    if elevation is None:
        raise HTTPException(status_code=404, detail="Elevation data not available")

    return ElevationResponse(latitude=request.latitude, longitude=request.longitude, elevation=elevation)


@router.post("/nearby-search")
async def nearby_search(request: NearbySearchRequest):
    """Find nearby places"""
    if not geocoder.ola_api_key:
        raise HTTPException(status_code=503, detail="Search service not configured")

    places = geocoder.find_nearby_places(request.latitude, request.longitude, request.radius, request.category)

    return {
        "location": {"latitude": request.latitude, "longitude": request.longitude},
        "radius": request.radius,
        "category": request.category,
        "count": len(places),
        "places": places,
    }


@router.get("/spots/nearest")
async def get_nearest_spots(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    limit: int = Query(10, le=50, description="Maximum number of spots to return"),
    max_distance: float = Query(50, le=200, description="Maximum distance in km"),
):
    """Get nearest spots to a location"""
    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate distance using Haversine formula in SQL
    cursor.execute(
        """
        SELECT *,
            (6371 * acos(
                cos(radians(?)) * cos(radians(latitude)) * 
                cos(radians(longitude) - radians(?)) + 
                sin(radians(?)) * sin(radians(latitude))
            )) AS distance_km
        FROM spots
        WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL
        AND distance_km <= ?
        ORDER BY distance_km
        LIMIT ?
    """,
        (lat, lon, lat, max_distance, limit),
    )

    spots = []
    for row in cursor.fetchall():
        spot = dict(row)
        spots.append(spot)

    conn.close()

    return {
        "center": {"latitude": lat, "longitude": lon},
        "max_distance_km": max_distance,
        "count": len(spots),
        "spots": spots,
    }


@router.get("/spots/elevation-profile/{spot_id}")
async def get_spot_elevation_profile(spot_id: int):
    """Get elevation profile for routes to a spot"""
    if not geocoder.ola_api_key:
        raise HTTPException(status_code=503, detail="Elevation service not configured")

    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get spot coordinates
    cursor.execute(
        """
        SELECT id, name, latitude, longitude, elevation
        FROM spots WHERE id = ?
    """,
        (spot_id,),
    )

    spot = cursor.fetchone()
    conn.close()

    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    # If spot doesn't have elevation, get it
    if spot["elevation"] is None:
        elevation = geocoder.get_elevation(spot["latitude"], spot["longitude"])
        if elevation:
            # Update database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE spots SET elevation = ? WHERE id = ?", (elevation, spot_id))
            conn.commit()
            conn.close()
    else:
        elevation = spot["elevation"]

    return {"spot": dict(spot), "elevation": elevation, "elevation_category": get_elevation_category(elevation)}


def get_elevation_category(elevation: Optional[float]) -> str:
    """Categorize elevation for activity recommendations"""
    if elevation is None:
        return "unknown"
    elif elevation < 200:
        return "lowland"
    elif elevation < 500:
        return "hills"
    elif elevation < 1000:
        return "low_mountain"
    elif elevation < 2000:
        return "mountain"
    else:
        return "high_mountain"


@router.get("/stats/elevation")
async def get_elevation_statistics():
    """Get elevation statistics for all spots"""
    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get statistics
    cursor.execute(
        """
        SELECT 
            COUNT(*) as total_spots,
            COUNT(elevation) as spots_with_elevation,
            MIN(elevation) as min_elevation,
            MAX(elevation) as max_elevation,
            AVG(elevation) as avg_elevation,
            COUNT(CASE WHEN elevation < 200 THEN 1 END) as lowland,
            COUNT(CASE WHEN elevation >= 200 AND elevation < 500 THEN 1 END) as hills,
            COUNT(CASE WHEN elevation >= 500 AND elevation < 1000 THEN 1 END) as low_mountain,
            COUNT(CASE WHEN elevation >= 1000 AND elevation < 2000 THEN 1 END) as mountain,
            COUNT(CASE WHEN elevation >= 2000 THEN 1 END) as high_mountain
        FROM spots
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    )

    stats = cursor.fetchone()
    conn.close()

    return {
        "total_spots": stats[0],
        "spots_with_elevation": stats[1],
        "coverage_percentage": (stats[1] / stats[0] * 100) if stats[0] > 0 else 0,
        "elevation_range": {"min": stats[2], "max": stats[3], "average": stats[4]},
        "categories": {
            "lowland": {"count": stats[5], "range": "< 200m"},
            "hills": {"count": stats[6], "range": "200-500m"},
            "low_mountain": {"count": stats[7], "range": "500-1000m"},
            "mountain": {"count": stats[8], "range": "1000-2000m"},
            "high_mountain": {"count": stats[9], "range": "> 2000m"},
        },
    }
