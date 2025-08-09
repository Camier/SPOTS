"""
Vision Module for Image-Based Location Detection
Uses Hugging Face models to identify and locate places from photos
"""

from .image_locator import ImageLocator
from .place_recognizer import PlaceRecognizer
from .similarity_search import SimilaritySearch

__all__ = ['ImageLocator', 'PlaceRecognizer', 'SimilaritySearch']