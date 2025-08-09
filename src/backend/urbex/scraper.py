"""
Urbex-specific scraper for finding abandoned places in Occitanie
"""
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

from ..scrapers_cleaned.core.base_scraper import BaseScraper
from ..scrapers_cleaned.utils.geocoding import FrenchGeocoder
from .data_models import UrbexSpot, UrbexCategory, DangerLevel, AccessDifficulty
from .validator import UrbexSpotValidator

logger = logging.getLogger(__name__)

class UrbexScraper(BaseScraper):
    """Specialized scraper for urbex locations"""
    
    # Occitanie departments
    OCCITANIE_DEPARTMENTS = [
        "09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"
    ]
    
    # Urbex-specific hashtags for Instagram
    URBEX_HASHTAGS = [
        # General urbex
        "urbexfrance", "urbex", "urbexworld", "urbexing",
        "abandonedplaces", "abandoned", "decay", "ruins",
        
        # French specific
        "urbexoccitanie", "urbextoulouse", "urbexmontpellier",
        "lieuxabandonnés", "ruines", "friche", "patrimoineoublié",
        
        # Category specific
        "abandonedcastle", "chateauabandonné", "industrialheritage",
        "abandonedchurch", "egliseabandonnée", "usineabandonnée",
        
        # Regional
        "urbex31", "urbex34", "urbex11", "urbex66", "urbex09",
        "urbexpyrenees", "urbexlanguedoc", "urbexmidipyrenees"
    ]
    
    # Keywords to identify urbex content
    URBEX_KEYWORDS = [
        "abandonné", "abandoned", "urbex", "ruine", "ruins",
        "friche", "désaffecté", "decay", "forgotten", "oublié",
        "exploration urbaine", "urban exploration", "lieu abandonné",
        "château abandonné", "usine abandonnée", "église abandonnée",
        "hôpital abandonné", "école abandonnée", "gare abandonnée"
    ]
    
    # Category detection patterns
    CATEGORY_PATTERNS = {
        UrbexCategory.CASTLE: r"château|castle|fort|forteresse|donjon",
        UrbexCategory.INDUSTRIAL: r"usine|factory|manufacture|industrie|atelier|entrepôt",
        UrbexCategory.CHURCH: r"église|church|chapelle|chapel|abbaye|monastery|couvent",
        UrbexCategory.HOSPITAL: r"hôpital|hospital|sanatorium|clinique|asile",
        UrbexCategory.SCHOOL: r"école|school|lycée|collège|université|pensionnat",
        UrbexCategory.MILITARY: r"militaire|military|caserne|barracks|bunker|fortification",
        UrbexCategory.RAILWAY: r"gare|station|railway|chemin de fer|train|locomotive",
        UrbexCategory.MINE: r"mine|carrière|quarry|extraction|souterrain",
        UrbexCategory.HOTEL: r"hôtel|hotel|motel|auberge|resort|palace",
        UrbexCategory.THEME_PARK: r"parc|park|attraction|manège|fête foraine"
    }
    
    # Danger level keywords
    DANGER_KEYWORDS = {
        DangerLevel.LOW: ["safe", "sûr", "stable", "accessible", "facile"],
        DangerLevel.MEDIUM: ["attention", "careful", "prudent", "moyen"],
        DangerLevel.HIGH: ["dangereux", "dangerous", "risqué", "instable", "effondrement"],
        DangerLevel.EXTREME: ["très dangereux", "extremely dangerous", "mortel", "interdit"]
    }
    
    def __init__(self):
        super().__init__()
        self.geocoder = FrenchGeocoder()
        self.validator = UrbexSpotValidator()
        
    def scrape_instagram_urbex(self, hashtag: str, limit: int = 20) -> List[UrbexSpot]:
        """Scrape Instagram for urbex spots using specific hashtag"""
        spots = []
        
        try:
            # This would integrate with Instagram scraper
            # For now, returning demo data
            logger.info(f"Searching Instagram for #{hashtag}")
            
            # Demo urbex spots for Occitanie
            demo_spots = self._get_demo_urbex_spots()
            
            for spot_data in demo_spots[:limit]:
                if self._is_in_occitanie(spot_data):
                    spot = self._parse_urbex_spot(spot_data)
                    if spot and self.validator.validate(spot):
                        spots.append(spot)
                        
        except Exception as e:
            logger.error(f"Error scraping Instagram urbex: {e}")
            
        return spots
    
    def scrape_reddit_urbex(self, subreddit: str = "urbexfrance") -> List[UrbexSpot]:
        """Scrape Reddit for urbex locations"""
        spots = []
        
        try:
            logger.info(f"Searching Reddit r/{subreddit}")
            
            # Would integrate with Reddit scraper
            # Demo implementation
            demo_spots = self._get_demo_urbex_spots()
            
            for spot_data in demo_spots:
                if self._is_in_occitanie(spot_data):
                    spot = self._parse_urbex_spot(spot_data)
                    if spot and self.validator.validate(spot):
                        spots.append(spot)
                        
        except Exception as e:
            logger.error(f"Error scraping Reddit urbex: {e}")
            
        return spots
    
    def _parse_urbex_spot(self, data: Dict) -> Optional[UrbexSpot]:
        """Parse raw data into UrbexSpot object"""
        try:
            # Extract coordinates
            lat, lng = self._extract_coordinates(data.get('text', ''))
            if not lat or not lng:
                # Try geocoding
                location = data.get('location', '')
                if location:
                    geo_result = self.geocoder.geocode(location)
                    if geo_result:
                        lat = geo_result.get('latitude')
                        lng = geo_result.get('longitude')
            
            if not lat or not lng:
                return None
            
            # Detect category
            category = self._detect_category(data.get('text', ''))
            
            # Detect danger level
            danger_level = self._detect_danger_level(data.get('text', ''))
            
            # Create spot
            spot = UrbexSpot(
                name=data.get('name', 'Unknown Urbex Location'),
                category=category,
                latitude=lat,
                longitude=lng,
                department=self._get_department(lat, lng),
                danger_level=danger_level,
                source=data.get('source', 'unknown'),
                discovered_date=datetime.now(),
                last_updated=datetime.now(),
                notes=data.get('text', '')
            )
            
            # Add additional info if available
            if 'year_abandoned' in data:
                spot.year_abandoned = data['year_abandoned']
            if 'hazards' in data:
                spot.hazards = data['hazards']
            if 'photos' in data:
                spot.photos = data['photos']
                
            return spot
            
        except Exception as e:
            logger.error(f"Error parsing urbex spot: {e}")
            return None
    
    def _detect_category(self, text: str) -> UrbexCategory:
        """Detect urbex category from text"""
        text_lower = text.lower()
        
        for category, pattern in self.CATEGORY_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return category
                
        return UrbexCategory.OTHER
    
    def _detect_danger_level(self, text: str) -> DangerLevel:
        """Detect danger level from text"""
        text_lower = text.lower()
        
        for level, keywords in self.DANGER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level
                    
        return DangerLevel.MEDIUM  # Default
    
    def _is_in_occitanie(self, data: Dict) -> bool:
        """Check if location is in Occitanie"""
        location = data.get('location', '').lower()
        text = data.get('text', '').lower()
        
        # Check for Occitanie departments
        for dept in self.OCCITANIE_DEPARTMENTS:
            if f"({dept})" in location or f" {dept} " in text:
                return True
        
        # Check for Occitanie cities
        occitanie_cities = [
            "toulouse", "montpellier", "nîmes", "perpignan", "béziers",
            "narbonne", "carcassonne", "albi", "tarbes", "castres"
        ]
        
        for city in occitanie_cities:
            if city in location or city in text:
                return True
                
        return False
    
    def _get_department(self, lat: float, lng: float) -> str:
        """Get department code from coordinates"""
        # This would use geocoding to get department
        # For now, return default
        return "31"  # Haute-Garonne
    
    def _extract_coordinates(self, text: str) -> tuple:
        """Extract coordinates from text"""
        # Pattern for coordinates
        coord_pattern = r'(\d+\.\d+)[,\s]+(\d+\.\d+)'
        match = re.search(coord_pattern, text)
        
        if match:
            return float(match.group(1)), float(match.group(2))
            
        return None, None
    
    def _get_demo_urbex_spots(self) -> List[Dict]:
        """Get demo urbex spots for testing"""
        return [
            {
                'name': 'Château de Lordat',
                'text': 'Abandoned castle in Ariège, amazing views but dangerous structure #urbexfrance #château',
                'location': 'Lordat, Ariège (09)',
                'year_abandoned': 1960,
                'source': 'instagram'
            },
            {
                'name': 'Usine Textile Mazamet',
                'text': 'Old textile factory in Tarn, huge industrial complex #urbex #industrial',
                'location': 'Mazamet, Tarn (81)',
                'year_abandoned': 1985,
                'source': 'reddit'
            },
            {
                'name': 'Sanatorium du Pic du Jer',
                'text': 'Abandoned sanatorium near Lourdes, very dangerous, asbestos present #urbex65',
                'location': 'Lourdes, Hautes-Pyrénées (65)',
                'year_abandoned': 1970,
                'hazards': ['asbestos', 'structural damage'],
                'source': 'instagram'
            },
            {
                'name': 'Gare de Latour-de-Carol',
                'text': 'Abandoned railway station in Pyrénées-Orientales, easy access #urbexrailway',
                'location': 'Latour-de-Carol, Pyrénées-Orientales (66)',
                'year_abandoned': 1990,
                'source': 'instagram'
            },
            {
                'name': 'Église Saint-Michel',
                'text': 'Beautiful abandoned church in Aude, roof collapsed but safe to explore #urbexchurch',
                'location': 'Carcassonne area, Aude (11)',
                'year_abandoned': 1975,
                'source': 'reddit'
            }
        ]
    
    def search_all_sources(self) -> List[UrbexSpot]:
        """Search all sources for urbex spots"""
        all_spots = []
        
        # Search Instagram
        for hashtag in self.URBEX_HASHTAGS[:5]:  # Limit for demo
            spots = self.scrape_instagram_urbex(hashtag, limit=5)
            all_spots.extend(spots)
        
        # Search Reddit
        spots = self.scrape_reddit_urbex()
        all_spots.extend(spots)
        
        # Remove duplicates based on coordinates
        unique_spots = {}
        for spot in all_spots:
            key = f"{spot.latitude:.4f},{spot.longitude:.4f}"
            if key not in unique_spots:
                unique_spots[key] = spot
        
        return list(unique_spots.values())