#!/usr/bin/env python3
"""
Real Instagram scraper that fetches actual data from Instagram
Uses instagrapi with authentication to get real posts from locations and hashtags
NO MOCK DATA - REAL DATA ONLY
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from src.backend.core.logging_config import logger

from .base_scraper import BaseScraper
from .geocoding_france import OccitanieGeocoder

# Import instagrapi
try:
    from instagrapi import Client
    from instagrapi.exceptions import ClientError, ClientNotFoundError, MediaNotFound, PrivateError, LoginRequired

    HAS_INSTAGRAPI = True
except ImportError:
    HAS_INSTAGRAPI = False
    logger.info("WARNING: instagrapi not installed. Install with: pip install instagrapi")


class RealInstagramScraper(BaseScraper, OccitanieGeocoder):
    """Real Instagram scraper that fetches actual data"""

    # Occitanie-focused hashtags (no simulation, real data only)
    HASHTAGS = {
        # High relevance Occitanie (0.8-1.0)
        "occitaniesecrete": 0.95,
        "spotsecretoccitanie": 0.95,
        "toulousesecret": 0.9,
        "montpelliersecret": 0.9,
        "pyrenéescachées": 0.9,
        "gorgesdutarn": 0.85,
        "cascadecachée": 0.9,
        "baignadesauvage": 0.85,
        "randonnéeoccitanie": 0.8,
        # Department specific (0.7-0.9)
        "ariege_pyrenees": 0.8,
        "aveyron_emotion": 0.8,
        "gard_tourisme": 0.7,
        "hautegaronnetourisme": 0.75,
        "gers_tourisme": 0.7,
        "herault_tourisme": 0.7,
        "lot_tourisme": 0.7,
        "lozere_tourisme": 0.7,
        "hautespyrenees": 0.8,
        "pyreneescatalanes": 0.8,
        "tarntourisme": 0.7,
        "tarnetgaronne": 0.7,
    }

    # Location IDs for Occitanie landmarks (to be discovered and cached)
    LOCATION_CACHE_FILE = "instagram_locations_cache.json"

    def __init__(self, username: str, password: str, session_file: Optional[str] = None):
        """
        Initialize real Instagram scraper

        Args:
            username: Instagram username
            password: Instagram password
            session_file: Optional path to save/load session
        """
        if not HAS_INSTAGRAPI:
            raise ImportError("instagrapi is required. Install with: pip install instagrapi")

        BaseScraper.__init__(self, "instagram")
        OccitanieGeocoder.__init__(self)

        self.username = username
        self.password = password
        self.session_file = session_file or "instagram_session.json"
        self.client = None
        self.location_cache = self._load_location_cache()

        # Setup client
        self._setup_client()

    def _setup_client(self):
        """Setup authenticated Instagram client"""
        self.client = Client()

        # Try to load existing session
        session_path = Path(self.session_file)
        if session_path.exists():
            try:
                self.client.load_settings(session_path)
                self.client.login(self.username, self.password)
                self.logger.info("Logged in using existing session")
                return
            except Exception as e:
                self.logger.warning(f"Failed to use existing session: {e}")

        # Fresh login
        try:
            self.client.login(self.username, self.password)
            # Save session for future use
            self.client.dump_settings(session_path)
            self.logger.info("Successfully logged in to Instagram")
        except Exception as e:
            self.logger.error(f"Failed to login to Instagram: {e}")
            raise

    def _load_location_cache(self) -> Dict:
        """Load cached Instagram location IDs"""
        cache_path = Path(self.LOCATION_CACHE_FILE)
        if cache_path.exists():
            with open(cache_path, "r") as f:
                return json.load(f)
        return {}

    def _save_location_cache(self):
        """Save location cache to file"""
        with open(self.LOCATION_CACHE_FILE, "w") as f:
            json.dump(self.location_cache, f, indent=2)

    def scrape(self, limit: int = 50, method: str = "location") -> List[Dict]:
        """
        Main scraping method - fetches REAL Instagram data

        Args:
            limit: Maximum number of posts to fetch
            method: "location" or "hashtag" based scraping

        Returns:
            List of real Instagram spots
        """
        if method == "location":
            return self._scrape_by_location(limit)
        else:
            return self._scrape_by_hashtag(limit)

    def _scrape_by_location(self, limit: int) -> List[Dict]:
        """Scrape real posts from Occitanie locations"""
        self.logger.info("Scraping real Instagram posts by location")
        spots = []

        # Popular Occitanie locations to search
        location_searches = [
            "Lac de Salagou",
            "Gorges du Tarn",
            "Pic du Midi",
            "Pont du Gard",
            "Carcassonne",
            "Cirque de Gavarnie",
            "Gorges de l'Hérault",
            "Lac de Naussac",
            "Cascade d'Ars",
            "Gouffre de Padirac",
        ]

        for location_name in location_searches:
            if len(spots) >= limit:
                break

            try:
                # Search for location
                if location_name not in self.location_cache:
                    self.logger.info(f"Searching for location: {location_name}")
                    locations = self.client.search_locations(location_name, amount=1)

                    if locations:
                        location = locations[0]
                        self.location_cache[location_name] = {
                            "pk": location.pk,
                            "name": location.name,
                            "lat": location.lat,
                            "lng": location.lng,
                        }
                        self._save_location_cache()
                    else:
                        self.logger.warning(f"Location not found: {location_name}")
                        continue
                else:
                    location = self.location_cache[location_name]

                # Get recent posts from this location
                self.logger.info(f"Fetching posts from {location_name}")
                location_medias = self.client.location_medias_recent(
                    location_id=location["pk"] if isinstance(location, dict) else location.pk, amount=10
                )

                # Process each media
                for media in location_medias:
                    if len(spots) >= limit:
                        break

                    spot = self._process_real_media(media, location_name)
                    if spot:
                        # Enhance with French geocoding
                        spot = self.enhance_spot_with_geocoding(spot)

                        # Only keep if in Occitanie
                        if spot.get("department") in self.OCCITANIE_DEPARTMENTS:
                            spots.append(spot)
                            self.logger.info(f"Found real spot: {spot.get('name')} in {spot.get('department')}")

                    self.rate_limit()

            except Exception as e:
                self.logger.error(f"Error scraping location {location_name}: {e}")

        return spots

    def _scrape_by_hashtag(self, limit: int) -> List[Dict]:
        """Scrape real posts from hashtags"""
        self.logger.info("Scraping real Instagram posts by hashtag")
        spots = []

        for hashtag, weight in sorted(self.HASHTAGS.items(), key=lambda x: x[1], reverse=True):
            if len(spots) >= limit:
                break

            try:
                self.logger.info(f"Fetching posts for #{hashtag}")

                # Get recent media for hashtag
                medias = self.client.hashtag_medias_recent(hashtag, amount=20)

                for media in medias:
                    if len(spots) >= limit:
                        break

                    # Only process if it's a secret/hidden spot
                    if not self._is_secret_spot(media.caption_text):
                        continue

                    spot = self._process_real_media(media, hashtag=hashtag, weight=weight)
                    if spot:
                        # Enhance with French geocoding
                        spot = self.enhance_spot_with_geocoding(spot)

                        # Only keep if in Occitanie
                        if (
                            spot.get("latitude")
                            and spot.get("longitude")
                            and self.is_in_occitanie(spot["latitude"], spot["longitude"])
                        ):
                            spots.append(spot)
                            self.logger.info(f"Found real spot via #{hashtag}: {spot.get('name')}")

                    self.rate_limit()

            except Exception as e:
                self.logger.error(f"Error scraping hashtag #{hashtag}: {e}")

        return spots

    def _process_real_media(
        self, media, location_name: str = None, hashtag: str = None, weight: float = 0.5
    ) -> Optional[Dict]:
        """Process real Instagram media object"""
        try:
            # Extract basic info
            caption = media.caption_text or ""

            # Get location info
            lat, lng = None, None
            location_str = location_name

            if media.location:
                lat = media.location.lat
                lng = media.location.lng
                location_str = media.location.name

            # Try to extract location from caption if not available
            if not location_str:
                location_str = self._extract_location_from_caption(caption)

            # Extract spot name
            spot_name = self._extract_spot_name(caption, location_str)

            # Build spot data from REAL Instagram post
            spot_data = {
                "source": f"instagram:#{hashtag}" if hashtag else f"instagram:@{media.user.username}",
                "source_url": f"https://instagram.com/p/{media.code}",
                "raw_text": caption,
                "name": spot_name,
                "latitude": lat,
                "longitude": lng,
                "address_hint": location_str,
                "type": self._guess_spot_type(caption),
                "activities": self._extract_activities(caption),
                "is_hidden": 1 if weight > 0.7 else 0,
                "metadata": {
                    "instagram_id": media.id,
                    "instagram_pk": media.pk,
                    "user": media.user.username,
                    "user_id": media.user.pk,
                    "hashtag": hashtag,
                    "relevance_score": weight,
                    "likes": media.like_count,
                    "comments": media.comment_count,
                    "created_at": media.taken_at.isoformat() if media.taken_at else None,
                    "media_type": media.media_type,  # 1=photo, 2=video, 8=album
                    "is_real_data": True,  # Mark as real data
                },
            }

            return spot_data

        except Exception as e:
            self.logger.error(f"Error processing media: {e}")
            return None

    def _is_secret_spot(self, caption: str) -> bool:
        """Check if post mentions a secret/hidden spot"""
        if not caption:
            return False

        secret_keywords = [
            "secret",
            "caché",
            "hidden",
            "peu connu",
            "méconnu",
            "confidentiel",
            "sauvage",
            "préservé",
            "spot secret",
            "coin secret",
            "endroit secret",
            "paradis caché",
        ]

        caption_lower = caption.lower()
        return any(keyword in caption_lower for keyword in secret_keywords)

    def _extract_location_from_caption(self, caption: str) -> Optional[str]:
        """Extract location hints from caption text"""
        import re

        # Look for location patterns
        patterns = [
            r"(?:à|près de|proche de|vers)\s+([A-Z][a-zÀ-ÿ\-\s]+)",
            r"📍\s*([A-Z][a-zÀ-ÿ\-\s]+)",
            r"(?:#)([A-Z][a-zÀ-ÿ]+)(?:\s|$)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, caption)
            if matches:
                return matches[0].strip()

        return None

    def _extract_spot_name(self, caption: str, location: str) -> str:
        """Extract spot name from caption"""
        import re

        # Look for specific spot mentions
        patterns = [
            r"(?:cascade|lac|grotte|gorge|gouffre|source|pont)\s+(?:de|du|des)\s+([A-Z][a-zÀ-ÿ\-\s]+)",
            r"([A-Z][a-zÀ-ÿ\-\s]+)\s+(?:cascade|lac|grotte|gorge|gouffre)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, caption, re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # Fallback to location
        return location or "Spot Instagram"

    def _guess_spot_type(self, caption: str) -> str:
        """Guess spot type from caption content"""
        caption_lower = caption.lower()

        type_keywords = {
            "cascade": ["cascade", "chute", "waterfall", "saut"],
            "lac": ["lac", "étang", "plan d'eau", "barrage"],
            "grotte": ["grotte", "gouffre", "aven", "caverne", "cave"],
            "gorge": ["gorge", "canyon", "défilé", "ravin"],
            "source": ["source", "résurgence", "fontaine", "spring"],
            "riviere": ["rivière", "fleuve", "ruisseau", "torrent"],
            "point_de_vue": ["panorama", "belvédère", "vue", "viewpoint", "sommet"],
        }

        for spot_type, keywords in type_keywords.items():
            if any(kw in caption_lower for kw in keywords):
                return spot_type

        return "nature_spot"

    def _extract_activities(self, caption: str) -> List[str]:
        """Extract activities from caption"""
        caption_lower = caption.lower()
        activities = []

        activity_keywords = {
            "baignade": ["baignade", "nager", "swimming", "plongeon", "bain"],
            "randonnée": ["randonnée", "rando", "marche", "hiking", "trek", "balade"],
            "escalade": ["escalade", "grimpe", "climbing", "varappe"],
            "spéléologie": ["spéléo", "spéléologie", "exploration souterraine"],
            "canyoning": ["canyoning", "canyon", "descente"],
            "kayak": ["kayak", "canoë", "paddle", "rafting"],
            "vtt": ["vtt", "vélo", "bike", "cycling"],
            "pêche": ["pêche", "fishing", "pêcher"],
            "photographie": ["photo", "photography", "shooting", "photographe"],
        }

        for activity, keywords in activity_keywords.items():
            if any(kw in caption_lower for kw in keywords):
                activities.append(activity)

        return activities[:4]  # Max 4 activities

    def search_location_by_name(self, location_name: str) -> Optional[Dict]:
        """Search for a specific location on Instagram"""
        try:
            locations = self.client.search_locations(location_name, amount=5)
            results = []

            for loc in locations:
                results.append(
                    {
                        "pk": loc.pk,
                        "name": loc.name,
                        "lat": loc.lat,
                        "lng": loc.lng,
                        "address": loc.address,
                        "city": loc.city,
                    }
                )

            return results

        except Exception as e:
            self.logger.error(f"Error searching location {location_name}: {e}")
            return None

    def get_user_posts(self, username: str, limit: int = 10) -> List[Dict]:
        """Get posts from a specific user (for outdoor/travel accounts)"""
        try:
            user = self.client.user_info_by_username(username)
            medias = self.client.user_medias(user.pk, amount=limit)

            spots = []
            for media in medias:
                # Only process outdoor/nature posts
                if self._is_outdoor_post(media.caption_text):
                    spot = self._process_real_media(media)
                    if spot:
                        spots.append(spot)

            return spots

        except Exception as e:
            self.logger.error(f"Error getting posts from @{username}: {e}")
            return []

    def _is_outdoor_post(self, caption: str) -> bool:
        """Check if post is about outdoor/nature spots"""
        if not caption:
            return False

        outdoor_keywords = [
            "nature",
            "outdoor",
            "randonnée",
            "hiking",
            "cascade",
            "lac",
            "montagne",
            "mountain",
            "gorge",
            "canyon",
            "grotte",
            "cave",
            "baignade",
            "swimming",
            "spot",
            "secret",
            "sauvage",
            "wild",
        ]

        caption_lower = caption.lower()
        return any(keyword in caption_lower for keyword in outdoor_keywords)


def main():
    """Example usage of real Instagram scraper"""
    import argparse

    parser = argparse.ArgumentParser(description="Real Instagram Scraper")
    parser.add_argument("--username", required=True, help="Instagram username")
    parser.add_argument("--password", required=True, help="Instagram password")
    parser.add_argument("--method", choices=["location", "hashtag"], default="location", help="Scraping method")
    parser.add_argument("--limit", type=int, default=50, help="Number of posts to scrape")
    parser.add_argument("--session", default="instagram_session.json", help="Session file path")

    args = parser.parse_args()

    # Create scraper
    scraper = RealInstagramScraper(username=args.username, password=args.password, session_file=args.session)

    # Scrape real data
    logger.info(f"Scraping real Instagram data using {args.method} method...")
    spots = scraper.scrape(limit=args.limit, method=args.method)

    logger.info(f"\nFound {len(spots)} real Instagram spots:")
    for spot in spots:
        logger.info(f"- {spot['name']} ({spot.get('type', 'unknown')})")
        logger.info(f"  Source: {spot['source_url']}")
        logger.info(f"  Location: {spot.get('address_hint', 'Unknown')}")
        if spot.get("activities"):
            logger.info(f"  Activities: {', '.join(spot['activities'])}")
        logger.info()

    # Save spots to database
    for spot in spots:
        scraper.save_spot(spot)

    logger.info(f"\nSaved {len(spots)} real spots to database")


if __name__ == "__main__":
    main()
