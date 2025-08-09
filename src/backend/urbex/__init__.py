"""
Urbex (Urban Exploration) Module for SPOTS Project
Handles discovery and cataloging of abandoned places in Occitanie
"""

from .scraper import UrbexScraper
from .validator import UrbexSpotValidator
from .data_models import UrbexSpot, UrbexCategory

__all__ = ['UrbexScraper', 'UrbexSpotValidator', 'UrbexSpot', 'UrbexCategory']