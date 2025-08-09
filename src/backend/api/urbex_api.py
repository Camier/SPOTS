"""
API endpoints for urbex functionality
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime

from ..urbex.database import UrbexDatabase
from ..urbex.data_models import UrbexSpot, UrbexCategory, DangerLevel
# from ..urbex.scraper import UrbexScraper  # Temporarily disabled
from ..urbex.validator import UrbexSpotValidator

router = APIRouter(prefix="/api/urbex", tags=["urbex"])

# Initialize database
db = UrbexDatabase()
# scraper = UrbexScraper()  # Temporarily disabled - abstract class issue
validator = UrbexSpotValidator()

@router.get("/spots", response_model=List[dict])
async def get_urbex_spots(
    department: Optional[str] = None,
    category: Optional[str] = None,
    max_danger: Optional[int] = Query(4, ge=1, le=4),
    beginner_friendly: Optional[bool] = False,
    limit: int = Query(100, le=500)
):
    """Get urbex spots with optional filters"""
    
    if beginner_friendly:
        spots = db.get_safe_spots(max_danger=2)
    elif department:
        spots = db.get_spots_by_department(department)
    elif category:
        try:
            cat_enum = UrbexCategory(category)
            spots = db.get_spots_by_category(cat_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    else:
        # Get all spots (would implement pagination in production)
        spots = db.get_safe_spots(max_danger=max_danger)
    
    # Convert to dict for JSON response
    return [spot.to_dict() for spot in spots[:limit]]

@router.get("/spots/{spot_id}")
async def get_urbex_spot(spot_id: int):
    """Get a specific urbex spot by ID"""
    spot = db.get_spot_by_id(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Urbex spot not found")
    return spot.to_dict()

@router.get("/spots/nearby")
async def get_nearby_urbex(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50, ge=1, le=200)
):
    """Get urbex spots near coordinates"""
    spots = db.get_nearby_spots(lat, lng, radius_km)
    return [spot.to_dict() for spot in spots]

@router.get("/search")
async def search_urbex(
    q: str = Query(..., min_length=2),
    limit: int = Query(50, le=200)
):
    """Search urbex spots by name or description"""
    spots = db.search_spots(q)
    return [spot.to_dict() for spot in spots[:limit]]

@router.post("/spots/{spot_id}/visit")
async def record_visit(
    spot_id: int,
    condition_report: str,
    danger_update: Optional[int] = Query(None, ge=1, le=4)
):
    """Record a visit to an urbex spot"""
    success = db.record_visit(spot_id, condition_report, danger_update)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to record visit")
    return {"message": "Visit recorded successfully"}

@router.get("/categories")
async def get_categories():
    """Get all urbex categories"""
    return [
        {
            "value": cat.value,
            "name": cat.name.replace('_', ' ').title(),
            "icon": get_category_icon(cat)
        }
        for cat in UrbexCategory
    ]

@router.get("/statistics")
async def get_statistics():
    """Get urbex database statistics"""
    return db.get_statistics()

@router.post("/scrape")
async def trigger_scraping(
    source: str = Query("all", regex="^(instagram|reddit|all)$"),
    limit: int = Query(20, le=100)
):
    """Trigger urbex scraping from social media"""
    # Temporarily disabled until scraper is fixed
    return {
        "status": "disabled",
        "message": "Scraping temporarily disabled - scraper implementation in progress",
        "spots_found": 0,
        "spots_validated": 0,
        "spots_added": 0
    }

@router.get("/export/geojson")
async def export_geojson(
    department: Optional[str] = None,
    category: Optional[str] = None
):
    """Export urbex spots as GeoJSON"""
    
    if department:
        spots = db.get_spots_by_department(department)
    elif category:
        try:
            cat_enum = UrbexCategory(category)
            spots = db.get_spots_by_category(cat_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    else:
        spots = db.get_safe_spots(max_danger=4)
    
    features = []
    for spot in spots:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [spot.longitude, spot.latitude]
            },
            "properties": {
                "name": spot.name,
                "category": spot.category.value,
                "danger_level": spot.danger_level.value,
                "access_difficulty": spot.access_difficulty.value,
                "year_abandoned": spot.year_abandoned,
                "city": spot.city,
                "department": spot.department
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

def get_category_icon(category: UrbexCategory) -> str:
    """Get emoji icon for category"""
    icons = {
        UrbexCategory.ABANDONED_BUILDING: "🏚️",
        UrbexCategory.INDUSTRIAL: "🏭",
        UrbexCategory.CASTLE: "🏰",
        UrbexCategory.CHURCH: "⛪",
        UrbexCategory.HOSPITAL: "🏥",
        UrbexCategory.SCHOOL: "🏫",
        UrbexCategory.MILITARY: "🎖️",
        UrbexCategory.TUNNEL: "🚇",
        UrbexCategory.MINE: "⛏️",
        UrbexCategory.QUARRY: "🪨",
        UrbexCategory.THEME_PARK: "🎡",
        UrbexCategory.HOTEL: "🏨",
        UrbexCategory.RAILWAY: "🚂",
        UrbexCategory.BUNKER: "🛡️",
        UrbexCategory.OTHER: "❓"
    }
    return icons.get(category, "❓")