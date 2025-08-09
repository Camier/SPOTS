"""
Validator for urbex spots to ensure safety and data quality
"""
import logging
from typing import Optional, List
from .data_models import UrbexSpot, DangerLevel

logger = logging.getLogger(__name__)

class UrbexSpotValidator:
    """Validate urbex spots for safety and data quality"""
    
    # Minimum requirements for a valid urbex spot
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 200
    VALID_COORD_RANGE = {
        'lat': (42.0, 45.0),  # Occitanie latitude range
        'lng': (-1.0, 5.0)    # Occitanie longitude range
    }
    
    # Forbidden keywords (places that should not be promoted)
    FORBIDDEN_KEYWORDS = [
        "école primaire",  # Active elementary schools
        "crèche",  # Daycare centers
        "site classé",  # Protected heritage sites
        "réserve naturelle",  # Nature reserves
        "propriété privée habitée",  # Inhabited private property
    ]
    
    # Required warnings for high-risk locations
    HIGH_RISK_WARNINGS = [
        "asbestos", "amiante",
        "effondrement", "collapse",
        "radioactive", "radioactif",
        "chemical", "chimique",
        "biohazard", "biological"
    ]
    
    def validate(self, spot: UrbexSpot) -> bool:
        """
        Validate an urbex spot
        Returns True if valid, False otherwise
        """
        try:
            # Basic validation
            if not self._validate_basic_info(spot):
                return False
            
            # Coordinate validation
            if not self._validate_coordinates(spot):
                return False
            
            # Safety validation
            if not self._validate_safety(spot):
                return False
            
            # Legal validation
            if not self._validate_legal(spot):
                return False
            
            # Content validation
            if not self._validate_content(spot):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating urbex spot: {e}")
            return False
    
    def _validate_basic_info(self, spot: UrbexSpot) -> bool:
        """Validate basic spot information"""
        # Check name
        if not spot.name or len(spot.name) < self.MIN_NAME_LENGTH:
            logger.warning(f"Invalid name: too short - {spot.name}")
            return False
        
        if len(spot.name) > self.MAX_NAME_LENGTH:
            logger.warning(f"Invalid name: too long - {spot.name}")
            return False
        
        # Check department
        if not spot.department:
            logger.warning("Missing department")
            return False
        
        return True
    
    def _validate_coordinates(self, spot: UrbexSpot) -> bool:
        """Validate coordinates are within Occitanie"""
        lat_range = self.VALID_COORD_RANGE['lat']
        lng_range = self.VALID_COORD_RANGE['lng']
        
        if not (lat_range[0] <= spot.latitude <= lat_range[1]):
            logger.warning(f"Latitude out of range: {spot.latitude}")
            return False
        
        if not (lng_range[0] <= spot.longitude <= lng_range[1]):
            logger.warning(f"Longitude out of range: {spot.longitude}")
            return False
        
        return True
    
    def _validate_safety(self, spot: UrbexSpot) -> bool:
        """Validate safety considerations"""
        # Check if extreme danger spots have proper warnings
        if spot.danger_level == DangerLevel.EXTREME:
            if not spot.hazards:
                logger.warning(f"Extreme danger spot without hazard list: {spot.name}")
                return False
            
            # Check for required warnings
            hazard_text = ' '.join(spot.hazards).lower()
            has_warning = any(warning in hazard_text for warning in self.HIGH_RISK_WARNINGS)
            
            if not has_warning:
                logger.warning(f"High-risk spot without proper warnings: {spot.name}")
                return False
        
        # Validate asbestos warning
        if spot.asbestos_risk and spot.danger_level == DangerLevel.LOW:
            logger.warning(f"Asbestos risk incompatible with low danger level: {spot.name}")
            spot.danger_level = DangerLevel.MEDIUM  # Auto-correct
        
        return True
    
    def _validate_legal(self, spot: UrbexSpot) -> bool:
        """Validate legal and ethical considerations"""
        # Check forbidden locations
        name_lower = spot.name.lower()
        notes_lower = (spot.notes or "").lower()
        
        for forbidden in self.FORBIDDEN_KEYWORDS:
            if forbidden in name_lower or forbidden in notes_lower:
                logger.warning(f"Forbidden location type: {forbidden} in {spot.name}")
                return False
        
        # Check if private property has appropriate warnings
        if spot.legal_status == "private" and not spot.permission_required:
            logger.warning(f"Private property without permission flag: {spot.name}")
            spot.permission_required = True  # Auto-correct
        
        return True
    
    def _validate_content(self, spot: UrbexSpot) -> bool:
        """Validate content quality and completeness"""
        # Check for minimal content
        if not spot.category:
            logger.warning(f"Missing category: {spot.name}")
            return False
        
        # Warn about incomplete data (but don't reject)
        warnings = []
        
        if not spot.year_abandoned:
            warnings.append("missing year_abandoned")
        
        if not spot.access_notes and spot.access_difficulty in [AccessDifficulty.HARD, AccessDifficulty.EXPERT]:
            warnings.append("difficult access without notes")
        
        if not spot.hazards and spot.danger_level in [DangerLevel.HIGH, DangerLevel.EXTREME]:
            warnings.append("high danger without hazard list")
        
        if warnings:
            logger.info(f"Spot '{spot.name}' has warnings: {', '.join(warnings)}")
        
        return True
    
    def get_safety_score(self, spot: UrbexSpot) -> int:
        """
        Calculate a safety score (0-100, higher is safer)
        """
        score = 100
        
        # Deduct for danger level
        score -= spot.danger_level.value * 15
        
        # Deduct for access difficulty
        score -= spot.access_difficulty.value * 10
        
        # Deduct for specific hazards
        if spot.asbestos_risk:
            score -= 20
        
        if spot.security_presence:
            score -= 10
        
        if not spot.structural_integrity or "poor" in (spot.structural_integrity or "").lower():
            score -= 15
        
        # Bonus for good documentation
        if spot.access_notes:
            score += 5
        
        if spot.hazards:
            score += 5  # Knowing hazards is better
        
        return max(0, min(100, score))
    
    def validate_batch(self, spots: List[UrbexSpot]) -> List[UrbexSpot]:
        """Validate a batch of spots and return only valid ones"""
        valid_spots = []
        
        for spot in spots:
            if self.validate(spot):
                valid_spots.append(spot)
            else:
                logger.info(f"Rejected spot: {spot.name}")
        
        logger.info(f"Validated {len(valid_spots)}/{len(spots)} urbex spots")
        return valid_spots