#!/usr/bin/env python3
"""
Real-time Validation Scraper Base Class
Validates data immediately during scraping to ensure quality
"""

import sys
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from src.backend.core.logging_config import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.backend.validators.social_media_schemas import DataValidator, SocialMediaSchemas
from src.backend.validators.real_data_validator import enforce_real_data


class ValidationStats:
    """Track validation statistics during scraping"""

    def __init__(self):
        self.total_items = 0
        self.valid_items = 0
        self.invalid_items = 0
        self.validation_errors = defaultdict(int)
        self.start_time = datetime.now()

    def add_valid(self):
        self.total_items += 1
        self.valid_items += 1

    def add_invalid(self, error: str):
        self.total_items += 1
        self.invalid_items += 1
        self.validation_errors[error] += 1

    def get_summary(self) -> Dict:
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "total_items": self.total_items,
            "valid_items": self.valid_items,
            "invalid_items": self.invalid_items,
            "validation_rate": (self.valid_items / self.total_items * 100) if self.total_items > 0 else 0,
            "duration_seconds": duration,
            "items_per_second": self.total_items / duration if duration > 0 else 0,
            "top_errors": dict(sorted(self.validation_errors.items(), key=lambda x: x[1], reverse=True)[:5]),
        }


class RealtimeValidatedScraper(ABC):
    """Base class for scrapers with real-time validation"""

    def __init__(self, source_type: str, fail_on_invalid: bool = False):
        """
        Initialize scraper with validation

        Args:
            source_type: 'instagram' or 'facebook'
            fail_on_invalid: If True, stop scraping on first invalid item
        """
        self.source_type = source_type
        self.fail_on_invalid = fail_on_invalid
        self.validator = DataValidator()
        self.schemas = SocialMediaSchemas()
        self.stats = ValidationStats()
        self.valid_items = []
        self.invalid_items = []

        # Setup logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(self.__class__.__name__)

        # Validation callbacks
        self.on_valid_item: Optional[Callable] = None
        self.on_invalid_item: Optional[Callable] = None

    @abstractmethod
    async def fetch_items(self) -> List[Dict]:
        """Fetch items from source - must be implemented by subclass"""
        pass

    @abstractmethod
    def transform_item(self, raw_item: Dict) -> Dict:
        """Transform raw item to schema format - must be implemented by subclass"""
        pass

    def validate_item(self, item: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate single item against appropriate schema

        Returns:
            (is_valid, error_message)
        """
        try:
            if self.source_type == "instagram":
                self.validator.validate_instagram_post(item)
            elif self.source_type == "facebook":
                self.validator.validate_facebook_post(item)
            else:
                self.validator.validate_unified_spot(item)
            return True, None
        except Exception as e:
            return False, str(e)

    def sanitize_item(self, item: Dict) -> Dict:
        """Sanitize item to remove PII"""
        return self.validator.sanitize_and_validate(item, self.source_type)

    async def scrape_with_validation(self, max_items: Optional[int] = None) -> Dict:
        """
        Main scraping method with real-time validation

        Args:
            max_items: Maximum items to scrape (None for all)

        Returns:
            Dictionary with results and statistics
        """
        self.logger.info(f"Starting {self.source_type} scraping with real-time validation")

        try:
            # Fetch items
            raw_items = await self.fetch_items()

            if max_items:
                raw_items = raw_items[:max_items]

            self.logger.info(f"Fetched {len(raw_items)} items to process")

            # Process each item with validation
            for i, raw_item in enumerate(raw_items):
                try:
                    # Transform to schema format
                    transformed = self.transform_item(raw_item)

                    # Sanitize PII
                    sanitized = self.sanitize_item(transformed)
                    if not sanitized:
                        raise ValueError("Sanitization failed")

                    # Validate
                    is_valid, error = self.validate_item(sanitized)

                    if is_valid:
                        self.valid_items.append(sanitized)
                        self.stats.add_valid()

                        # Log every 10 valid items
                        if self.stats.valid_items % 10 == 0:
                            self.logger.info(f"✅ Validated {self.stats.valid_items} items")

                        # Call callback if set
                        if self.on_valid_item:
                            self.on_valid_item(sanitized)
                    else:
                        self.invalid_items.append({"item": transformed, "error": error, "index": i})
                        self.stats.add_invalid(error or "Unknown error")

                        self.logger.warning(f"❌ Invalid item {i}: {error}")

                        # Call callback if set
                        if self.on_invalid_item:
                            self.on_invalid_item(transformed, error)

                        # Fail fast if configured
                        if self.fail_on_invalid:
                            raise ValueError(f"Invalid item at index {i}: {error}")

                except Exception as e:
                    self.logger.error(f"Error processing item {i}: {e}")
                    self.stats.add_invalid(str(e))

                    if self.fail_on_invalid:
                        raise

            # Final summary
            summary = self.stats.get_summary()
            self.logger.info(
                f"""
Scraping completed:
  ✅ Valid items: {summary['valid_items']}
  ❌ Invalid items: {summary['invalid_items']}
  📊 Validation rate: {summary['validation_rate']:.1f}%
  ⏱️  Duration: {summary['duration_seconds']:.1f}s
  🚀 Speed: {summary['items_per_second']:.1f} items/s
            """
            )

            return {"valid_items": self.valid_items, "invalid_items": self.invalid_items, "statistics": summary}

        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            raise

    def export_valid_items(self, output_file: str):
        """Export only valid items to file"""
        export_data = {
            "export_date": datetime.now().isoformat(),
            "source": self.source_type.capitalize(),
            "total_spots": len(self.valid_items),
            "validation_stats": self.stats.get_summary(),
            "spots": self.valid_items,
        }

        # Ensure directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"✅ Exported {len(self.valid_items)} valid items to {output_file}")

    def set_validation_callbacks(self, on_valid: Callable = None, on_invalid: Callable = None):
        """Set callbacks for validation events"""
        self.on_valid_item = on_valid
        self.on_invalid_item = on_invalid


class RealtimeInstagramScraper(RealtimeValidatedScraper):
    """Example Instagram scraper with real-time validation"""

    def __init__(self, fail_on_invalid: bool = False):
        super().__init__("instagram", fail_on_invalid)

    async def fetch_items(self) -> List[Dict]:
        """Fetch Instagram posts (demo with sample data)"""
        # In reality, this would use Puppeteer/Playwright
        return [
            {
                "id": "123456789",
                "caption": "Belle journée au Lac de Salagou! 🏊‍♂️ #Occitanie",
                "timestamp": "2025-08-03T14:00:00Z",
                "likes": 156,
                "url": "https://instagram.com/p/test1",
            },
            {
                "id": "987654321",
                "caption": "Randonnée au Pic du Canigou, vue incroyable!",
                "timestamp": "2025-08-03T10:00:00Z",
                "likes": -5,  # Invalid: negative likes
                "url": "https://instagram.com/p/test2",
            },
            {
                "id": "456789123",
                "caption": "Escalade dans les Gorges du Tarn 🧗",
                "timestamp": "invalid-date",  # Invalid: bad timestamp
                "likes": 89,
                "url": "https://instagram.com/p/test3",
            },
            {
                "id": "789123456",
                "caption": "Camping sauvage près de Montpellier avec @username",
                "timestamp": "2025-08-03T18:00:00Z",
                "likes": 234,
                "url": "https://instagram.com/p/test4",
            },
        ]

    def transform_item(self, raw_item: Dict) -> Dict:
        """Transform to Instagram schema format"""
        from src.backend.scrapers.unified_instagram_scraper import UnifiedInstagramScraper

        scraper = UnifiedInstagramScraper(strategy="auto")

        # Extract location and activities
        # Note: These methods are now part of the unified scraper's internal processing
        location = None  # Will be extracted during scraping
        activities = []  # Will be detected during scraping

        # Get coordinates if location found
        coordinates = None
        if location:
            coords = bp.geocode_location(location)
            if coords:
                coordinates = {"lat": coords[0], "lon": coords[1]}

        return {
            "id": raw_item.get("id", ""),
            "caption": raw_item.get("caption", ""),
            "timestamp": raw_item.get("timestamp", ""),
            "likes": raw_item.get("likes", 0),
            "url": raw_item.get("url", ""),
            "location": location,
            "coordinates": coordinates,
            "activities": activities,
            "sentiment": "positive" if any(e in raw_item.get("caption", "") for e in ["😍", "🏊‍♂️", "🧗"]) else None,
            "collected_at": datetime.now().isoformat(),
        }


async def demo_realtime_validation():
    """Demonstrate real-time validation during scraping"""
    logger.info("🚀 Real-time Validation Demo")
    logger.info("=" * 50)

    # Create scraper with validation
    scraper = RealtimeInstagramScraper(fail_on_invalid=False)

    # Set up callbacks to show real-time feedback
    def on_valid(item):
        logger.info(f"  ✅ Valid: {item.get('location', 'Unknown')} - {item.get('caption', '')[:30]}...")

    def on_invalid(item, error):
        logger.info(f"  ❌ Invalid: {error}")

    scraper.set_validation_callbacks(on_valid, on_invalid)

    # Run scraping with validation
    logger.info("\n📊 Processing items with real-time validation:\n")
    results = await scraper.scrape_with_validation(max_items=10)

    # Export valid items
    output_file = f"exports/realtime_validated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.export_valid_items(output_file)

    # Show invalid items details
    if results["invalid_items"]:
        logger.info("\n⚠️  Invalid Items Details:")
        for invalid in results["invalid_items"]:
            logger.info(f"  - Item {invalid['index']}: {invalid['error']}")

    return results


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_realtime_validation())
