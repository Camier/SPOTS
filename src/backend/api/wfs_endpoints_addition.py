#!/usr/bin/env python3
"""
Additional WFS endpoints for IGN real-time vector data integration
Add these endpoints to your existing ign_data.py router
"""

# Add these imports to your existing ign_data.py
from ..services.ign_wfs_service import IGNWFSService

# Initialize WFS service (add this after your existing ign_service initialization)
wfs_service = IGNWFSService()

# ADD THESE NEW ENDPOINTS TO YOUR EXISTING ROUTER:


@router.get("/wfs/capabilities")
async def get_wfs_capabilities():
    """Get IGN WFS service capabilities and available layers"""
    capabilities = wfs_service.get_capabilities()

    return {
        "service": "IGN WFS-Geoportail",
        "description": "Real-time vector data from IGN Géoplateforme",
        "capabilities": capabilities,
        "integration_status": "Active",
        "supported_queries": [
            "Administrative boundaries",
            "Transport networks",
            "Hydrography features",
            "Spot surroundings analysis",
        ],
    }


@router.get("/spots/{spot_id}/wfs-analysis")
async def get_spot_wfs_analysis(
    spot_id: int, radius: int = Query(1500, description="Analysis radius in meters", le=5000)
):
    """
    Get real-time WFS analysis for a specific spot

    Uses live IGN vector data for:
    - Administrative context (commune, department)
    - Transport network (trails, paths, roads)
    - Hydrography (rivers, lakes, springs)
    - Accessibility scoring
    """
    import sqlite3

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get spot coordinates
    cursor.execute("SELECT * FROM spots WHERE id = ?", (spot_id,))
    spot = cursor.fetchone()

    if not spot:
        conn.close()
        raise HTTPException(status_code=404, detail="Spot not found")

    spot_dict = dict(spot)
    conn.close()

    if not (spot_dict.get("latitude") and spot_dict.get("longitude")):
        raise HTTPException(status_code=400, detail="Spot has no coordinates")

    # Perform WFS analysis
    analysis = wfs_service.analyze_spot_surroundings(spot_id, (spot_dict["latitude"], spot_dict["longitude"]), radius)

    return {
        "spot": {
            "id": spot_dict["id"],
            "name": spot_dict["name"],
            "type": spot_dict["type"],
            "coordinates": {"latitude": spot_dict["latitude"], "longitude": spot_dict["longitude"]},
        },
        "wfs_analysis": analysis,
        "data_source": "IGN Géoplateforme WFS (real-time)",
        "analysis_timestamp": analysis["timestamp"],
    }


@router.get("/wfs/transport")
async def query_transport_network(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: int = Query(1000, description="Search radius in meters", le=5000),
    transport_type: str = Query("all", regex="^(all|hiking|cycling|roads)$"),
):
    """Query transport networks around coordinates using WFS"""

    result = wfs_service.query_transport_network((lat, lon), radius, transport_type)

    return {
        "query_parameters": {"coordinates": [lat, lon], "radius": radius, "transport_type": transport_type},
        "result": result,
        "data_source": "IGN Géoplateforme WFS",
    }


@router.get("/wfs/hydrography")
async def query_water_features(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: int = Query(2000, description="Search radius in meters", le=5000),
    feature_type: str = Query("all", regex="^(all|rivers|lakes|springs)$"),
):
    """Query water features around coordinates using WFS"""

    result = wfs_service.query_hydrography((lat, lon), radius, feature_type)

    return {
        "query_parameters": {"coordinates": [lat, lon], "radius": radius, "feature_type": feature_type},
        "result": result,
        "data_source": "IGN Géoplateforme WFS",
    }


@router.get("/wfs/administrative")
async def query_administrative_boundaries(
    bbox: str = Query(..., description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    level: str = Query("commune", regex="^(commune|department|region)$"),
):
    """Query administrative boundaries using WFS"""

    try:
        # Parse bounding box
        bbox_coords = [float(x) for x in bbox.split(",")]
        if len(bbox_coords) != 4:
            raise ValueError("Invalid bbox format")

        result = wfs_service.query_administrative_boundaries(tuple(bbox_coords), level)

        return {
            "query_parameters": {"bounding_box": bbox_coords, "administrative_level": level},
            "result": result,
            "data_source": "IGN Géoplateforme WFS",
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bbox format. Use: min_lon,min_lat,max_lon,max_lat")
