"""
Place recognition using CLIP and other vision models
Identifies specific locations and landmarks in Occitanie
"""

import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from PIL import Image
import torch
from pathlib import Path

logger = logging.getLogger(__name__)

class PlaceRecognizer:
    """
    Recognize places using CLIP (Contrastive Language-Image Pre-training)
    for zero-shot classification of Occitanie locations
    """
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize CLIP model for place recognition
        CLIP allows zero-shot classification with text prompts
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.processor = None
        
        try:
            from transformers import CLIPProcessor, CLIPModel
            self.processor = CLIPProcessor.from_pretrained(model_name)
            self.model = CLIPModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Loaded CLIP model: {model_name}")
        except ImportError:
            logger.warning("CLIP not available. Install with: pip install transformers")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            
        # Occitanie-specific place descriptions for zero-shot classification
        self.place_descriptions = {
            # Natural spots
            "waterfall": [
                "a waterfall in the mountains",
                "cascade dans les montagnes",
                "water falling from rocks",
                "chute d'eau naturelle"
            ],
            "cave": [
                "entrance to a cave",
                "grotte naturelle",
                "dark cave opening",
                "cavern entrance in rocks"
            ],
            "spring": [
                "natural water spring",
                "source d'eau claire",
                "water emerging from ground",
                "fontaine naturelle"
            ],
            "ruins": [
                "ancient stone ruins",
                "ruines de château",
                "abandoned castle walls",
                "old fortress remains"
            ],
            "lake": [
                "mountain lake surrounded by forest",
                "lac de montagne",
                "peaceful lake with reflections",
                "étang naturel"
            ],
            
            # Specific Occitanie landmarks
            "toulouse": [
                "Toulouse city with pink brick buildings",
                "Capitole de Toulouse",
                "Basilique Saint-Sernin Toulouse",
                "ville rose architecture"
            ],
            "carcassonne": [
                "Medieval fortress of Carcassonne",
                "Cité de Carcassonne walls",
                "château comtal de Carcassonne",
                "medieval city ramparts"
            ],
            "montpellier": [
                "Montpellier city center",
                "Place de la Comédie Montpellier",
                "Arc de Triomphe Montpellier",
                "modern city architecture"
            ],
            "pyrenees": [
                "Pyrenees mountain peaks",
                "snow-capped Pyrenees",
                "Pic du Midi observatory",
                "mountain trails in Pyrenees"
            ],
            "canal_du_midi": [
                "Canal du Midi with boats",
                "tree-lined canal waterway",
                "historic canal locks",
                "péniches on the canal"
            ],
            "pont_du_gard": [
                "Roman aqueduct Pont du Gard",
                "ancient stone bridge",
                "three-tier Roman bridge",
                "historic aqueduct arches"
            ],
            "gorges": [
                "Gorges du Tarn canyon",
                "deep river gorge",
                "limestone cliffs and river",
                "canyon with kayakers"
            ]
        }
        
        # Activity descriptions
        self.activity_descriptions = {
            "hiking": [
                "people hiking on mountain trail",
                "backpackers on path",
                "randonneurs sur sentier"
            ],
            "swimming": [
                "people swimming in natural pool",
                "baignade en eau naturelle",
                "swimmers in lake or river"
            ],
            "climbing": [
                "rock climbers on cliff",
                "escalade sur rocher",
                "climbing equipment on rocks"
            ],
            "kayaking": [
                "kayaks on river",
                "canoë-kayak sur rivière",
                "paddling through rapids"
            ],
            "camping": [
                "tents in nature",
                "camping sauvage",
                "campfire and tents"
            ]
        }
        
    def recognize_place(self, image_path: str, custom_descriptions: Optional[List[str]] = None) -> List[Dict]:
        """
        Recognize place using CLIP zero-shot classification
        
        Args:
            image_path: Path to image file
            custom_descriptions: Optional custom text descriptions to match
            
        Returns:
            List of recognized places with confidence scores
        """
        if not self.model:
            logger.warning("CLIP model not loaded")
            return []
            
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        
        # Prepare text descriptions
        if custom_descriptions:
            text_descriptions = custom_descriptions
            labels = [f"custom_{i}" for i in range(len(custom_descriptions))]
        else:
            # Flatten all descriptions
            text_descriptions = []
            labels = []
            for place_type, descriptions in self.place_descriptions.items():
                text_descriptions.extend(descriptions)
                labels.extend([place_type] * len(descriptions))
        
        # Process inputs
        inputs = self.processor(
            text=text_descriptions,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.device)
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
        
        # Aggregate scores by place type
        place_scores = {}
        for i, (prob, label) in enumerate(zip(probs[0], labels)):
            if label not in place_scores:
                place_scores[label] = []
            place_scores[label].append(float(prob))
        
        # Average scores for each place type
        results = []
        for place_type, scores in place_scores.items():
            avg_score = np.mean(scores)
            max_score = np.max(scores)
            results.append({
                'place_type': place_type,
                'confidence': float(max_score),
                'avg_confidence': float(avg_score)
            })
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return results[:5]  # Return top 5 matches
    
    def identify_activities(self, image_path: str) -> List[Dict]:
        """
        Identify outdoor activities visible in the image
        """
        if not self.model:
            return []
            
        image = Image.open(image_path).convert('RGB')
        
        # Prepare activity descriptions
        text_descriptions = []
        labels = []
        for activity, descriptions in self.activity_descriptions.items():
            text_descriptions.extend(descriptions)
            labels.extend([activity] * len(descriptions))
        
        # Process inputs
        inputs = self.processor(
            text=text_descriptions,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.device)
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
        
        # Aggregate scores
        activity_scores = {}
        for prob, label in zip(probs[0], labels):
            if label not in activity_scores:
                activity_scores[label] = []
            activity_scores[label].append(float(prob))
        
        # Get best matches
        results = []
        for activity, scores in activity_scores.items():
            max_score = np.max(scores)
            if max_score > 0.2:  # Threshold
                results.append({
                    'activity': activity,
                    'confidence': float(max_score)
                })
        
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results
    
    def match_to_known_spots(self, image_path: str, known_spots: List[Dict]) -> List[Dict]:
        """
        Match image to known spots using their descriptions
        """
        if not self.model or not known_spots:
            return []
            
        image = Image.open(image_path).convert('RGB')
        
        # Create descriptions for known spots
        spot_descriptions = []
        spot_indices = []
        
        for i, spot in enumerate(known_spots):
            # Create descriptive text for each spot
            description = f"{spot.get('type', 'outdoor spot')} near {spot.get('city', 'Occitanie')}"
            if spot.get('description'):
                description = spot['description'][:100]  # Use actual description if available
            
            spot_descriptions.append(description)
            spot_indices.append(i)
        
        # Process inputs
        inputs = self.processor(
            text=spot_descriptions,
            images=image,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to(self.device)
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
        
        # Get top matches
        top_k = min(5, len(known_spots))
        top_probs, top_indices = torch.topk(probs[0], top_k)
        
        results = []
        for prob, idx in zip(top_probs, top_indices):
            spot_idx = spot_indices[idx]
            spot = known_spots[spot_idx]
            results.append({
                'spot_id': spot.get('id'),
                'name': spot.get('name', 'Unknown'),
                'type': spot.get('type'),
                'confidence': float(prob),
                'location': {
                    'lat': spot.get('latitude'),
                    'lng': spot.get('longitude')
                }
            })
        
        return results
    
    def extract_scene_attributes(self, image_path: str) -> Dict:
        """
        Extract various attributes from the scene
        """
        if not self.model:
            return {}
            
        image = Image.open(image_path).convert('RGB')
        
        # Define attribute checks
        attributes_to_check = {
            'time_of_day': [
                "photo taken at sunrise",
                "photo taken at sunset",
                "photo taken during day",
                "photo taken at night"
            ],
            'weather': [
                "sunny weather",
                "cloudy weather",
                "rainy weather",
                "foggy weather"
            ],
            'season': [
                "spring season with flowers",
                "summer season with green vegetation",
                "autumn season with colored leaves",
                "winter season with snow"
            ],
            'water_presence': [
                "water visible in image",
                "no water visible"
            ],
            'vegetation': [
                "dense forest vegetation",
                "sparse vegetation",
                "no vegetation"
            ],
            'accessibility': [
                "easy access visible trail",
                "difficult terrain",
                "paved road access"
            ]
        }
        
        results = {}
        
        for attribute_type, descriptions in attributes_to_check.items():
            inputs = self.processor(
                text=descriptions,
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            # Get best match
            best_idx = torch.argmax(probs[0])
            results[attribute_type] = {
                'value': descriptions[best_idx],
                'confidence': float(probs[0][best_idx])
            }
        
        return results