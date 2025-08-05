#!/usr/bin/env python3
"""
Consolidated Spot Data Validator
Combines validation logic from all validator modules
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from schema import Schema, And, Or, Use, Optional as SchemaOptional, SchemaError

logger = logging.getLogger(__name__)


class SpotValidator:
    """Enhanced data validator for spot information"""

    # Toulouse region boundaries
    TOULOUSE_BOUNDS = {"lat_min": 42.5, "lat_max": 44.5, "lon_min": -1.0, "lon_max": 3.0}

    # Valid location types (combined from all validators)
    LOCATION_TYPES = [
        "natural", "urban", "abandoned", "viewpoint", "water", "ruins", "park",
        "trail", "cave", "building", "bridge", "tunnel", "forest", "mountain",
        "beach", "lake", "river", "waterfall", "cascade", "natural_pool",
        "abandoned_building", "nature", "historical", "geological", "unknown"
    ]

    # Valid activities (combined)
    ACTIVITIES = [
        "hiking", "climbing", "swimming", "photography", "exploration",
        "urbex", "camping", "biking", "running", "walking", "nature",
        "sightseeing", "picnic", "kayaking", "fishing", "birdwatching",
        "stargazing", "meditation", "trail_running", "rock_climbing"
    ]

    # Patterns that indicate mock/fake data
    MOCK_PATTERNS = [
        r'test[\s_-]?data', r'mock[\s_-]?data', r'fake[\s_-]?data',
        r'sample[\s_-]?data', r'example[\s_-]?data', r'demo[\s_-]?data',
        r'dummy[\s_-]?data', r'placeholder', r'lorem\s*ipsum', r'foo[\s_-]?bar',
        r'test\d+', r'user\d+', r'spot\d+', r'location\d+', r'example\.com'
    ]

    def __init__(self):
        """Initialize the validator with schema"""
        self.schema = self._create_schema()
        self.validation_stats = {"total": 0, "valid": 0, "invalid": 0}

    def _create_schema(self) -> Schema:
        """Create validation schema"""
        return Schema({
            "name": And(str, len, lambda x: 3 <= len(x) <= 100),
            "coordinates": {
                "latitude": And(Use(float), lambda x: self.TOULOUSE_BOUNDS["lat_min"] <= x <= self.TOULOUSE_BOUNDS["lat_max"]),
                "longitude": And(Use(float), lambda x: self.TOULOUSE_BOUNDS["lon_min"] <= x <= self.TOULOUSE_BOUNDS["lon_max"]),
            },
            SchemaOptional("type"): And(str, lambda x: x in self.LOCATION_TYPES),
            SchemaOptional("description"): And(str, lambda x: 10 <= len(x) <= 1000),
            SchemaOptional("activities"): [And(str, lambda x: x in self.ACTIVITIES)],
            SchemaOptional("hashtags"): [And(str, lambda x: x.startswith("#"))],
            SchemaOptional("source"): And(str, lambda x: x in ["instagram", "reddit", "manual", "tourist_office"]),
            SchemaOptional("verified"): bool,
            SchemaOptional("department"): And(str, lambda x: x in ["31", "34", "65", "11", "66", "09", "81", "82"]),
            SchemaOptional("created_at"): Or(str, datetime),
            SchemaOptional("updated_at"): Or(str, datetime),
        })

    def validate_spot(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate spot data against schema and business rules
        Returns (is_valid, error_message)
        """
        self.validation_stats["total"] += 1

        # Check for mock data patterns
        if self._contains_mock_data(data):
            self.validation_stats["invalid"] += 1
            return False, "Data appears to be mock/fake data"

        # Validate against schema
        try:
            self.schema.validate(data)
        except SchemaError as e:
            self.validation_stats["invalid"] += 1
            return False, f"Schema validation failed: {str(e)}"

        # Additional business rules
        if not self._validate_coordinates_precision(data.get("coordinates", {})):
            self.validation_stats["invalid"] += 1
            return False, "Coordinates lack required precision (need at least 4 decimal places)"

        if not self._validate_data_source(data):
            self.validation_stats["invalid"] += 1
            return False, "Data source validation failed"

        self.validation_stats["valid"] += 1
        return True, None

    def _contains_mock_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains mock/fake patterns"""
        data_str = str(data).lower()
        for pattern in self.MOCK_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                logger.warning(f"Mock data pattern detected: {pattern}")
                return True
        return False

    def _validate_coordinates_precision(self, coords: Dict[str, float]) -> bool:
        """Ensure coordinates have sufficient precision"""
        if not coords or "latitude" not in coords or "longitude" not in coords:
            return False
        
        lat_str = str(coords["latitude"])
        lon_str = str(coords["longitude"])
        
        # Check decimal places
        lat_decimals = len(lat_str.split(".")[-1]) if "." in lat_str else 0
        lon_decimals = len(lon_str.split(".")[-1]) if "." in lon_str else 0
        
        return lat_decimals >= 4 and lon_decimals >= 4

    def _validate_data_source(self, data: Dict[str, Any]) -> bool:
        """Validate data has proper source attribution"""
        source = data.get("source")
        if not source:
            return False
            
        # Check source-specific requirements
        if source == "instagram":
            return all(key in data for key in ["instagram_id", "username"])
        elif source == "reddit":
            return all(key in data for key in ["reddit_id", "subreddit"])
        elif source == "manual":
            return data.get("verified", False) and "verifier_id" in data
            
        return True

    def get_validation_stats(self) -> Dict[str, int]:
        """Get validation statistics"""
        return self.validation_stats.copy()

    def reset_stats(self):
        """Reset validation statistics"""
        self.validation_stats = {"total": 0, "valid": 0, "invalid": 0}