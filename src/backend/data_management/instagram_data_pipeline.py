#!/usr/bin/env python3
"""
Instagram Data Pipeline - Complete data handling workflow
Integrates scraping, validation, sanitization, and storage
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from src.backend.core.logging_config import logger

from ..scrapers.instagram_data_handler import InstagramDataHandler
from .data_validator import DataValidator
from ..scrapers.geocoding_france import OccitanieGeocoder


class InstagramDataPipeline:
    """Complete pipeline for Instagram data processing"""

    def __init__(self):
        self.handler = InstagramDataHandler()
        self.validator = DataValidator()
        self.geocoder = OccitanieGeocoder()

        # Setup logging
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_dir / "instagram_pipeline.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def process_instagram_post(self, raw_post: Dict) -> Optional[Dict]:
        """Process a single Instagram post through the pipeline"""

        self.logger.info(f"Processing post: {raw_post.get('post_id', 'unknown')}")

        # Step 1: Initial validation
        valid, errors = self.validator.validate_spot_data(raw_post)
        if not valid:
            self.logger.warning(f"Validation failed: {errors}")
            return None

        # Step 2: Clean data
        cleaned_post = self.validator.clean_spot_data(raw_post)

        # Step 3: Geocode if needed
        if "location_name" in cleaned_post and not cleaned_post.get("lat"):
            self.logger.info(f"Geocoding: {cleaned_post['location_name']}")
            geocoded = self.geocoder.enhance_spot_with_geocoding(
                {
                    "name": cleaned_post["location_name"],
                    "address_hint": f"{cleaned_post['location_name']}, Occitanie, France",
                }
            )

            if geocoded.get("latitude"):
                cleaned_post["lat"] = geocoded["latitude"]
                cleaned_post["lon"] = geocoded["longitude"]
                cleaned_post["department"] = geocoded.get("department")
                cleaned_post["city"] = geocoded.get("city")

        # Step 4: Final validation with coordinates
        valid, errors = self.validator.validate_spot_data(cleaned_post)
        if not valid:
            self.logger.warning(f"Post-geocoding validation failed: {errors}")
            return None

        # Step 5: Store in database
        success = self.handler.store_instagram_spot(cleaned_post)
        if success:
            self.logger.info(f"Successfully stored: {cleaned_post['location_name']}")
            return cleaned_post
        else:
            self.logger.error(f"Failed to store: {cleaned_post['location_name']}")
            return None

    def process_batch(self, posts: List[Dict]) -> Dict:
        """Process a batch of Instagram posts"""

        self.logger.info(f"Starting batch processing of {len(posts)} posts")

        results = {"processed": 0, "stored": 0, "failed": 0, "errors": [], "locations": []}

        for post in posts:
            try:
                processed = self.process_instagram_post(post)
                if processed:
                    results["processed"] += 1
                    results["stored"] += 1
                    results["locations"].append(processed["location_name"])
                else:
                    results["failed"] += 1

            except Exception as e:
                self.logger.error(f"Error processing post: {e}")
                results["failed"] += 1
                results["errors"].append(str(e))

        # Generate summary
        summary = self.handler.get_spots_summary()
        results["summary"] = summary

        self.logger.info(f"Batch complete: {results['stored']} stored, {results['failed']} failed")

        return results

    def export_data(self, format: str = "json") -> Path:
        """Export processed data"""

        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            # Get all data from database
            import sqlite3

            conn = sqlite3.connect(self.handler.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT location_name, location_lat, location_lon, department,
                       caption_sanitized, activities, spot_type, collected_at
                FROM instagram_spots
                WHERE privacy_compliant = 1
            """
            )

            spots = []
            for row in cursor.fetchall():
                spots.append(
                    {
                        "name": row[0],
                        "coordinates": {"lat": row[1], "lon": row[2]},
                        "department": row[3],
                        "caption": row[4],
                        "activities": json.loads(row[5]) if row[5] else [],
                        "type": row[6],
                        "collected_at": row[7],
                    }
                )

            conn.close()

            # Save to file
            export_path = export_dir / f"instagram_spots_{timestamp}.json"
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"export_date": datetime.now().isoformat(), "total_spots": len(spots), "spots": spots},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            self.logger.info(f"Exported {len(spots)} spots to {export_path}")
            return export_path

        else:
            raise ValueError(f"Unsupported export format: {format}")


def main():
    """Example usage"""
    pipeline = InstagramDataPipeline()

    # Example posts from Instagram
    instagram_posts = [
        {
            "post_id": "real_001",
            "location_name": "Cascade des Anglais",
            "caption": "Magnifique cascade cachée près de Vernet-les-Bains! #pyrenees #cascade #randonnee",
            "hashtags": ["pyrenees", "cascade", "randonnee", "occitanie"],
            "source": "instagram",
        },
        {
            "post_id": "real_002",
            "location_name": "Cirque de Gavarnie",
            "caption": "Le grand site des Pyrénées! Randonnée inoubliable #gavarnie #unesco",
            "hashtags": ["gavarnie", "unesco", "pyrenees", "hiking"],
            "source": "instagram",
        },
        {
            "post_id": "spam_001",
            "location_name": "CLICK HERE!!!",
            "caption": "DM for collab! Link in bio!",
            "hashtags": ["spam"],
            "source": "instagram",
        },
    ]

    # Process batch
    results = pipeline.process_batch(instagram_posts)

    logger.info("\n=== Pipeline Results ===")
    logger.info(f"Processed: {results['processed']}")
    logger.info(f"Stored: {results['stored']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Locations: {', '.join(results['locations'])}")

    # Export data
    if results["stored"] > 0:
        export_path = pipeline.export_data("json")
        logger.info(f"\nData exported to: {export_path}")


if __name__ == "__main__":
    main()
