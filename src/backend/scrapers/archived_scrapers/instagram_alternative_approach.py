#!/usr/bin/env python3
"""Alternative Instagram approach - using user timelines instead of hashtags"""

from instagrapi import Client
import json
from pathlib import Path
from datetime import datetime
from src.backend.core.logging_config import logger


def test_alternative_methods():
    """Test different Instagram data access methods"""
    cl = Client()

    # Load session
    session_file = Path("instagrapi_session.json")
    if session_file.exists():
        cl.load_settings(session_file)
        logger.info("✅ Session loaded\n")
    else:
        logger.info("❌ No session found")
        return

    logger.info("🔍 Testing Alternative Instagram Access Methods\n")

    # Method 1: Search users interested in outdoor activities
    logger.info("1️⃣ Searching for outdoor-related users...")
    try:
        outdoor_keywords = ["randonnee", "montagne", "outdoor"]
        users_found = []

        for keyword in outdoor_keywords:
            try:
                users = cl.search_users(keyword, amount=5)
                logger.info(f"   Found {len(users)} users for '{keyword}'")
                for user in users[:3]:
                    logger.info(f"      - @{user.username}")
                    users_found.append(user.username)
            except Exception as e:
                logger.info(f"   Error searching '{keyword}': {e}")

    except Exception as e:
        logger.info(f"   ❌ User search failed: {e}")

    # Method 2: Get location info directly
    logger.info("\n2️⃣ Testing location search...")
    try:
        # Search for locations in France
        locations = ["Chamonix", "Annecy", "Pyrenees"]

        for loc in locations:
            try:
                places = cl.search_locations(loc, amount=3)
                logger.info(f"   Found {len(places)} places for '{loc}'")
                for place in places:
                    logger.info(f"      - {place.name} ({place.lat}, {place.lng})")
            except Exception as e:
                logger.info(f"   Error searching '{loc}': {e}")

    except Exception as e:
        logger.info(f"   ❌ Location search failed: {e}")

    # Method 3: Get user's own feed (if following outdoor accounts)
    logger.info("\n3️⃣ Testing user timeline...")
    try:
        user_id = cl.user_id_from_username("fiac_lux")
        logger.info(f"   Your user ID: {user_id}")

        # Get your own recent posts
        medias = cl.user_medias(user_id, amount=5)
        logger.info(f"   Found {len(medias)} recent posts from your account")

    except Exception as e:
        logger.info(f"   ❌ Timeline access failed: {e}")

    # Method 4: Try getting posts by location ID
    logger.info("\n4️⃣ Testing posts by location...")
    try:
        # Try a known location ID (this would need to be discovered first)
        # Example: Search for posts at specific locations
        test_location = "Lac d'Annecy"
        locations = cl.search_locations(test_location, amount=1)

        if locations:
            location = locations[0]
            logger.info(f"   Found location: {location.name}")
            logger.info(f"   Trying to get posts from this location...")

            # This might work better than hashtags
            try:
                location_medias = cl.location_medias_recent(location.pk, amount=5)
                logger.info(f"   ✅ Found {len(location_medias)} posts at {location.name}")
            except Exception as e:
                logger.info("   ❌ Could not get posts from location")

    except Exception as e:
        logger.info(f"   ❌ Location posts failed: {e}")

    logger.info("\n📋 Summary:")
    logger.info("The Instagrapi library has issues with hashtag posts due to Instagram format changes.")
    logger.info("Alternative approaches that might work:")
    logger.info("1. Search and analyze specific outdoor user accounts")
    logger.info("2. Search by location instead of hashtags")
    logger.info("3. Use web scraping with Selenium as fallback")


if __name__ == "__main__":
    test_alternative_methods()
