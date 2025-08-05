#!/usr/bin/env python3
"""
Instagram Scraper with JSON Schema Validation
Ensures all data conforms to defined schemas before storage
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from src.backend.core.logging_config import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.backend.validators.social_media_schemas import DataValidator, SocialMediaSchemas
from src.backend.scrapers.unified_instagram_scraper import UnifiedInstagramScraper
from src.backend.validators.real_data_validator import enforce_real_data


class ValidatedInstagramScraper(UnifiedInstagramScraper):
    """Instagram scraper with built-in schema validation"""

    def __init__(self):
        super().__init__(strategy="auto")
        self.validator = DataValidator()
        self.schemas = SocialMediaSchemas()

    def create_validated_spot(self, post_data: Dict) -> Optional[Dict]:
        """Create and validate Instagram spot data"""
        # Extract data using parent class methods
        location_name = self.extract_location_from_caption(post_data.get("caption", ""))
        activities = self.detect_activities(post_data.get("caption", ""))

        # Geocode if location found
        coordinates = None
        if location_name:
            coords = self.geocode_location(location_name)
            if coords:
                coordinates = {"lat": coords[0], "lon": coords[1]}

        # Build Instagram post data according to schema
        instagram_post = {
            "id": post_data.get("id", f"generated_{datetime.now().timestamp()}"),
            "caption": post_data.get("caption", ""),
            "timestamp": post_data.get("timestamp", datetime.now().isoformat()),
            "likes": post_data.get("likes", 0),
            "url": post_data.get("url", "https://instagram.com/p/unknown"),
            "location": location_name,
            "coordinates": coordinates,
            "activities": activities,
            "sentiment": self.analyze_sentiment(post_data.get("caption", "")),
            "collected_at": datetime.now().isoformat(),
        }

        # Validate against schema
        if self.validator.validate_instagram_post(instagram_post):
            return instagram_post
        else:
            logger.info(f"⚠️  Invalid Instagram post data for ID: {instagram_post['id']}")
            return None

    def analyze_sentiment(self, text: str) -> Optional[str]:
        """Simple sentiment analysis for French text"""
        if not text:
            return None

        positive_words = [
            "magnifique",
            "super",
            "génial",
            "incroyable",
            "parfait",
            "excellent",
            "merveilleux",
            "sublime",
            "😍",
            "❤️",
            "🔥",
        ]
        negative_words = ["nul", "mauvais", "dangereux", "fermé", "interdit", "sale", "pollué", "décevant", "😞", "👎"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        elif positive_count > 0 or negative_count > 0:
            return "neutral"
        else:
            return None

    def export_validated_data(self, posts: List[Dict], output_file: str):
        """Export validated Instagram data with proper schema"""
        validated_posts = []

        for post in posts:
            validated_post = self.create_validated_spot(post)
            if validated_post:
                validated_posts.append(validated_post)

        # Create export structure according to schema
        export_data = {
            "export_date": datetime.now().isoformat(),
            "source": "Instagram",  # Required field
            "total_spots": len(validated_posts),
            "spots": validated_posts,
        }

        # Validate entire export file
        validation_result = self.validator.validate_export_file(output_file)

        # Save file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✅ Exported {len(validated_posts)} validated Instagram spots")
        logger.info(f"📁 File: {output_file}")

        # Validate the saved file
        validation_result = self.validator.validate_export_file(output_file)
        if validation_result["valid"]:
            logger.info("✅ Export file passes schema validation!")
        else:
            logger.info(f"⚠️  Validation issues: {validation_result.get('errors', [])}")

        return export_data


def demo_validated_scraping():
    """Demonstrate validated Instagram scraping"""
    scraper = ValidatedInstagramScraper()

    # Sample Instagram posts
    sample_posts = [
        {
            "id": "3382721454605055587",
            "caption": "Magnifique journée au Lac de Salagou! 😍 Eau cristalline parfaite pour la baignade. #Occitanie #OutdoorLife",
            "timestamp": "2025-08-03T14:30:00Z",
            "likes": 245,
            "url": "https://instagram.com/p/C8zXyS3tL1j",
        },
        {
            "id": "3382721454605055588",
            "caption": "Randonnée épique au Pic du Canigou ce matin! Vue à 360° sur les Pyrénées 🏔️",
            "timestamp": "2025-08-03T10:15:00Z",
            "likes": 189,
            "url": "https://instagram.com/p/C8zXyS3tL1k",
        },
        {
            "id": "3382721454605055589",
            "caption": "Session escalade aux Gorges du Tarn. Voies incroyables! Contact: user@example.com",
            "timestamp": "2025-08-03T16:45:00Z",
            "likes": 156,
            "url": "https://instagram.com/p/C8zXyS3tL1l",
        },
    ]

    logger.info("🔍 Processing Instagram posts with validation...")

    # Process each post
    for post in sample_posts:
        validated = scraper.create_validated_spot(post)
        if validated:
            logger.info(f"\n✅ Validated post: {validated['location'] or 'Unknown'}")
            logger.info(f"   Activities: {', '.join(validated['activities'])}")
            logger.info(f"   Sentiment: {validated['sentiment']}")
            logger.info(f"   Coordinates: {validated['coordinates']}")

    # Export with validation
    output_file = f"exports/validated_instagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.export_validated_data(sample_posts, output_file)


if __name__ == "__main__":
    demo_validated_scraping()
