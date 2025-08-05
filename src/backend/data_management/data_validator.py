#!/usr/bin/env python3
"""
Data Validator - Ensures data quality and compliance
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from src.backend.core.logging_config import logger


class DataValidator:
    """Validates and ensures data quality"""

    def __init__(self):
        self.validation_rules = {
            "location_name": self._validate_location,
            "coordinates": self._validate_coordinates,
            "caption": self._validate_caption,
            "hashtags": self._validate_hashtags,
            "department": self._validate_department,
            "activities": self._validate_activities,
        }

    def _validate_location(self, location: str) -> Tuple[bool, Optional[str]]:
        """Validate location name"""
        if not location or len(location) < 3:
            return False, "Location name too short"

        if len(location) > 100:
            return False, "Location name too long"

        # Check for spam patterns
        spam_patterns = ["buy", "sale", "discount", "promo", "click here", "link in bio"]
        if any(pattern in location.lower() for pattern in spam_patterns):
            return False, "Location contains spam"

        return True, None

    def _validate_coordinates(self, lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        """Validate GPS coordinates for Occitanie region"""
        # Occitanie approximate bounds (includes Pyrénées-Orientales in the east)
        if not (42.0 <= lat <= 45.0):
            return False, f"Latitude {lat} outside Occitanie bounds"

        if not (-0.5 <= lon <= 4.5):
            return False, f"Longitude {lon} outside Occitanie bounds"

        return True, None

    def _validate_caption(self, caption: str) -> Tuple[bool, Optional[str]]:
        """Validate caption content"""
        if not caption:
            return True, None  # Empty caption is OK

        # Check length
        if len(caption) > 5000:
            return False, "Caption too long"

        # Check for excessive hashtags
        hashtag_count = caption.count("#")
        if hashtag_count > 30:
            return False, "Too many hashtags in caption"

        # Check for spam
        spam_indicators = ["DM for collab", "link in bio", "swipe up", "giveaway"]
        spam_count = sum(1 for indicator in spam_indicators if indicator.lower() in caption.lower())
        if spam_count >= 2:
            return False, "Caption appears to be spam"

        return True, None

    def _validate_hashtags(self, hashtags: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate hashtags"""
        if not hashtags:
            return True, None

        if len(hashtags) > 30:
            return False, "Too many hashtags"

        # Check each hashtag
        for tag in hashtags:
            if len(tag) > 100:
                return False, f"Hashtag too long: {tag}"

            if not re.match(r"^#?[\w]+$", tag):
                return False, f"Invalid hashtag format: {tag}"

        return True, None

    def _validate_department(self, dept: str) -> Tuple[bool, Optional[str]]:
        """Validate Occitanie department"""
        # All Occitanie departments:
        # 09 - Ariège, 11 - Aude, 12 - Aveyron, 30 - Gard
        # 31 - Haute-Garonne, 32 - Gers, 34 - Hérault, 46 - Lot
        # 48 - Lozère, 65 - Hautes-Pyrénées, 66 - Pyrénées-Orientales
        # 81 - Tarn, 82 - Tarn-et-Garonne
        occitanie_depts = ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"]

        if dept and dept not in occitanie_depts:
            return False, f"Department {dept} not in Occitanie"

        return True, None

    def _validate_activities(self, activities: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate activities list"""
        valid_activities = [
            "baignade",
            "randonnée",
            "escalade",
            "kayak",
            "vtt",
            "camping",
            "pêche",
            "photographie",
            "spéléologie",
            "canyoning",
            "parapente",
            "ski",
            "observation",
            "pique-nique",
        ]

        if not activities:
            return True, None

        for activity in activities:
            if activity not in valid_activities:
                return False, f"Unknown activity: {activity}"

        return True, None

    def validate_spot_data(self, spot_data: Dict) -> Tuple[bool, List[str]]:
        """Validate complete spot data"""
        errors = []

        # Required fields
        required_fields = ["location_name", "source"]
        for field in required_fields:
            if field not in spot_data or not spot_data[field]:
                errors.append(f"Missing required field: {field}")

        # Validate each field
        if "location_name" in spot_data:
            valid, error = self._validate_location(spot_data["location_name"])
            if not valid:
                errors.append(error)

        if "lat" in spot_data and "lon" in spot_data:
            try:
                lat = float(spot_data["lat"])
                lon = float(spot_data["lon"])
                valid, error = self._validate_coordinates(lat, lon)
                if not valid:
                    errors.append(error)
            except (ValueError, TypeError):
                errors.append("Invalid coordinate format")

        if "caption" in spot_data:
            valid, error = self._validate_caption(spot_data["caption"])
            if not valid:
                errors.append(error)

        if "hashtags" in spot_data:
            valid, error = self._validate_hashtags(spot_data["hashtags"])
            if not valid:
                errors.append(error)

        if "department" in spot_data:
            valid, error = self._validate_department(spot_data["department"])
            if not valid:
                errors.append(error)

        if "activities" in spot_data:
            valid, error = self._validate_activities(spot_data["activities"])
            if not valid:
                errors.append(error)

        return len(errors) == 0, errors

    def clean_spot_data(self, spot_data: Dict) -> Dict:
        """Clean and normalize spot data"""
        cleaned = spot_data.copy()

        # Normalize location name
        if "location_name" in cleaned:
            cleaned["location_name"] = cleaned["location_name"].strip().title()

        # Clean hashtags
        if "hashtags" in cleaned:
            cleaned["hashtags"] = [tag.lower().strip().replace("#", "") for tag in cleaned["hashtags"] if tag.strip()]

        # Normalize activities
        if "activities" in cleaned:
            cleaned["activities"] = [activity.lower().strip() for activity in cleaned["activities"]]

        # Add metadata
        cleaned["validated_at"] = datetime.now().isoformat()
        cleaned["data_quality"] = "validated"

        return cleaned


def main():
    """Example usage"""
    validator = DataValidator()

    # Test data
    test_spots = [
        {
            "location_name": "Lac de Salagou",
            "lat": 43.6508,
            "lon": 3.3857,
            "department": "34",
            "caption": "Beautiful lake for swimming!",
            "hashtags": ["#lacsalagou", "#swimming", "#occitanie"],
            "activities": ["baignade", "randonnée"],
            "source": "instagram",
        },
        {
            "location_name": "CLICK HERE FOR DISCOUNT!!!",
            "lat": 50.0,  # Outside Occitanie
            "caption": "DM for collab! Link in bio! Swipe up!",
            "hashtags": ["#" * 50],  # Invalid
            "source": "instagram",
        },
    ]

    for i, spot in enumerate(test_spots):
        logger.info(f"\n--- Testing Spot {i+1} ---")
        valid, errors = validator.validate_spot_data(spot)

        if valid:
            logger.info("✅ Valid spot data")
            cleaned = validator.clean_spot_data(spot)
            logger.info(f"Location: {cleaned['location_name']}")
            logger.info(f"Activities: {cleaned.get('activities', [])}")
        else:
            logger.info("❌ Invalid spot data:")
            for error in errors:
                logger.info(f"   - {error}")


if __name__ == "__main__":
    main()
