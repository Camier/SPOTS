"""
Data models for urbex spots
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

class UrbexCategory(Enum):
    """Categories of urbex locations"""
    ABANDONED_BUILDING = "abandoned_building"
    INDUSTRIAL = "industrial"
    CASTLE = "castle"
    CHURCH = "church"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    MILITARY = "military"
    TUNNEL = "tunnel"
    MINE = "mine"
    QUARRY = "quarry"
    THEME_PARK = "theme_park"
    HOTEL = "hotel"
    RAILWAY = "railway"
    BUNKER = "bunker"
    OTHER = "other"

class DangerLevel(Enum):
    """Safety risk levels for urbex spots"""
    LOW = 1  # Safe, stable structures
    MEDIUM = 2  # Some risks, caution needed
    HIGH = 3  # Dangerous, experienced only
    EXTREME = 4  # Very dangerous, not recommended

class AccessDifficulty(Enum):
    """How hard it is to access the location"""
    EASY = 1  # Open access
    MODERATE = 2  # Some obstacles
    HARD = 3  # Significant barriers
    EXPERT = 4  # Requires special equipment/skills

@dataclass
class UrbexSpot:
    """Urbex location data model"""
    # Basic info
    name: str
    category: UrbexCategory
    latitude: float
    longitude: float
    department: str
    region: str = "Occitanie"
    
    # Location details
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Urbex-specific attributes
    danger_level: DangerLevel = DangerLevel.MEDIUM
    access_difficulty: AccessDifficulty = AccessDifficulty.MODERATE
    is_active: bool = True  # False if demolished/secured
    year_abandoned: Optional[int] = None
    historical_use: Optional[str] = None
    current_state: Optional[str] = None
    
    # Access info
    access_notes: Optional[str] = None
    best_time_to_visit: Optional[str] = None
    security_presence: bool = False
    fence_type: Optional[str] = None
    entry_points: Optional[List[str]] = None
    
    # Safety warnings
    hazards: Optional[List[str]] = None
    structural_integrity: Optional[str] = None
    asbestos_risk: bool = False
    
    # Photography
    photography_spots: Optional[List[str]] = None
    best_light_time: Optional[str] = None
    notable_features: Optional[List[str]] = None
    
    # Legal status
    legal_status: Optional[str] = None  # "public", "private", "disputed"
    owner_info: Optional[str] = None
    permission_required: bool = True
    
    # Community info
    popularity_score: int = 0  # 0-100
    visit_count: int = 0
    last_confirmed_visit: Optional[datetime] = None
    local_name: Optional[str] = None
    
    # Media
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    instagram_posts: Optional[List[str]] = None
    
    # Metadata
    discovered_date: datetime = None
    last_updated: datetime = None
    source: Optional[str] = None
    verified: bool = False
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'category': self.category.value,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'department': self.department,
            'region': self.region,
            'address': self.address,
            'city': self.city,
            'postal_code': self.postal_code,
            'danger_level': self.danger_level.value,
            'access_difficulty': self.access_difficulty.value,
            'is_active': self.is_active,
            'year_abandoned': self.year_abandoned,
            'historical_use': self.historical_use,
            'current_state': self.current_state,
            'access_notes': self.access_notes,
            'best_time_to_visit': self.best_time_to_visit,
            'security_presence': self.security_presence,
            'fence_type': self.fence_type,
            'entry_points': ','.join(self.entry_points) if self.entry_points else None,
            'hazards': ','.join(self.hazards) if self.hazards else None,
            'structural_integrity': self.structural_integrity,
            'asbestos_risk': self.asbestos_risk,
            'photography_spots': ','.join(self.photography_spots) if self.photography_spots else None,
            'best_light_time': self.best_light_time,
            'notable_features': ','.join(self.notable_features) if self.notable_features else None,
            'legal_status': self.legal_status,
            'owner_info': self.owner_info,
            'permission_required': self.permission_required,
            'popularity_score': self.popularity_score,
            'visit_count': self.visit_count,
            'last_confirmed_visit': self.last_confirmed_visit.isoformat() if self.last_confirmed_visit else None,
            'local_name': self.local_name,
            'discovered_date': self.discovered_date.isoformat() if self.discovered_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'source': self.source,
            'verified': self.verified,
            'notes': self.notes
        }
    
    def get_risk_score(self) -> int:
        """Calculate overall risk score (0-100)"""
        base_score = self.danger_level.value * 20
        if self.asbestos_risk:
            base_score += 15
        if not self.structural_integrity or "poor" in (self.structural_integrity or "").lower():
            base_score += 15
        if self.security_presence:
            base_score += 10
        return min(base_score, 100)
    
    def is_beginner_friendly(self) -> bool:
        """Check if suitable for urbex beginners"""
        return (
            self.danger_level in [DangerLevel.LOW, DangerLevel.MEDIUM] and
            self.access_difficulty in [AccessDifficulty.EASY, AccessDifficulty.MODERATE] and
            not self.asbestos_risk and
            self.get_risk_score() < 50
        )