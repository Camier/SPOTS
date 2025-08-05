#!/usr/bin/env python3
"""API endpoints for IGN OpenData integration"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
import logging
from pathlib import Path

from ..scrapers.ign_opendata import IGNOpenDataService
from ..services.ign_wfs_service import IGNWFSService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize IGN service
ign_service = IGNOpenDataService()
# Initialize WFS service
wfs_service = IGNWFSService()


@router.get("/spots/{spot_id}/environment")
async def get_spot_environment(
    spot_id: int, radius: int = Query(1000, description="Analysis radius in meters", le=5000)
):
    """
    Get environmental analysis for a specific spot using IGN data

    Includes:
    - Forest coverage and types
    - Elevation profile and terrain difficulty
    - Land use classification
    - Accessibility information
    """
    import sqlite3

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get spot
    cursor.execute("SELECT * FROM spots WHERE id = ?", (spot_id,))
    spot = cursor.fetchone()

    if not spot:
        conn.close()
        raise HTTPException(status_code=404, detail="Spot not found")

    spot_dict = dict(spot)
    conn.close()

    # Get environmental analysis
    if spot_dict.get("latitude") and spot_dict.get("longitude"):
        env_analysis = ign_service.analyze_spot_environment(spot_dict["latitude"], spot_dict["longitude"], radius)

        return {
            "spot": {
                "id": spot_dict["id"],
                "name": spot_dict["name"],
                "type": spot_dict["type"],
                "coordinates": {"latitude": spot_dict["latitude"], "longitude": spot_dict["longitude"]},
            },
            "environment": env_analysis,
        }
    else:
        raise HTTPException(status_code=400, detail="Spot has no coordinates")


@router.get("/spots/enriched")
async def get_enriched_spots(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    type: Optional[str] = None,
    min_forest_coverage: Optional[int] = Query(None, ge=0, le=100),
    terrain_difficulty: Optional[str] = Query(None, regex="^(Easy|Moderate|Challenging|Expert)$"),
):
    """
    Get spots enriched with IGN environmental data

    Filter options:
    - type: Spot type (cave, waterfall, etc.)
    - min_forest_coverage: Minimum forest coverage percentage
    - terrain_difficulty: Terrain difficulty level
    """
    import sqlite3

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query
    where_clauses = []
    params = []

    if type:
        where_clauses.append("type = ?")
        params.append(type)

    where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Get spots
    cursor.execute(
        f"""
        SELECT * FROM spots
        {where_clause}
        ORDER BY confidence_score DESC
        LIMIT ? OFFSET ?
    """,
        params + [limit, offset],
    )

    spots = []
    for row in cursor.fetchall():
        spot_dict = dict(row)

        # Enrich with IGN data (in production, this would be cached)
        if spot_dict.get("latitude") and spot_dict.get("longitude"):
            enriched = ign_service.enrich_spot_data(spot_dict)

            # Apply filters
            if min_forest_coverage is not None:
                forest_coverage = enriched.get("environment", {}).get("forest", {}).get("coverage_percent", 0)
                if forest_coverage < min_forest_coverage:
                    continue

            if terrain_difficulty:
                terrain = enriched.get("environment", {}).get("terrain", {}).get("level")
                if terrain != terrain_difficulty:
                    continue

            spots.append(enriched)

    conn.close()

    return {
        "total": len(spots),
        "limit": limit,
        "offset": offset,
        "filters": {"type": type, "min_forest_coverage": min_forest_coverage, "terrain_difficulty": terrain_difficulty},
        "spots": spots,
    }


@router.get("/map-layers/ign")
async def get_ign_map_layers():
    """
    Get comprehensive IGN map layer configurations for frontend

    Returns WMTS URLs and configuration for multiple categories:
    - Base maps (satellite, topographic)
    - Terrain & Nature
    - Infrastructure
    - Administrative
    - Water features
    - Tourism & Services
    - Historical
    """
    layers = ign_service.get_map_layers()

    # Add extensive additional layers organized by category
    layers.update(
        {
            # Base map alternatives
            "scan25": {
                "name": "Carte topographique 1:25000",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg",
                "attribution": "© IGN SCAN25",
                "opacity": 1.0,
                "type": "base",
                "category": "base_maps",
            },
            "plan_ign": {
                "name": "Plan IGN v2",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 1.0,
                "type": "base",
                "category": "base_maps",
            },
            # Nature & Environment layers
            "protected_areas": {
                "name": "Zones protégées",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=PROTECTEDAREAS.ALL&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.5,
                "type": "overlay",
                "category": "nature",
            },
            "natura2000": {
                "name": "Sites Natura 2000",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=PROTECTEDAREAS.NATURA2000&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.6,
                "type": "overlay",
                "category": "nature",
            },
            "geology": {
                "name": "Carte géologique",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOLOGIE.GEOLOGIE&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© BRGM",
                "opacity": 0.5,
                "type": "overlay",
                "category": "nature",
            },
            # Infrastructure layers
            "hiking_trails": {
                "name": "Sentiers de randonnée",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=TRANSPORTNETWORKS.ROADS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.8,
                "type": "overlay",
                "category": "infrastructure",
            },
            "cycling_routes": {
                "name": "Pistes cyclables",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=TRANSPORTNETWORKS.ROADS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.8,
                "type": "overlay",
                "category": "infrastructure",
            },
            "transport": {
                "name": "Transport en commun",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=TRANSPORTNETWORKS.ROADS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.7,
                "type": "overlay",
                "category": "infrastructure",
            },
            # Water features
            "hydrography": {
                "name": "Hydrographie",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=HYDROGRAPHY.HYDROGRAPHY&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.7,
                "type": "overlay",
                "category": "water",
            },
            "flood_zones": {
                "name": "Zones inondables",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=RISQUES.INONDATIONS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.5,
                "type": "overlay",
                "category": "water",
            },
            # Administrative boundaries
            "cadastre": {
                "name": "Parcelles cadastrales",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.6,
                "type": "overlay",
                "category": "administrative",
            },
            "communes": {
                "name": "Limites communales",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=LIMITES_ADMINISTRATIVES_EXPRESS.LATEST&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.7,
                "type": "overlay",
                "category": "administrative",
            },
            # Tourism & Points of Interest
            "tourism_poi": {
                "name": "Points touristiques",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.8,
                "type": "overlay",
                "category": "tourism",
            },
            "emergency": {
                "name": "Services d'urgence",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.9,
                "type": "overlay",
                "category": "tourism",
            },
            # Historical layers
            "cassini": {
                "name": "Carte de Cassini (XVIIIe)",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.CASSINI&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg",
                "attribution": "© IGN",
                "opacity": 0.8,
                "type": "base",
                "category": "historical",
            },
            "etat_major": {
                "name": "Carte d'État-Major (1820-1866)",
                "url": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg",
                "attribution": "© IGN",
                "opacity": 0.8,
                "type": "base",
                "category": "historical",
            },
        }
    )

    return {
        "layers": layers,
        "categories": {
            "base_maps": "Fonds de carte",
            "nature": "Nature & Environnement",
            "infrastructure": "Infrastructure",
            "water": "Hydrographie",
            "administrative": "Administratif",
            "tourism": "Tourisme & Services",
            "historical": "Cartes historiques",
        },
        "description": "Comprehensive IGN layer collection for advanced mapping",
        "usage": "Organized by categories for better user experience",
    }


@router.get("/environment/statistics")
async def get_environment_statistics():
    """Get aggregated environmental statistics for all spots"""
    import sqlite3

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get spot count by presumed environment
    stats = {
        "total_spots": cursor.execute("SELECT COUNT(*) FROM spots").fetchone()[0],
        "by_elevation": {
            "lowland": 0,  # < 500m
            "hills": 0,  # 500-1000m
            "mountain": 0,  # 1000-2000m
            "high_mountain": 0,  # > 2000m
        },
        "by_type_environment": {},
        "accessibility_score": {"easy": 0, "moderate": 0, "difficult": 0},
    }

    # Categorize by elevation
    cursor.execute(
        """
        SELECT 
            CASE 
                WHEN elevation < 500 THEN 'lowland'
                WHEN elevation < 1000 THEN 'hills'
                WHEN elevation < 2000 THEN 'mountain'
                ELSE 'high_mountain'
            END as category,
            COUNT(*) as count
        FROM spots
        WHERE elevation IS NOT NULL
        GROUP BY category
    """
    )

    for row in cursor.fetchall():
        stats["by_elevation"][row[0]] = row[1]

    # Get environment assumptions by type
    type_environments = {
        "cave": {"typical_forest_coverage": 70, "typical_terrain": "Moderate"},
        "waterfall": {"typical_forest_coverage": 80, "typical_terrain": "Challenging"},
        "natural_spring": {"typical_forest_coverage": 60, "typical_terrain": "Easy"},
        "historical_ruins": {"typical_forest_coverage": 40, "typical_terrain": "Easy"},
        "viewpoint": {"typical_forest_coverage": 20, "typical_terrain": "Moderate"},
        "hiking_trail": {"typical_forest_coverage": 50, "typical_terrain": "Moderate"},
    }

    cursor.execute(
        """
        SELECT type, COUNT(*) as count
        FROM spots
        GROUP BY type
    """
    )

    for row in cursor.fetchall():
        spot_type = row[0] or "unknown"
        stats["by_type_environment"][spot_type] = {
            "count": row[1],
            "typical_environment": type_environments.get(
                spot_type, {"typical_forest_coverage": 50, "typical_terrain": "Moderate"}
            ),
        }

    conn.close()

    return stats


@router.post("/download-ign-data")
async def download_ign_data(
    department: str = Query(..., regex="^(09|11|12|30|31|32|34|46|48|65|66|81|82)$"),
    dataset: str = Query(..., regex="^(bd_foret|rgealti|dnsb_haies|rpg)$"),
):
    """
    Trigger download of IGN data for a specific department

    Note: This would typically be an admin-only endpoint
    """
    try:
        file_path = ign_service.download_department_data(department, dataset)

        if file_path:
            return {
                "status": "success",
                "department": department,
                "dataset": dataset,
                "file_path": str(file_path),
                "message": f"Downloaded {dataset} data for department {department}",
            }
        else:
            raise HTTPException(status_code=500, detail="Download failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    """Get real-time WFS analysis for a specific spot"""
    import sqlite3

    db_path = Path(__file__).parent.parent.parent.parent / "data" / "occitanie_spots.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM spots WHERE id = ?", (spot_id,))
    spot = cursor.fetchone()

    if not spot:
        conn.close()
        raise HTTPException(status_code=404, detail="Spot not found")

    spot_dict = dict(spot)
    conn.close()

    if not (spot_dict.get("latitude") and spot_dict.get("longitude")):
        raise HTTPException(status_code=400, detail="Spot has no coordinates")

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
