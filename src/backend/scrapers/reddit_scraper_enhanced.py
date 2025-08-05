#!/usr/bin/env python3
"""Enhanced Reddit scraper with Ola Maps geocoding integration"""

import praw
import re
from typing import Dict, List, Optional
import logging
from datetime import datetime

from .base_scraper import BaseScraper
from .geocoding_mixin import GeocodingMixin
from .enhanced_coordinate_extractor import EnhancedCoordinateExtractor
from src.backend.validators.real_data_validator import enforce_real_data


class EnhancedRedditScraper(BaseScraper, GeocodingMixin):
    """Reddit scraper with geocoding capabilities"""

    def __init__(self, db_path: str = None):
        BaseScraper.__init__(self, "reddit", db_path)
        GeocodingMixin.__init__(self)

        # Initialize Reddit API
        self.reddit = None
        self.coord_extractor = EnhancedCoordinateExtractor()

        # Occitanie-specific subreddits
        self.subreddits = [
            "toulouse",
            "Toulouse",
            "montpellier",
            "Montpellier",
            "france",
            "randonnee",
            "campingfrance",
            "pyrénées",
        ]

        # Location keywords for Occitanie
        self.location_keywords = [
            "toulouse",
            "montpellier",
            "narbonne",
            "perpignan",
            "albi",
            "carcassonne",
            "tarbes",
            "nîmes",
            "béziers",
            "montauban",
            "ariège",
            "aveyron",
            "haute-garonne",
            "gers",
            "lot",
            "hautes-pyrénées",
            "tarn",
            "tarn-et-garonne",
            "pyrénées",
            "occitanie",
            "midi-pyrénées",
            "languedoc",
        ]

    def init_reddit(self):
        """Initialize Reddit API client"""
        try:
            # Try to load credentials from config
            from .config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET, user_agent=REDDIT_USER_AGENT
            )
            self.logger.info("Reddit API initialized successfully")
            return True

        except ImportError:
            self.logger.warning("Reddit credentials not found in config.py")
            # Use read-only mode
            self.reddit = praw.Reddit(
                client_id="YOUR_CLIENT_ID", client_secret="YOUR_SECRET", user_agent="OccitanieSpotsScraper/1.0"
            )
            return False

    def is_occitanie_related(self, text: str) -> bool:
        """Check if text is related to Occitanie region"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.location_keywords)

    def extract_location_info(self, text: str) -> Dict:
        """Extract location information from text"""
        location_info = {
            "raw_text": text,
            "coordinates": None,
            "location_names": [],
            "is_hidden": self.is_secret_spot(text),
        }

        # Try to extract coordinates
        coords = self.coord_extractor.extract_from_text(text)
        if coords:
            location_info["coordinates"] = coords

        # Extract location names
        for keyword in self.location_keywords:
            if keyword in text.lower():
                location_info["location_names"].append(keyword)

        # Look for specific patterns
        patterns = [
            r"près de ([A-Za-zÀ-ÿ\s-]+)",
            r"à ([A-Za-zÀ-ÿ\s-]+)",
            r"au ([A-Za-zÀ-ÿ\s-]+)",
            r"vers ([A-Za-zÀ-ÿ\s-]+)",
            r"direction ([A-Za-zÀ-ÿ\s-]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            location_info["location_names"].extend(matches)

        return location_info

    def process_submission(self, submission) -> Optional[Dict]:
        """Process a Reddit submission into spot data"""
        # Skip if not Occitanie related
        full_text = f"{submission.title} {submission.selftext}"
        if not self.is_occitanie_related(full_text):
            return None

        # Extract location info
        location_info = self.extract_location_info(full_text)

        # Build spot data
        spot_data = {
            "source": "reddit",
            "source_url": f"https://reddit.com{submission.permalink}",
            "name": submission.title[:200],
            "description": submission.selftext[:1000],
            "raw_text": full_text[:2000],
            "author": str(submission.author) if submission.author else "deleted",
            "subreddit": submission.subreddit.display_name,
            "score": submission.score,
            "num_comments": submission.num_comments,
            "created_at": datetime.fromtimestamp(submission.created_utc).isoformat(),
            "is_hidden": location_info["is_hidden"],
        }

        # Add coordinates if found
        if location_info["coordinates"]:
            spot_data["latitude"] = location_info["coordinates"][0]
            spot_data["longitude"] = location_info["coordinates"][1]

        # Try geocoding if we have location names but no coordinates
        elif location_info["location_names"]:
            location_text = " ".join(location_info["location_names"][:3])  # Use first 3 locations
            geocoded = self.geocode_address(location_text)
            if geocoded:
                spot_data["latitude"] = geocoded["latitude"]
                spot_data["longitude"] = geocoded["longitude"]
                spot_data["geocoding_confidence"] = geocoded["confidence"]
                spot_data["address"] = geocoded["formatted_address"]

        # Enhance with geocoding data
        spot_data = self.enhance_spot_with_geocoding(spot_data)

        # Only return if we have coordinates
        if spot_data.get("latitude") and spot_data.get("longitude"):
            return spot_data

        return None

    @enforce_real_data
    def scrape_subreddit(self, subreddit_name: str, limit: int = 100) -> List[Dict]:
        """Scrape posts from a specific subreddit"""
        spots = []

        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            # Search for outdoor/nature related posts
            search_terms = [
                "randonnée",
                "baignade",
                "cascade",
                "lac",
                "montagne",
                "spot",
                "endroit",
                "lieu",
                "visite",
                "nature",
            ]

            for term in search_terms:
                self.logger.info(f"Searching r/{subreddit_name} for '{term}'...")

                for submission in subreddit.search(term, limit=limit // len(search_terms)):
                    spot_data = self.process_submission(submission)
                    if spot_data:
                        spots.append(spot_data)
                        self.logger.info(f"Found spot: {spot_data['name']}")

                    self.rate_limit()

        except Exception as e:
            self.logger.error(f"Error scraping r/{subreddit_name}: {e}")

        return spots

    @enforce_real_data
    def scrape(self, limit: int = 100) -> List[Dict]:
        """Main scraping method"""
        if not self.init_reddit():
            self.logger.error("Failed to initialize Reddit API")
            return []

        all_spots = []

        for subreddit in self.subreddits:
            self.logger.info(f"Scraping r/{subreddit}...")
            spots = self.scrape_subreddit(subreddit, limit)
            all_spots.extend(spots)

        # Remove duplicates based on coordinates
        unique_spots = []
        seen_coords = set()

        for spot in all_spots:
            if spot.get("latitude") and spot.get("longitude"):
                coord_key = f"{spot['latitude']:.4f},{spot['longitude']:.4f}"
                if coord_key not in seen_coords:
                    seen_coords.add(coord_key)
                    unique_spots.append(spot)

        self.logger.info(f"Found {len(unique_spots)} unique spots from Reddit")
        return unique_spots

    def save_spot(self, spot_data: Dict) -> bool:
        """Save spot with enhanced data"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Check if spot already exists
            if spot_data.get("latitude") and spot_data.get("longitude"):
                cursor.execute(
                    """
                    SELECT id FROM spots 
                    WHERE ABS(latitude - ?) < 0.0001 
                    AND ABS(longitude - ?) < 0.0001
                """,
                    (spot_data["latitude"], spot_data["longitude"]),
                )

                if cursor.fetchone():
                    self.logger.debug(f"Spot already exists at {spot_data['latitude']}, {spot_data['longitude']}")
                    conn.close()
                    return False

            # Insert new spot with enhanced fields
            cursor.execute(
                """
                INSERT INTO spots (
                    name, description, type, latitude, longitude,
                    elevation, address, geocoding_confidence,
                    department, source, url, weather_sensitive,
                    confidence_score, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    spot_data.get("name", "Unknown"),
                    spot_data.get("description", ""),
                    "reddit_spot",
                    spot_data.get("latitude"),
                    spot_data.get("longitude"),
                    spot_data.get("elevation"),
                    spot_data.get("address"),
                    spot_data.get("geocoding_confidence", 0.5),
                    self.get_department_from_coords(spot_data.get("latitude", 0), spot_data.get("longitude", 0)),
                    "reddit",
                    spot_data.get("source_url"),
                    1 if spot_data.get("is_hidden") else 0,
                    spot_data.get("score", 0) / 100.0,  # Normalize Reddit score
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            conn.close()

            self.logger.info(f"Saved enhanced spot: {spot_data.get('name', 'Unknown')}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving spot: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    scraper = EnhancedRedditScraper()
    scraper.run(limit=50)
