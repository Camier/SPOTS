#!/usr/bin/env python3
"""
JSON Schema Validation for Social Media Data Storage
Ensures data consistency and integrity across Instagram and Facebook scrapers
"""

from jsonschema import validate, ValidationError, Draft7Validator
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import re
from src.backend.core.logging_config import logger


class SocialMediaSchemas:
    """JSON schemas for validating social media post data"""

    # Instagram post schema
    INSTAGRAM_POST_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["id", "caption", "timestamp", "likes", "url"],
        "properties": {
            "id": {"type": "string", "minLength": 1, "description": "Unique Instagram post ID"},
            "caption": {"type": "string", "description": "Post caption text (can be empty)"},
            "timestamp": {"type": "string", "format": "date-time", "description": "ISO 8601 formatted timestamp"},
            "likes": {"type": "integer", "minimum": 0, "description": "Number of likes"},
            "url": {"type": "string", "format": "uri", "pattern": "^https?://", "description": "Instagram post URL"},
            "location": {"type": ["string", "null"], "description": "Location name extracted from post"},
            "coordinates": {
                "type": ["object", "null"],
                "properties": {"lat": {"type": ["number", "null"]}, "lon": {"type": ["number", "null"]}},
                "required": ["lat", "lon"],
            },
            "activities": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["randonnée", "baignade", "escalade", "vtt", "kayak", "camping", "pêche", "spéléo"],
                },
                "description": "Outdoor activities detected",
            },
            "sentiment": {
                "type": ["string", "null"],
                "enum": ["positive", "neutral", "negative", None],
                "description": "Sentiment analysis result",
            },
            "collected_at": {"type": "string", "format": "date-time", "description": "When data was collected"},
        },
        "additionalProperties": False,
    }

    # Facebook post schema
    FACEBOOK_POST_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["name", "location_text", "description", "source_type", "collected_at"],
        "properties": {
            "name": {"type": "string", "minLength": 1, "description": "Primary location name"},
            "location_text": {"type": "string", "description": "Full location text (can include multiple places)"},
            "coordinates": {
                "type": ["array", "null"],
                "items": {"type": "number"},
                "minItems": 2,
                "maxItems": 2,
                "description": "Latitude, longitude tuple",
            },
            "description": {"type": "string", "maxLength": 1000, "description": "Sanitized post text"},
            "activities": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["randonnée", "baignade", "escalade", "vtt", "kayak", "camping", "pêche", "spéléo"],
                },
            },
            "source_url": {"type": "string", "description": "Facebook source URL (sanitized)"},
            "source_name": {"type": "string", "description": "Page/group name"},
            "source_type": {
                "type": "string",
                "enum": ["group", "page", "event", "post", "search"],
                "description": "Type of Facebook source",
            },
            "author": {"type": "string", "pattern": "^(Anonymous|Unknown|User)$", "description": "Anonymized author"},
            "post_date": {"type": "string", "format": "date-time"},
            "images": {
                "type": "array",
                "items": {"type": "string", "pattern": "^image_\\d+\\.jpg$"},
                "description": "Sanitized image references",
            },
            "engagement": {
                "type": "object",
                "properties": {
                    "likes": {"type": "integer", "minimum": 0},
                    "comments": {"type": "integer", "minimum": 0},
                    "shares": {"type": "integer", "minimum": 0},
                },
                "additionalProperties": False,
            },
            "comments_sample": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
                "description": "Sample of sanitized comments",
            },
            "collected_at": {"type": "string", "format": "date-time"},
        },
        "additionalProperties": False,
    }

    # Unified spot schema (after processing)
    UNIFIED_SPOT_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["name", "source", "activities", "collected_at"],
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "source": {"type": "string", "enum": ["instagram", "facebook"]},
            "coordinates": {
                "type": ["object", "null"],
                "properties": {
                    "lat": {"type": "number", "minimum": 42.0, "maximum": 45.0},
                    "lon": {"type": "number", "minimum": -0.5, "maximum": 4.5},
                },
                "required": ["lat", "lon"],
                "description": "Coordinates within Occitanie bounds",
            },
            "department": {
                "type": ["string", "null"],
                "pattern": "^(09|11|12|30|31|32|34|46|48|65|66|81|82)$",
                "description": "Occitanie department code",
            },
            "activities": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["randonnée", "baignade", "escalade", "vtt", "kayak", "camping", "pêche", "spéléo"],
                },
            },
            "type": {
                "type": "string",
                "enum": ["lac", "montagne", "gorge", "cascade", "forêt", "grotte", "nature_spot"],
            },
            "engagement_score": {"type": "number", "minimum": 0},
            "elevation_ign": {"type": ["number", "null"], "description": "Elevation in meters from IGN data"},
            "nearest_water": {
                "type": ["object", "null"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "distance": {"type": "number", "minimum": 0},
                },
            },
            "nearby_trails": {
                "type": ["array", "null"],
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "distance": {"type": "number", "minimum": 0},
                    },
                },
            },
            "forest_info": {
                "type": ["object", "null"],
                "properties": {"in_forest": {"type": "boolean"}, "forest_type": {"type": "string"}},
            },
            "collected_at": {"type": "string", "format": "date-time"},
            "last_updated": {"type": "string", "format": "date-time"},
        },
        "additionalProperties": False,
    }

    # Export file schema
    EXPORT_FILE_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["export_date", "source", "total_spots", "spots"],
        "properties": {
            "export_date": {"type": "string", "format": "date-time"},
            "source": {"type": "string", "enum": ["Instagram", "Facebook", "Combined"]},
            "total_spots": {"type": "integer", "minimum": 0},
            "enrichment_source": {"type": ["string", "null"], "description": "e.g., 'IGN Open Data'"},
            "spots": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"$ref": "#/definitions/instagram_post"},
                        {"$ref": "#/definitions/facebook_post"},
                        {"$ref": "#/definitions/unified_spot"},
                    ]
                },
            },
        },
        "definitions": {
            "instagram_post": INSTAGRAM_POST_SCHEMA,
            "facebook_post": FACEBOOK_POST_SCHEMA,
            "unified_spot": UNIFIED_SPOT_SCHEMA,
        },
    }


class DataValidator:
    """Validates social media data against schemas"""

    def __init__(self):
        self.schemas = SocialMediaSchemas()

    def validate_instagram_post(self, data: Dict[str, Any]) -> bool:
        """Validate Instagram post data"""
        try:
            validate(instance=data, schema=self.schemas.INSTAGRAM_POST_SCHEMA)
            return True
        except ValidationError as e:
            logger.info(f"Instagram validation error: {e.message}")
            return False

    def validate_facebook_post(self, data: Dict[str, Any]) -> bool:
        """Validate Facebook post data"""
        try:
            validate(instance=data, schema=self.schemas.FACEBOOK_POST_SCHEMA)
            return True
        except ValidationError as e:
            logger.info(f"Facebook validation error: {e.message}")
            return False

    def validate_unified_spot(self, data: Dict[str, Any]) -> bool:
        """Validate unified spot data"""
        try:
            validate(instance=data, schema=self.schemas.UNIFIED_SPOT_SCHEMA)
            return True
        except ValidationError as e:
            logger.info(f"Unified spot validation error: {e.message}")
            return False

    def validate_export_file(self, file_path: str) -> Dict[str, Any]:
        """Validate an entire export file"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Basic file structure validation
        try:
            validate(instance=data, schema=self.schemas.EXPORT_FILE_SCHEMA)
        except ValidationError as e:
            return {"valid": False, "error": f"File structure error: {e.message}", "path": list(e.absolute_path)}

        # Validate individual spots based on source
        source = data.get("source", "").lower()
        spots = data.get("spots", [])

        errors = []
        for i, spot in enumerate(spots):
            try:
                if source == "instagram":
                    validate(instance=spot, schema=self.schemas.INSTAGRAM_POST_SCHEMA)
                elif source == "facebook":
                    validate(instance=spot, schema=self.schemas.FACEBOOK_POST_SCHEMA)
                else:  # Combined or unified
                    validate(instance=spot, schema=self.schemas.UNIFIED_SPOT_SCHEMA)
            except ValidationError as e:
                errors.append({"index": i, "error": e.message, "path": list(e.absolute_path)})

        return {"valid": len(errors) == 0, "total_spots": len(spots), "errors": errors, "source": source}

    def sanitize_and_validate(self, data: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """Sanitize data and validate against appropriate schema"""
        # Sanitization patterns
        email_pattern = r"\S+@\S+\.\S+"
        phone_pattern = r"(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}"

        # Deep copy to avoid modifying original
        import copy

        sanitized = copy.deepcopy(data)

        # Recursive sanitization
        def sanitize_value(value):
            if isinstance(value, str):
                value = re.sub(email_pattern, "[email]", value)
                value = re.sub(phone_pattern, "[phone]", value)
                value = re.sub(r"@[\w.]+", "[user]", value)
            elif isinstance(value, dict):
                for k, v in value.items():
                    value[k] = sanitize_value(v)
            elif isinstance(value, list):
                value = [sanitize_value(item) for item in value]
            return value

        sanitized = sanitize_value(sanitized)

        # Validate
        try:
            if source == "instagram":
                validate(instance=sanitized, schema=self.schemas.INSTAGRAM_POST_SCHEMA)
            elif source == "facebook":
                validate(instance=sanitized, schema=self.schemas.FACEBOOK_POST_SCHEMA)
            else:
                validate(instance=sanitized, schema=self.schemas.UNIFIED_SPOT_SCHEMA)
            return sanitized
        except ValidationError:
            return None


def demo_validation():
    """Demonstrate schema validation"""
    validator = DataValidator()

    # Test Instagram post
    instagram_post = {
        "id": "3382721454605055587",
        "caption": "Le lac d'Oô 😍 Un incontournable des Pyrénées! #pyreneescachees",
        "timestamp": "2024-06-13T14:34:48Z",
        "likes": 164,
        "url": "https://instagram.com/p/C8zXyS3tL1j",
        "location": "Lac d'Oô, Haute-Garonne",
        "activities": ["randonnée", "baignade"],
        "sentiment": "positive",
        "collected_at": "2025-08-03T20:00:00Z",
    }

    logger.info("🔍 Validating Instagram post...")
    if validator.validate_instagram_post(instagram_post):
        logger.info("✅ Instagram post is valid!")

    # Test Facebook post
    facebook_post = {
        "name": "Lac de Salagou",
        "location_text": "Lac de Salagou, Hérault",
        "coordinates": [43.6508, 3.3857],
        "description": "Beautiful lake for swimming and hiking! Contact [email] for info",
        "activities": ["baignade", "randonnée"],
        "source_url": "https://facebook.com/groups/example",
        "source_name": "Outdoor Occitanie",
        "source_type": "group",
        "author": "Anonymous",
        "post_date": "2025-08-01T10:00:00Z",
        "images": ["image_0.jpg", "image_1.jpg"],
        "engagement": {"likes": 245, "comments": 34, "shares": 12},
        "comments_sample": ["Great spot!", "Water was perfect"],
        "collected_at": "2025-08-03T20:00:00Z",
    }

    logger.info("\n🔍 Validating Facebook post...")
    if validator.validate_facebook_post(facebook_post):
        logger.info("✅ Facebook post is valid!")

    # Test unified spot
    unified_spot = {
        "name": "Pic du Canigou",
        "source": "instagram",
        "coordinates": {"lat": 42.5197, "lon": 2.4563},
        "department": "66",
        "activities": ["randonnée", "escalade"],
        "type": "montagne",
        "engagement_score": 450.5,
        "elevation_ign": 2784.0,
        "nearest_water": {"name": "Lac des Cortalets", "type": "Lac", "distance": 1200.0},
        "nearby_trails": [{"name": "GR10", "type": "Sentier", "distance": 0.0}],
        "forest_info": {"in_forest": True, "forest_type": "Forêt de conifères"},
        "collected_at": "2025-08-03T20:00:00Z",
        "last_updated": "2025-08-03T21:00:00Z",
    }

    logger.info("\n🔍 Validating unified spot...")
    if validator.validate_unified_spot(unified_spot):
        logger.info("✅ Unified spot is valid!")

    # Test invalid data
    logger.info("\n🔍 Testing invalid data...")
    invalid_post = {
        "id": "123",
        "caption": "Test",
        "likes": -5,  # Invalid: negative likes
        "url": "not-a-url",  # Invalid: not a URI
        "timestamp": "yesterday",  # Invalid: not ISO format
    }

    if not validator.validate_instagram_post(invalid_post):
        logger.info("❌ Invalid post correctly rejected!")

    # Test sanitization
    logger.info("\n🔍 Testing sanitization...")
    dirty_data = {
        "name": "Lac Test",
        "location_text": "Near user@example.com",
        "description": "Call 06 12 34 56 78 or @username for info",
        "source_type": "group",
        "collected_at": "2025-08-03T20:00:00Z",
    }

    sanitized = validator.sanitize_and_validate(dirty_data, "facebook")
    if sanitized:
        logger.info("✅ Data sanitized successfully:")
        logger.info(f"  - Email removed: {sanitized['location_text']}")
        logger.info(f"  - Phone removed: {sanitized['description']}")


if __name__ == "__main__":
    demo_validation()
