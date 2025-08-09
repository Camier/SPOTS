"""
Image-based location detection using Hugging Face models
Identifies locations in Occitanie from uploaded photos
"""

import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from dataclasses import dataclass
import exifread
from geopy.geocoders import Nominatim
import io

logger = logging.getLogger(__name__)

@dataclass
class LocationPrediction:
    """Predicted location from image"""
    place_name: str
    confidence: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    department: Optional[str] = None
    region: str = "Occitanie"
    landmarks: List[str] = None
    scene_type: Optional[str] = None  # waterfall, cave, ruins, etc.
    
class ImageLocator:
    """
    Locate places in Occitanie from images using:
    1. EXIF GPS data (if available)
    2. Visual landmark recognition
    3. Scene classification
    4. Similarity matching with known spots
    """
    
    def __init__(self, model_name: str = "google/vit-base-patch16-224"):
        """
        Initialize with Vision Transformer for image classification
        For production, consider using:
        - CLIP for zero-shot classification
        - GeoEstimation models for location prediction
        - Custom fine-tuned models on Occitanie landmarks
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.geocoder = Nominatim(user_agent="spots_image_locator")
        
        # Load models (simplified for demo)
        try:
            from transformers import ViTImageProcessor, ViTForImageClassification
            self.processor = ViTImageProcessor.from_pretrained(model_name)
            self.model = ViTForImageClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Loaded vision model: {model_name}")
        except ImportError:
            logger.warning("Transformers not installed. Install with: pip install transformers torch pillow")
            self.processor = None
            self.model = None
            
        # Occitanie landmarks for recognition
        self.occitanie_landmarks = {
            # Toulouse area
            "basilique_saint_sernin": {"lat": 43.6085, "lng": 1.4418, "dept": "31"},
            "pont_neuf_toulouse": {"lat": 43.5997, "lng": 1.4422, "dept": "31"},
            "capitole_toulouse": {"lat": 43.6047, "lng": 1.4442, "dept": "31"},
            
            # Carcassonne
            "cite_carcassonne": {"lat": 43.2065, "lng": 2.3640, "dept": "11"},
            
            # Montpellier
            "place_comedie_montpellier": {"lat": 43.6085, "lng": 3.8798, "dept": "34"},
            "arc_triomphe_montpellier": {"lat": 43.6119, "lng": 3.8772, "dept": "34"},
            
            # Natural landmarks
            "pic_du_midi": {"lat": 42.9369, "lng": 0.1416, "dept": "65"},
            "cirque_gavarnie": {"lat": 42.6953, "lng": -0.0098, "dept": "65"},
            "pont_du_gard": {"lat": 43.9475, "lng": 4.5350, "dept": "30"},
            "gorges_du_tarn": {"lat": 44.3667, "lng": 3.2500, "dept": "48"},
            
            # Castles
            "chateau_foix": {"lat": 42.9656, "lng": 1.6053, "dept": "09"},
            "chateau_peyrepertuse": {"lat": 42.8703, "lng": 2.5567, "dept": "11"},
            "chateau_queribus": {"lat": 42.8369, "lng": 2.6217, "dept": "11"},
        }
        
        # Scene types common in Occitanie
        self.scene_types = {
            "waterfall": ["cascade", "chute d'eau", "waterfall", "falls"],
            "cave": ["grotte", "cave", "cavern", "aven"],
            "ruins": ["ruines", "ruins", "château", "castle", "fort"],
            "spring": ["source", "spring", "fontaine", "resurgence"],
            "lake": ["lac", "lake", "étang", "pond"],
            "river": ["rivière", "river", "fleuve", "stream"],
            "mountain": ["montagne", "mountain", "pic", "peak", "sommet"],
            "forest": ["forêt", "forest", "bois", "wood"],
            "bridge": ["pont", "bridge", "viaduc", "aqueduc"],
            "church": ["église", "church", "cathédrale", "basilique", "abbaye"]
        }
        
    def extract_gps_from_exif(self, image_path: str) -> Optional[Tuple[float, float]]:
        """Extract GPS coordinates from image EXIF data"""
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                
            # Check for GPS tags
            if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                lat = self._convert_to_degrees(tags['GPS GPSLatitude'])
                lng = self._convert_to_degrees(tags['GPS GPSLongitude'])
                
                # Handle hemisphere
                if tags.get('GPS GPSLatitudeRef', 'N').values[0] == 'S':
                    lat = -lat
                if tags.get('GPS GPSLongitudeRef', 'E').values[0] == 'W':
                    lng = -lng
                    
                # Check if in Occitanie region
                if self._is_in_occitanie(lat, lng):
                    logger.info(f"Found GPS coordinates in EXIF: {lat}, {lng}")
                    return lat, lng
                    
        except Exception as e:
            logger.debug(f"Could not extract EXIF GPS: {e}")
            
        return None
    
    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to degrees"""
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)
        return d + (m / 60.0) + (s / 3600.0)
    
    def _is_in_occitanie(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within Occitanie region"""
        # Approximate bounds of Occitanie
        return (42.0 <= lat <= 45.0) and (-1.0 <= lng <= 5.0)
    
    def identify_landmarks(self, image: Image.Image) -> List[Dict]:
        """Identify known Occitanie landmarks in image"""
        if not self.model:
            return []
            
        # Process image
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            
        # Get predictions
        predictions = torch.nn.functional.softmax(logits, dim=-1)
        top_k = torch.topk(predictions, k=5)
        
        # Map to landmark names (simplified - would need custom model)
        landmarks = []
        for score, idx in zip(top_k.values[0], top_k.indices[0]):
            if score > 0.3:  # Confidence threshold
                # This is simplified - in reality, we'd need a model trained on landmarks
                label = self.model.config.id2label[idx.item()]
                
                # Check if label matches any landmark
                for landmark_key, landmark_data in self.occitanie_landmarks.items():
                    if landmark_key.replace('_', ' ') in label.lower():
                        landmarks.append({
                            'name': landmark_key,
                            'confidence': float(score),
                            'location': landmark_data
                        })
                        
        return landmarks
    
    def classify_scene_type(self, image: Image.Image) -> Tuple[str, float]:
        """Classify the type of outdoor scene"""
        if not self.model:
            return "unknown", 0.0
            
        # Process image
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            
        # Get predictions
        predictions = torch.nn.functional.softmax(logits, dim=-1)
        top_prediction = torch.argmax(predictions, dim=-1)
        confidence = torch.max(predictions).item()
        
        # Get label
        label = self.model.config.id2label[top_prediction.item()].lower()
        
        # Map to scene types
        for scene_type, keywords in self.scene_types.items():
            for keyword in keywords:
                if keyword in label:
                    return scene_type, confidence
                    
        return "outdoor", confidence * 0.5  # Generic outdoor scene
    
    def predict_location(self, image_path: str) -> LocationPrediction:
        """
        Predict location from image using multiple methods
        """
        # 1. Try EXIF GPS first
        gps_coords = self.extract_gps_from_exif(image_path)
        if gps_coords:
            lat, lng = gps_coords
            
            # Reverse geocode to get place name
            try:
                location = self.geocoder.reverse(f"{lat}, {lng}", language='fr')
                place_name = location.address if location else "Unknown location"
                department = self._get_department_from_coords(lat, lng)
                
                return LocationPrediction(
                    place_name=place_name,
                    confidence=1.0,  # GPS is accurate
                    latitude=lat,
                    longitude=lng,
                    department=department
                )
            except Exception as e:
                logger.error(f"Reverse geocoding failed: {e}")
        
        # 2. Load image for visual analysis
        image = Image.open(image_path).convert('RGB')
        
        # 3. Identify landmarks
        landmarks = self.identify_landmarks(image)
        if landmarks:
            best_landmark = max(landmarks, key=lambda x: x['confidence'])
            location_data = best_landmark['location']
            
            return LocationPrediction(
                place_name=best_landmark['name'].replace('_', ' ').title(),
                confidence=best_landmark['confidence'],
                latitude=location_data['lat'],
                longitude=location_data['lng'],
                department=location_data['dept'],
                landmarks=[l['name'] for l in landmarks]
            )
        
        # 4. Classify scene type
        scene_type, scene_confidence = self.classify_scene_type(image)
        
        # 5. Return best guess based on scene type
        return LocationPrediction(
            place_name=f"Unknown {scene_type} in Occitanie",
            confidence=scene_confidence * 0.5,  # Lower confidence for scene-only
            scene_type=scene_type,
            region="Occitanie"
        )
    
    def _get_department_from_coords(self, lat: float, lng: float) -> str:
        """Get department code from coordinates"""
        # Simplified department boundaries
        departments = {
            "09": {"name": "Ariège", "lat_range": (42.5, 43.0), "lng_range": (1.0, 2.0)},
            "11": {"name": "Aude", "lat_range": (42.5, 43.5), "lng_range": (2.0, 3.0)},
            "12": {"name": "Aveyron", "lat_range": (43.8, 44.8), "lng_range": (1.8, 3.2)},
            "30": {"name": "Gard", "lat_range": (43.5, 44.5), "lng_range": (3.5, 4.5)},
            "31": {"name": "Haute-Garonne", "lat_range": (42.7, 43.9), "lng_range": (0.5, 2.0)},
            "32": {"name": "Gers", "lat_range": (43.3, 44.0), "lng_range": (-0.2, 1.2)},
            "34": {"name": "Hérault", "lat_range": (43.2, 44.0), "lng_range": (3.0, 4.0)},
            "46": {"name": "Lot", "lat_range": (44.2, 45.0), "lng_range": (1.0, 2.2)},
            "48": {"name": "Lozère", "lat_range": (44.0, 44.9), "lng_range": (3.0, 3.9)},
            "65": {"name": "Hautes-Pyrénées", "lat_range": (42.7, 43.5), "lng_range": (-0.5, 0.5)},
            "66": {"name": "Pyrénées-Orientales", "lat_range": (42.3, 42.9), "lng_range": (1.7, 3.2)},
            "81": {"name": "Tarn", "lat_range": (43.4, 44.2), "lng_range": (1.5, 2.8)},
            "82": {"name": "Tarn-et-Garonne", "lat_range": (43.7, 44.4), "lng_range": (0.8, 2.0)},
        }
        
        for dept_code, dept_info in departments.items():
            lat_min, lat_max = dept_info["lat_range"]
            lng_min, lng_max = dept_info["lng_range"]
            
            if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
                return dept_code
                
        return "31"  # Default to Haute-Garonne
    
    def extract_text_from_image(self, image_path: str) -> List[str]:
        """Extract text from image that might indicate location"""
        # This would use OCR (like Tesseract) to extract text
        # Text on signs, landmarks, etc. can help identify location
        # Implementation would require: pip install pytesseract
        return []
    
    def get_similar_known_spots(self, image_path: str, known_spots: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Find known spots that are visually similar to the uploaded image
        This would use image embeddings for similarity search
        """
        # Would use CLIP or similar model to create embeddings
        # Then compute similarity with known spot images
        return []