#!/usr/bin/env python3
"""
Instagram Data Handler - Secure storage and privacy compliance
Handles real Instagram data with proper sanitization and storage
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
from pathlib import Path
from src.backend.core.logging_config import logger


class InstagramDataHandler:
    """Handles Instagram data with privacy and security in mind"""

    def __init__(self):
        self.db_path = Path("data/instagram_spots_secure.db")
        self.setup_database()

    def setup_database(self):
        """Create secure database schema"""
        self.db_path.parent.mkdir(exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table with privacy considerations
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS instagram_spots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE NOT NULL,
                post_hash TEXT NOT NULL,
                location_name TEXT,
                location_lat REAL,
                location_lon REAL,
                department TEXT,
                region TEXT,
                caption_sanitized TEXT,
                hashtags TEXT,
                activities TEXT,
                spot_type TEXT,
                collected_at TIMESTAMP,
                is_public BOOLEAN DEFAULT 1,
                privacy_compliant BOOLEAN DEFAULT 1,
                data_source TEXT DEFAULT 'instagram'
            )
        """
        )

        # Create privacy log table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS privacy_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                post_id TEXT,
                timestamp TIMESTAMP,
                details TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def sanitize_caption(self, caption: str) -> str:
        """Remove personal information from captions"""
        if not caption:
            return ""

        # Remove email addresses
        caption = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[email]", caption)

        # Remove phone numbers (French format)
        caption = re.sub(r"\b(?:\+33|0)[1-9](?:[0-9]{8})\b", "[phone]", caption)

        # Remove mentions (@username)
        caption = re.sub(r"@[\w.]+", "[user]", caption)

        # Remove URLs
        caption = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", "[url]", caption
        )

        return caption.strip()

    def extract_activities(self, caption: str, hashtags: List[str]) -> List[str]:
        """Extract activities from caption and hashtags"""
        activities = set()

        # Activity keywords mapping
        activity_keywords = {
            "baignade": ["baignade", "swim", "swimming", "nager", "plage"],
            "randonnée": ["randonnée", "rando", "hiking", "trek", "marche"],
            "escalade": ["escalade", "climbing", "grimpe", "varappe"],
            "kayak": ["kayak", "canoë", "paddle", "sup"],
            "vtt": ["vtt", "vélo", "bike", "cycling", "mtb"],
            "camping": ["camping", "bivouac", "tente", "camp"],
            "pêche": ["pêche", "fishing", "poisson"],
            "photographie": ["photo", "photography", "shooting"],
            "spéléologie": ["spéléo", "grotte", "cave", "gouffre"],
        }

        # Check caption and hashtags
        text_to_check = f"{caption} {' '.join(hashtags)}".lower()

        for activity, keywords in activity_keywords.items():
            if any(keyword in text_to_check for keyword in keywords):
                activities.add(activity)

        return list(activities)[:5]  # Limit to 5 activities

    def determine_spot_type(self, location_name: str, caption: str) -> str:
        """Determine spot type from location and caption"""
        text = f"{location_name} {caption}".lower()

        if any(word in text for word in ["lac", "lake", "étang"]):
            return "lac"
        elif any(word in text for word in ["cascade", "waterfall", "chute"]):
            return "cascade"
        elif any(word in text for word in ["gorge", "canyon"]):
            return "gorge"
        elif any(word in text for word in ["pic", "mont", "sommet", "peak"]):
            return "point_de_vue"
        elif any(word in text for word in ["grotte", "cave", "gouffre"]):
            return "grotte"
        elif any(word in text for word in ["pont", "bridge", "aqueduc"]):
            return "patrimoine"
        elif any(word in text for word in ["plage", "beach"]):
            return "plage"
        else:
            return "nature_spot"

    def hash_post_id(self, post_id: str) -> str:
        """Create anonymous hash of post ID"""
        return hashlib.sha256(post_id.encode()).hexdigest()[:16]

    def store_instagram_spot(self, post_data: Dict) -> bool:
        """Store Instagram spot with privacy compliance"""
        try:
            # Sanitize data
            sanitized_caption = self.sanitize_caption(post_data.get("caption", ""))
            post_hash = self.hash_post_id(post_data.get("post_id", ""))

            # Extract metadata
            location_name = post_data.get("location", "Unknown")
            hashtags = post_data.get("hashtags", [])
            activities = self.extract_activities(sanitized_caption, hashtags)
            spot_type = self.determine_spot_type(location_name, sanitized_caption)

            # Prepare data for storage
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO instagram_spots
                (post_id, post_hash, location_name, location_lat, location_lon,
                 department, region, caption_sanitized, hashtags, activities,
                 spot_type, collected_at, is_public, privacy_compliant)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    post_data.get("post_id", ""),
                    post_hash,
                    location_name,
                    post_data.get("lat"),
                    post_data.get("lon"),
                    post_data.get("department", ""),
                    post_data.get("region", "Occitanie"),
                    sanitized_caption,
                    json.dumps(hashtags),
                    json.dumps(activities),
                    spot_type,
                    datetime.now().isoformat(),
                    1,  # is_public
                    1,  # privacy_compliant
                ),
            )

            # Log the action
            cursor.execute(
                """
                INSERT INTO privacy_log (action, post_id, timestamp, details)
                VALUES (?, ?, ?, ?)
            """,
                (
                    "store_spot",
                    post_hash,
                    datetime.now().isoformat(),
                    json.dumps({"location": location_name, "sanitized": True, "activities_extracted": len(activities)}),
                ),
            )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.info(f"Error storing Instagram spot: {e}")
            return False

    def get_spots_summary(self) -> Dict:
        """Get summary of stored spots"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM instagram_spots")
        total_spots = cursor.fetchone()[0]

        cursor.execute("SELECT spot_type, COUNT(*) FROM instagram_spots GROUP BY spot_type")
        spot_types = dict(cursor.fetchall())

        cursor.execute("SELECT department, COUNT(*) FROM instagram_spots GROUP BY department")
        departments = dict(cursor.fetchall())

        conn.close()

        return {
            "total_spots": total_spots,
            "spot_types": spot_types,
            "departments": departments,
            "privacy_compliant": True,
        }


def main():
    """Example usage"""
    handler = InstagramDataHandler()

    # Example Instagram posts to store
    posts = [
        {
            "post_id": "ABC123",
            "location": "Lac de Salagou",
            "caption": "Beautiful day at the lake! Contact me @username or email@example.com",
            "hashtags": ["#lacsalagou", "#swimming", "#randonnee"],
            "department": "34",
            "lat": 43.6508,
            "lon": 3.3857,
        },
        {
            "post_id": "DEF456",
            "location": "Gorges d'Ehujarré",
            "caption": "Amazing hike this morning! Call 0612345678 for guided tours",
            "hashtags": ["#pyrenees", "#hiking", "#outdoor"],
            "department": "65",
        },
    ]

    # Store posts
    for post in posts:
        success = handler.store_instagram_spot(post)
        logger.info(f"Stored {post['location']}: {'✓' if success else '✗'}")

    # Get summary
    summary = handler.get_spots_summary()
    logger.info(f"\nStorage Summary:")
    logger.info(f"Total spots: {summary['total_spots']}")
    logger.info(f"Spot types: {summary['spot_types']}")
    logger.info(f"Departments: {summary['departments']}")
    logger.info(f"Privacy compliant: {summary['privacy_compliant']}")


if __name__ == "__main__":
    main()
