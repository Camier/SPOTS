"""
API endpoints for image-based location detection and visual search
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List, Optional, Dict
import shutil
from pathlib import Path
import uuid
from datetime import datetime

from ..vision.image_locator import ImageLocator
from ..vision.place_recognizer import PlaceRecognizer  
from ..vision.similarity_search import SimilaritySearch

router = APIRouter(prefix="/api/vision", tags=["vision"])

# Initialize vision services
image_locator = ImageLocator()
place_recognizer = PlaceRecognizer()
similarity_search = SimilaritySearch()

# Upload directory
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/locate")
async def locate_from_image(
    file: UploadFile = File(...),
    extract_exif: bool = True,
    recognize_landmarks: bool = True
):
    """
    Identify location from uploaded image
    Uses EXIF data, landmark recognition, and scene classification
    """
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get location prediction
        prediction = image_locator.predict_location(str(file_path))
        
        # Extract additional info
        scene_type, scene_confidence = image_locator.classify_scene_type(str(file_path))
        
        result = {
            "file_id": file_id,
            "location": {
                "place_name": prediction.place_name,
                "confidence": prediction.confidence,
                "latitude": prediction.latitude,
                "longitude": prediction.longitude,
                "department": prediction.department,
                "region": prediction.region
            },
            "scene": {
                "type": scene_type or prediction.scene_type,
                "confidence": scene_confidence
            },
            "landmarks": prediction.landmarks or []
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up uploaded file after processing
        if file_path.exists():
            file_path.unlink()

@router.post("/recognize")
async def recognize_place(
    file: UploadFile = File(...),
    include_activities: bool = False,
    custom_descriptions: Optional[List[str]] = None
):
    """
    Recognize place type and activities using CLIP zero-shot classification
    """
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Recognize place
        places = place_recognizer.recognize_place(str(file_path), custom_descriptions)
        
        result = {
            "file_id": file_id,
            "places": places
        }
        
        # Add activities if requested
        if include_activities:
            activities = place_recognizer.identify_activities(str(file_path))
            result["activities"] = activities
        
        # Extract scene attributes
        attributes = place_recognizer.extract_scene_attributes(str(file_path))
        result["attributes"] = attributes
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_path.exists():
            file_path.unlink()

@router.post("/search/similar")
async def search_similar_spots(
    file: UploadFile = File(...),
    k: int = Query(10, ge=1, le=50),
    filter_type: Optional[str] = None
):
    """
    Find visually similar spots from the database
    """
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Search for similar spots
        similar_spots = similarity_search.search_similar(
            str(file_path), 
            k=k,
            filter_type=filter_type
        )
        
        return {
            "file_id": file_id,
            "similar_spots": similar_spots,
            "total_results": len(similar_spots)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_path.exists():
            file_path.unlink()

@router.post("/index/add")
async def add_to_index(spot_images: List[Dict]):
    """
    Add spot images to the similarity search index
    Expected format: [{"spot_id": 1, "image_path": "path/to/image.jpg", ...}]
    """
    try:
        similarity_search.add_spot_images(spot_images)
        return {
            "success": True,
            "message": f"Added {len(spot_images)} images to index",
            "index_stats": similarity_search.get_embedding_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/index/stats")
async def get_index_stats():
    """Get statistics about the similarity search index"""
    return similarity_search.get_embedding_stats()

@router.post("/index/rebuild")
async def rebuild_index():
    """Rebuild the similarity search index"""
    try:
        similarity_search.rebuild_index()
        return {
            "success": True,
            "message": "Index rebuilt successfully",
            "stats": similarity_search.get_embedding_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    full_analysis: bool = True
):
    """
    Comprehensive image analysis combining all vision capabilities
    """
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Perform comprehensive analysis
        analysis = {
            "file_id": file_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Location detection
        location_pred = image_locator.predict_location(str(file_path))
        analysis["location"] = {
            "place_name": location_pred.place_name,
            "confidence": location_pred.confidence,
            "coordinates": {
                "latitude": location_pred.latitude,
                "longitude": location_pred.longitude
            },
            "department": location_pred.department,
            "region": location_pred.region,
            "scene_type": location_pred.scene_type
        }
        
        if full_analysis:
            # Place recognition
            places = place_recognizer.recognize_place(str(file_path))
            analysis["recognized_places"] = places[:3]  # Top 3
            
            # Activities
            activities = place_recognizer.identify_activities(str(file_path))
            analysis["activities"] = activities
            
            # Scene attributes
            attributes = place_recognizer.extract_scene_attributes(str(file_path))
            analysis["attributes"] = attributes
            
            # Similar spots
            similar = similarity_search.search_similar(str(file_path), k=5)
            analysis["similar_spots"] = similar
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_path.exists():
            file_path.unlink()

@router.get("/duplicates")
async def find_duplicate_images(threshold: float = Query(0.95, ge=0.5, le=1.0)):
    """Find duplicate or near-duplicate images in the index"""
    duplicates = similarity_search.find_duplicates(threshold)
    return {
        "duplicate_groups": duplicates,
        "total_groups": len(duplicates),
        "threshold": threshold
    }

@router.post("/match-to-spots")
async def match_to_known_spots(
    file: UploadFile = File(...),
    spots: List[Dict] = Query(..., description="List of known spots with descriptions")
):
    """
    Match uploaded image to a list of known spots
    """
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Match to known spots
        matches = place_recognizer.match_to_known_spots(str(file_path), spots)
        
        return {
            "file_id": file_id,
            "matches": matches,
            "best_match": matches[0] if matches else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_path.exists():
            file_path.unlink()