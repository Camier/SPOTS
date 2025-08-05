#!/usr/bin/env python3
"""
Puppeteer Instagram Scraper with Real-time Validation
Validates each post immediately as it's scraped
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from src.backend.core.logging_config import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.backend.scrapers.realtime_validated_scraper import RealtimeValidatedScraper
from src.backend.scrapers.unified_instagram_scraper import UnifiedInstagramScraper


class PuppeteerRealtimeValidator(RealtimeValidatedScraper):
    """Puppeteer scraper with real-time validation for Instagram"""

    def __init__(self, mcp_enabled: bool = True, fail_on_invalid: bool = False):
        super().__init__("instagram", fail_on_invalid)
        self.mcp_enabled = mcp_enabled
        self.scraper = UnifiedInstagramScraper(strategy="auto")
        self.browser_initialized = False

    async def initialize_browser(self):
        """Initialize Puppeteer via MCP"""
        if self.mcp_enabled:
            self.logger.info("🌐 Initializing Puppeteer browser...")
            # In real implementation, would call Puppeteer MCP
            # For now, we'll simulate
            self.browser_initialized = True
        else:
            self.logger.info("📝 Running in demo mode (no browser)")

    async def fetch_items(self) -> List[Dict]:
        """Fetch Instagram posts using Puppeteer MCP"""
        if not self.browser_initialized:
            await self.initialize_browser()

        if self.mcp_enabled:
            # Real implementation would:
            # 1. Navigate to Instagram
            # 2. Login if needed
            # 3. Search for location/hashtag
            # 4. Scroll and collect posts
            # 5. Extract post data

            # For demo, return simulated data
            self.logger.info("🔍 Fetching Instagram posts via Puppeteer...")

        # Simulated Instagram posts with various validation scenarios
        return [
            {
                "post_id": "C8zXyS3tL1j",
                "caption": "Journée parfaite au Lac de Salagou! 🏊‍♂️ Eau cristalline, idéale pour la baignade. #Occitanie #NatureLover",
                "timestamp": "2025-08-03T14:30:00Z",
                "likes": 245,
                "author": "@nature_explorer",
                "location_tag": "Lac de Salagou",
                "url": "https://instagram.com/p/C8zXyS3tL1j",
                "image_url": "https://instagram.com/image1.jpg",
            },
            {
                "post_id": "C8zXyS3tL2k",
                "caption": "Randonnée matinale au Pic du Canigou 🏔️ Vue à couper le souffle! Contact: user@email.com",
                "timestamp": "2025-08-03T08:15:00Z",
                "likes": 189,
                "author": "@hiker_66",
                "url": "https://instagram.com/p/C8zXyS3tL2k",
            },
            {
                "post_id": "C8zXyS3tL3l",
                "caption": "Escalade aux Gorges du Tarn aujourd'hui! 🧗‍♀️",
                "timestamp": "2025-08-03T16:45:00Z",
                "likes": -10,  # Invalid: negative
                "url": "invalid-url",  # Invalid: not a proper URL
            },
            {
                "post_id": "C8zXyS3tL4m",
                "caption": "Découverte des cascades près de Saint-Guilhem-le-Désert 💦",
                "timestamp": "not-a-date",  # Invalid: bad format
                "likes": 156,
                "url": "https://instagram.com/p/C8zXyS3tL4m",
            },
            {
                "post_id": "C8zXyS3tL5n",
                "caption": "Session VTT dans les Cévennes! 🚵‍♂️ Trails incroyables près de Florac. Tel: 06 12 34 56 78",
                "timestamp": "2025-08-03T11:00:00Z",
                "likes": 312,
                "author": "@vtt_occitanie",
                "location_tag": "Florac, Cévennes",
                "url": "https://instagram.com/p/C8zXyS3tL5n",
            },
            {
                "post_id": "",  # Invalid: empty ID
                "caption": "Camping sauvage autorisé près du Lac du Laouzas 🏕️",
                "timestamp": "2025-08-03T19:30:00Z",
                "likes": 67,
                "url": "https://instagram.com/p/C8zXyS3tL6o",
            },
            {
                "post_id": "C8zXyS3tL7p",
                "caption": "Balade en kayak sur le Tarn 🛶 Départ de La Malène",
                "timestamp": "2025-08-03T13:20:00Z",
                "likes": 423,
                "location_tag": "La Malène",
                "url": "https://instagram.com/p/C8zXyS3tL7p",
            },
            {
                "post_id": "C8zXyS3tL8q",
                "caption": "Pêche à la truite dans les Pyrénées 🎣 Spot secret près de Bagnères-de-Luchon",
                "timestamp": "2025-08-03T07:00:00Z",
                "likes": 98,
                "url": "https://instagram.com/p/C8zXyS3tL8q",
            },
        ]

    def transform_item(self, raw_item: Dict) -> Dict:
        """Transform Puppeteer data to Instagram schema format"""
        # Extract location from caption or location tag
        location = raw_item.get("location_tag")
        if not location:
            location = self.bp.extract_location_from_caption(raw_item.get("caption", ""))

        # Detect activities
        activities = self.bp.detect_activities(raw_item.get("caption", ""))

        # Geocode location
        coordinates = None
        if location:
            self.logger.debug(f"📍 Geocoding: {location}")
            coords = self.bp.geocode_location(location)
            if coords:
                coordinates = {"lat": coords[0], "lon": coords[1]}
                self.logger.debug(f"  ✅ Found: {coords}")

        # Build Instagram post according to schema
        return {
            "id": raw_item.get("post_id", ""),
            "caption": raw_item.get("caption", ""),
            "timestamp": raw_item.get("timestamp", ""),
            "likes": raw_item.get("likes", 0),
            "url": raw_item.get("url", ""),
            "location": location,
            "coordinates": coordinates,
            "activities": activities,
            "sentiment": self._analyze_sentiment(raw_item.get("caption", "")),
            "collected_at": datetime.now().isoformat(),
        }

    def _analyze_sentiment(self, text: str) -> Optional[str]:
        """Simple sentiment analysis"""
        positive_indicators = ["parfaite", "incroyable", "magnifique", "😍", "🏊‍♂️", "💦", "🏔️"]
        negative_indicators = ["dangereux", "interdit", "fermé", "pollué"]

        text_lower = text.lower()
        pos_count = sum(1 for ind in positive_indicators if ind in text_lower)
        neg_count = sum(1 for ind in negative_indicators if ind in text_lower)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        elif pos_count > 0:
            return "neutral"
        return None

    async def scrape_instagram_with_validation(
        self, search_query: str = "randonnée Occitanie", max_posts: int = 20
    ) -> Dict:
        """
        Main method to scrape Instagram with real-time validation

        Args:
            search_query: Search term for Instagram
            max_posts: Maximum posts to scrape

        Returns:
            Results dictionary with valid/invalid items and stats
        """
        self.logger.info(f"🎯 Starting Instagram scrape for: '{search_query}'")
        self.logger.info(f"📊 Real-time validation: {'ENABLED' if not self.fail_on_invalid else 'STRICT MODE'}")

        # Set up progress callbacks
        processed = 0

        def on_valid(item):
            nonlocal processed
            processed += 1
            location = item.get("location", "Unknown")
            activities = ", ".join(item.get("activities", [])) or "None"
            self.logger.info(f"  ✅ [{processed}] Valid: {location} | Activities: {activities}")

        def on_invalid(item, error):
            nonlocal processed
            processed += 1
            self.logger.warning(f"  ❌ [{processed}] Invalid: {error[:50]}...")

        self.set_validation_callbacks(on_valid, on_invalid)

        # Run scraping with validation
        results = await self.scrape_with_validation(max_items=max_posts)

        # Generate summary report
        self._generate_validation_report(results)

        return results

    def _generate_validation_report(self, results: Dict):
        """Generate detailed validation report"""
        stats = results["statistics"]

        report = f"""
{'=' * 60}
📊 REAL-TIME VALIDATION REPORT
{'=' * 60}

🎯 Scraping Summary:
  • Total items processed: {stats['total_items']}
  • Valid items: {stats['valid_items']} ({stats['validation_rate']:.1f}%)
  • Invalid items: {stats['invalid_items']}
  • Processing time: {stats['duration_seconds']:.1f}s
  • Speed: {stats['items_per_second']:.1f} items/second

📍 Location Detection:
  • Items with location: {sum(1 for item in results['valid_items'] if item.get('location'))}
  • Items with coordinates: {sum(1 for item in results['valid_items'] if item.get('coordinates'))}
  • Occitanie coverage: {sum(1 for item in results['valid_items'] if item.get('coordinates') and self.bp.is_in_occitanie(item['coordinates']['lat'], item['coordinates']['lon']))}

🏃 Activity Detection:
"""

        # Count activities
        activity_counts = {}
        for item in results["valid_items"]:
            for activity in item.get("activities", []):
                activity_counts[activity] = activity_counts.get(activity, 0) + 1

        for activity, count in sorted(activity_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"  • {activity}: {count} posts\n"

        if stats["top_errors"]:
            report += f"\n❌ Top Validation Errors:\n"
            for error, count in stats["top_errors"].items():
                report += f"  • {error[:60]}...: {count} times\n"

        report += f"\n{'=' * 60}"

        logger.info(report)

        # Save report
        report_file = f"exports/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)


async def demo_puppeteer_validation():
    """Demonstrate Puppeteer scraping with real-time validation"""
    logger.info("🚀 Puppeteer Instagram Scraper with Real-time Validation")
    logger.info("=" * 60)

    # Create scraper
    scraper = PuppeteerRealtimeValidator(mcp_enabled=False, fail_on_invalid=False)  # Demo mode  # Continue on errors

    # Run scraping
    results = await scraper.scrape_instagram_with_validation(search_query="outdoor Occitanie", max_posts=10)

    # Export valid results
    if results["valid_items"]:
        output_file = f"exports/puppeteer_validated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        scraper.export_valid_items(output_file)

    return results


async def demo_strict_validation():
    """Demonstrate strict validation (fail on first error)"""
    logger.info("\n\n🔒 STRICT VALIDATION MODE DEMO")
    logger.info("=" * 60)
    logger.info("Will stop on first validation error...")

    scraper = PuppeteerRealtimeValidator(mcp_enabled=False, fail_on_invalid=True)  # Strict mode

    try:
        results = await scraper.scrape_instagram_with_validation(max_posts=10)
    except ValueError as e:
        logger.info(f"\n⛔ Scraping stopped: {e}")
        logger.info(f"✅ Collected {len(scraper.valid_items)} valid items before error")

        if scraper.valid_items:
            output_file = f"exports/strict_validated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            scraper.export_valid_items(output_file)


if __name__ == "__main__":
    # Run demos
    asyncio.run(demo_puppeteer_validation())
    asyncio.run(demo_strict_validation())
