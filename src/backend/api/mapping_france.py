#!/usr/bin/env python3
"""API endpoints for mapping features using French BAN and IGN services"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
import logging
from pydantic import BaseModel, Field
from pathlib import Path

from ..scrapers.geocoding_france import FrenchGeocodingMixin, OccitanieGeocoder

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize geocoding services
geocoder = OccitanieGeocoder()


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
    city: Optional[str] = None
    postcode: Optional[str] = None
    department: Optional[str] = None
    precision: Optional[str] = Field(None, description="Service used: premium, ban, or legacy")
    # Premium-specific fields
    housenumber: Optional[str] = None
    street: Optional[str] = None
    entrance: Optional[str] = None
    quality: Optional[str] = None


class ElevationRequest(BaseModel):
    latitude: float
    longitude: float


class ElevationResponse(BaseModel):
    latitude: float
    longitude: float
    elevation: float
    source: str = Field(description="Data source (IGN or Open-Elevation)")


class PlaceSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    latitude: Optional[float] = Field(None, description="Latitude for location bias")
    longitude: Optional[float] = Field(None, description="Longitude for location bias")
    limit: int = Field(default=10, le=50, description="Maximum results")


@router.post("/geocode", response_model=GeocodingResponse)
async def geocode_address(request: GeocodingRequest):
    """
    Convert an address to coordinates using geocoding services
    Priority: ADRESSE-PREMIUM (if enabled) -> BAN -> Legacy BAN

    Premium service provides:
    - Sub-meter accuracy for addresses
    - Better rural/remote location coverage
    - Historical names recognition
    - Building entrance precision
    """
    result = geocoder.geocode_occitanie(request.address)
    if not result:
        raise HTTPException(status_code=404, detail="Address not found or not in Occitanie")

    return GeocodingResponse(**result)


@router.post("/reverse-geocode")
async def reverse_geocode(coords: Coordinates):
    """
    Convert coordinates to an address using French BAN API
    Free service, no API key required
    """
    address = geocoder.reverse_geocode(coords.latitude, coords.longitude)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found for coordinates")

    # Check if in Occitanie
    is_occitanie = geocoder.is_in_occitanie(coords.latitude, coords.longitude)

    return {
        "address": address,
        "latitude": coords.latitude,
        "longitude": coords.longitude,
        "in_occitanie": is_occitanie,
    }


@router.post("/elevation", response_model=ElevationResponse)
async def get_elevation(request: ElevationRequest):
    """
    Get elevation for coordinates using IGN or Open-Elevation
    Free service, no API key required
    """
    # Try IGN first
    elevation = geocoder.get_elevation_ign(request.latitude, request.longitude)
    source = "IGN"

    # Fallback to Open-Elevation
    if elevation is None:
        elevation = geocoder.get_elevation_open(request.latitude, request.longitude)
        source = "Open-Elevation"

    if elevation is None:
        raise HTTPException(status_code=404, detail="Elevation data not available")

    return ElevationResponse(latitude=request.latitude, longitude=request.longitude, elevation=elevation, source=source)


@router.post("/search-places")
async def search_places(request: PlaceSearchRequest):
    """
    Search for places using French BAN API
    Can be biased towards a location if coordinates provided
    """
    places = geocoder.search_places_ban(request.query, request.latitude, request.longitude, request.limit)

    # Filter to Occitanie if we have results
    occitanie_places = []
    for place in places:
        if place.get("latitude") and place.get("longitude"):
            if geocoder.is_in_occitanie(place["latitude"], place["longitude"]):
                place["in_occitanie"] = True
                occitanie_places.append(place)

    return {
        "query": request.query,
        "total_results": len(places),
        "occitanie_results": len(occitanie_places),
        "places": occitanie_places[: request.limit],
    }


@router.get("/spots/nearest")
async def get_nearest_spots(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    limit: int = Query(10, le=50, description="Maximum number of spots to return"),
    max_distance: float = Query(50, le=200, description="Maximum distance in km"),
):
    """Get nearest spots to a location using Haversine formula"""
    import sqlite3

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

    # Get address for the search location
    search_address = geocoder.reverse_geocode(lat, lon) or "Unknown location"

    return {
        "center": {"latitude": lat, "longitude": lon, "address": search_address},
        "max_distance_km": max_distance,
        "count": len(spots),
        "spots": spots,
    }


@router.get("/spots/elevation-profile/{spot_id}")
async def get_spot_elevation_profile(spot_id: int):
    """Get elevation profile for a specific spot"""
    import sqlite3

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get spot coordinates
    cursor.execute(
        """
        SELECT id, name, latitude, longitude, elevation, address
        FROM spots WHERE id = ?
    """,
        (spot_id,),
    )

    spot = cursor.fetchone()

    if not spot:
        conn.close()
        raise HTTPException(status_code=404, detail="Spot not found")

    spot_dict = dict(spot)

    # If spot doesn't have elevation, get it
    if spot_dict["elevation"] is None and spot_dict["latitude"] and spot_dict["longitude"]:
        elevation = geocoder.get_elevation(spot_dict["latitude"], spot_dict["longitude"])
        if elevation:
            # Update database
            cursor.execute("UPDATE spots SET elevation = ? WHERE id = ?", (elevation, spot_id))
            conn.commit()
            spot_dict["elevation"] = elevation

    # If spot doesn't have address, get it
    if not spot_dict["address"] and spot_dict["latitude"] and spot_dict["longitude"]:
        address = geocoder.reverse_geocode(spot_dict["latitude"], spot_dict["longitude"])
        if address:
            cursor.execute("UPDATE spots SET address = ? WHERE id = ?", (address, spot_id))
            conn.commit()
            spot_dict["address"] = address

    conn.close()

    return {"spot": spot_dict, "elevation_category": get_elevation_category(spot_dict.get("elevation"))}


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

    # Get department statistics
    cursor.execute(
        """
        SELECT 
            SUBSTR(address, -2) as dept_code,
            COUNT(*) as count,
            AVG(elevation) as avg_elevation
        FROM spots
        WHERE address IS NOT NULL
        GROUP BY dept_code
        ORDER BY count DESC
    """
    )

    dept_stats = cursor.fetchall()
    conn.close()

    return {
        "total_spots": stats[0],
        "spots_with_elevation": stats[1],
        "coverage_percentage": (stats[1] / stats[0] * 100) if stats[0] > 0 else 0,
        "elevation_range": {"min": stats[2], "max": stats[3], "average": stats[4]},
        "categories": {
            "lowland": {"count": stats[5], "range": "< 200m", "description": "Plaines et vallées"},
            "hills": {"count": stats[6], "range": "200-500m", "description": "Collines"},
            "low_mountain": {"count": stats[7], "range": "500-1000m", "description": "Moyenne montagne"},
            "mountain": {"count": stats[8], "range": "1000-2000m", "description": "Montagne"},
            "high_mountain": {"count": stats[9], "range": "> 2000m", "description": "Haute montagne"},
        },
        "by_department": [{"code": row[0], "count": row[1], "avg_elevation": row[2]} for row in dept_stats if row[0]],
    }


@router.get("/departments")
async def get_occitanie_departments():
    """Get list of Occitanie departments with their codes"""
    return {
        "region": "Occitanie",
        "departments": [{"code": code, "name": name} for code, name in OccitanieGeocoder.OCCITANIE_DEPARTMENTS.items()],
        "total": len(OccitanieGeocoder.OCCITANIE_DEPARTMENTS),
    }


@router.get("/geocoding-status")
async def get_geocoding_status():
    """Get the current status of geocoding services"""
    import os

    return {
        "services": {
            "premium": {
                "enabled": geocoder.premium_service.enabled,
                "name": "ADRESSE-PREMIUM",
                "description": "Premium geocoding with sub-meter accuracy",
                "features": [
                    "Sub-meter accuracy",
                    "Rural/remote locations",
                    "Historical names",
                    "Building entrances",
                    "POI search",
                    "Batch operations",
                ],
                "authenticated": (
                    geocoder.premium_service.access_token is not None if geocoder.premium_service.enabled else False
                ),
            },
            "ban": {
                "enabled": True,
                "name": "Base Adresse Nationale (BAN)",
                "description": "Standard French geocoding service",
                "endpoint": geocoder.ban_base_url,
            },
            "legacy_ban": {
                "enabled": True,
                "name": "Legacy BAN API",
                "description": "Fallback geocoding service",
                "endpoint": geocoder.ban_legacy_url,
            },
            "ign_elevation": {
                "enabled": True,
                "name": "IGN Elevation Service",
                "description": "French national elevation data",
                "endpoint": geocoder.ign_elevation_url,
            },
            "open_elevation": {
                "enabled": True,
                "name": "Open-Elevation",
                "description": "Global elevation fallback",
                "endpoint": "https://api.open-elevation.com",
            },
        },
        "hierarchy": [
            "ADRESSE-PREMIUM (if enabled)",
            "BAN (IGN hosted)",
            "Legacy BAN (data.gouv.fr)",
            "Open-Elevation (for elevation only)",
        ],
    }


@router.get("/validate-location")
async def validate_location(lat: float, lon: float):
    """Check if coordinates are in Occitanie region"""
    is_in_occitanie = geocoder.is_in_occitanie(lat, lon)
    dept_code = geocoder.get_department_code(lat, lon)
    address = geocoder.reverse_geocode(lat, lon)

    return {
        "coordinates": {"latitude": lat, "longitude": lon},
        "in_occitanie": is_in_occitanie,
        "department_code": dept_code,
        "department_name": OccitanieGeocoder.OCCITANIE_DEPARTMENTS.get(dept_code, "Unknown"),
        "address": address,
    }


@router.post("/search-poi")
async def search_poi(
    query: str = Query(..., description="POI search query (e.g., refuge, cascade, grotte)"),
    lat: float = Query(..., description="Center latitude"),
    lon: float = Query(..., description="Center longitude"),
    radius: int = Query(5000, le=50000, description="Search radius in meters"),
):
    """
    Search for Points of Interest (Premium feature)
    Only available when ADRESSE-PREMIUM is enabled

    Useful for finding:
    - Mountain refuges (refuge)
    - Waterfalls (cascade)
    - Caves (grotte)
    - Lakes (lac)
    - Viewpoints (belvédère)
    """
    if not geocoder.premium_service.enabled:
        raise HTTPException(status_code=503, detail="POI search requires ADRESSE-PREMIUM service to be enabled")

    pois = geocoder.premium_service.search_poi_premium(query, lat, lon, radius)

    # Filter to Occitanie if possible
    occitanie_pois = []
    for poi in pois:
        if poi.get("latitude") and poi.get("longitude"):
            if geocoder.is_in_occitanie(poi["latitude"], poi["longitude"]):
                poi["in_occitanie"] = True
                occitanie_pois.append(poi)
            else:
                poi["in_occitanie"] = False
                occitanie_pois.append(poi)

    return {
        "query": query,
        "center": {"latitude": lat, "longitude": lon},
        "radius_meters": radius,
        "total_results": len(pois),
        "occitanie_results": sum(1 for p in occitanie_pois if p.get("in_occitanie")),
        "pois": occitanie_pois,
    }
