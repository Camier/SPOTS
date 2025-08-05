#!/usr/bin/env python3
"""
Real Instagram scraper using Playwright browser automation
Fetches ACTUAL Instagram data - NO MOCK DATA
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from src.backend.core.logging_config import logger

from playwright.sync_api import sync_playwright, Page, Browser
from .base_scraper import BaseScraper
from .geocoding_france import OccitanieGeocoder


class PlaywrightInstagramScraper(BaseScraper, OccitanieGeocoder):
    """Real Instagram scraper using Playwright for browser automation"""

    # Occitanie locations to search
    OCCITANIE_LOCATIONS = [
        "Lac de Salagou",
        "Gorges du Tarn",
        "Pic du Midi",
        "Pont du Gard",
        "Carcassonne",
        "Cirque de Gavarnie",
        "Gorges de l'Hérault",
        "Cascade d'Ars",
        "Gouffre de Padirac",
        "Lac de Naussac",
        "Cascade de Sautadet",
        "Grotte de Niaux",
    ]

    # Occitanie hashtags
    HASHTAGS = [
        "occitaniesecrete",
        "toulousesecret",
        "montpelliersecret",
        "pyrenéescachées",
        "gorgesdutarn",
        "cascadecachée",
        "baignadesauvage",
        "randonnéeoccitanie",
        "spotsecretoccitanie",
    ]

    def __init__(self, username: str, password: str, headless: bool = False):
        """Initialize Playwright Instagram scraper"""
        BaseScraper.__init__(self, "instagram")
        OccitanieGeocoder.__init__(self)

        self.username = username
        self.password = password
        self.headless = headless
        self.browser = None
        self.page = None
        self.logged_in = False

    def setup_browser(self) -> Tuple[Browser, Page]:
        """Setup Playwright browser"""
        self.logger.info("Setting up Playwright browser...")

        playwright = sync_playwright().start()

        # Launch browser with realistic settings
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # Create context with realistic viewport and user agent
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="fr-FR",
            timezone_id="Europe/Paris",
        )

        # Add stealth settings
        context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        )

        page = context.new_page()

        # Set extra headers
        page.set_extra_http_headers(
            {
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            }
        )

        return browser, page

    def login(self) -> bool:
        """Login to Instagram using Playwright"""
        try:
            self.logger.info("Logging in to Instagram...")

            # Go to Instagram
            self.page.goto("https://www.instagram.com/", wait_until="networkidle")
            time.sleep(3)

            # Handle cookie banner if present
            try:
                cookie_button = self.page.locator('button:has-text("Autoriser les cookies essentiels")')
                if cookie_button.is_visible():
                    cookie_button.click()
                    time.sleep(1)
            except (requests.RequestException, ConnectionError) as e:
                pass

            # Check if already logged in
            if self.page.locator('svg[aria-label="Accueil"]').is_visible():
                self.logger.info("Already logged in!")
                self.logged_in = True
                return True

            # Fill login form
            self.logger.info("Filling login form...")

            # Enter username
            username_input = self.page.locator('input[name="username"]')
            username_input.fill(self.username)
            time.sleep(1)

            # Enter password
            password_input = self.page.locator('input[name="password"]')
            password_input.fill(self.password)
            time.sleep(1)

            # Click login button
            login_button = self.page.locator('button[type="submit"]')
            login_button.click()

            # Wait for navigation
            time.sleep(5)

            # Check for errors
            error_message = self.page.locator('div[role="alert"]')
            if error_message.is_visible():
                error_text = error_message.text_content()
                self.logger.error(f"Login error: {error_text}")
                return False

            # Handle "Save login info" popup
            try:
                not_now_button = self.page.locator('button:has-text("Plus tard")')
                if not_now_button.is_visible():
                    not_now_button.click()
                    time.sleep(1)
            except Exception as e:
                pass

            # Handle notifications popup
            try:
                not_now_button = self.page.locator('button:has-text("Plus tard")')
                if not_now_button.is_visible():
                    not_now_button.click()
                    time.sleep(1)
            except Exception as e:
                pass

            # Verify login success
            if self.page.locator('svg[aria-label="Accueil"]').is_visible():
                self.logger.info("Login successful!")
                self.logged_in = True

                # Save cookies for future sessions
                cookies = self.page.context.cookies()
                with open("instagram_cookies.json", "w") as f:
                    json.dump(cookies, f)

                return True
            else:
                self.logger.error("Login failed - could not verify home button")
                return False

        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False

    def search_location(self, location_name: str) -> Optional[str]:
        """Search for a location and return its URL"""
        try:
            self.logger.info(f"Searching for location: {location_name}")

            # Click search button
            search_button = self.page.locator('svg[aria-label="Rechercher"]').first
            search_button.click()
            time.sleep(2)

            # Enter search query
            search_input = self.page.locator('input[placeholder="Rechercher"]')
            search_input.fill(location_name)
            time.sleep(3)

            # Look for location results
            location_results = self.page.locator('a[href*="/explore/locations/"]')

            if location_results.count() > 0:
                # Click first location result
                first_location = location_results.first
                location_url = first_location.get_attribute("href")
                location_name = first_location.text_content()

                self.logger.info(f"Found location: {location_name}")

                # Navigate to location page
                first_location.click()
                time.sleep(3)

                return self.page.url
            else:
                self.logger.warning(f"No location found for: {location_name}")
                return None

        except Exception as e:
            self.logger.error(f"Error searching location: {e}")
            return None

    def scrape_location_posts(self, location_url: str, limit: int = 10) -> List[Dict]:
        """Scrape posts from a location page"""
        posts = []

        try:
            # Go to location page if not already there
            if self.page.url != location_url:
                self.page.goto(location_url, wait_until="networkidle")
                time.sleep(3)

            # Get location name from page
            location_name = self.page.locator("h1").text_content()
            self.logger.info(f"Scraping posts from: {location_name}")

            # Find all post links
            post_links = self.page.locator('article a[href*="/p/"]')
            post_count = min(post_links.count(), limit)

            self.logger.info(f"Found {post_links.count()} posts, scraping {post_count}")

            # Collect post URLs first
            post_urls = []
            for i in range(post_count):
                try:
                    url = post_links.nth(i).get_attribute("href")
                    if url and "/p/" in url:
                        full_url = f"https://www.instagram.com{url}" if not url.startswith("http") else url
                        post_urls.append(full_url)
                except (requests.RequestException, ConnectionError) as e:
                    continue

            # Scrape each post
            for i, post_url in enumerate(post_urls):
                self.logger.info(f"Scraping post {i+1}/{len(post_urls)}: {post_url}")

                post_data = self.scrape_single_post(post_url, location_name)
                if post_data:
                    posts.append(post_data)

                # Rate limiting
                time.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping location posts: {e}")

        return posts

    def scrape_single_post(self, post_url: str, location_name: str = None) -> Optional[Dict]:
        """Scrape data from a single Instagram post"""
        try:
            # Navigate to post
            self.page.goto(post_url, wait_until="networkidle")
            time.sleep(2)

            # Extract username
            username_elem = self.page.locator("article header a").first
            username = username_elem.text_content() if username_elem else "unknown"

            # Extract caption
            caption = ""
            try:
                # Look for caption in various possible locations
                caption_elem = self.page.locator("article h1").first
                if not caption_elem.is_visible():
                    caption_elem = self.page.locator("article span").filter(has_text=re.compile(r".{20,}"))

                if caption_elem.is_visible():
                    caption = caption_elem.text_content()
            except (AttributeError, KeyError, IndexError) as e:
                pass

            # Extract likes count
            likes = 0
            try:
                likes_elem = self.page.locator('section button:has-text("J\'aime")').first
                likes_text = likes_elem.text_content()
                # Extract number from text like "123 J'aime"
                likes_match = re.search(r"(\d+)", likes_text.replace(" ", ""))
                if likes_match:
                    likes = int(likes_match.group(1))
            except (AttributeError, KeyError, IndexError) as e:
                pass

            # Extract location if shown on post
            post_location = location_name
            try:
                location_elem = self.page.locator('article a[href*="/explore/locations/"]').first
                if location_elem.is_visible():
                    post_location = location_elem.text_content()
            except (AttributeError, KeyError, IndexError) as e:
                pass

            # Extract hashtags from caption
            hashtags = re.findall(r"#(\w+)", caption)

            # Determine if it's a hidden/secret spot
            is_hidden = self._is_secret_spot(caption)

            # Extract activities
            activities = self._extract_activities(caption)

            # Guess spot type
            spot_type = self._guess_spot_type(caption)

            # Build spot data
            spot_data = {
                "source": f"instagram:@{username}",
                "source_url": post_url,
                "raw_text": caption,
                "name": self._extract_spot_name(caption, post_location),
                "address_hint": post_location,
                "type": spot_type,
                "activities": activities,
                "is_hidden": 1 if is_hidden else 0,
                "metadata": {
                    "username": username,
                    "likes": likes,
                    "hashtags": hashtags,
                    "scraped_at": datetime.now().isoformat(),
                    "is_real_data": True,
                },
            }

            return spot_data

        except Exception as e:
            self.logger.error(f"Error scraping post {post_url}: {e}")
            return None

    def scrape_hashtag_posts(self, hashtag: str, limit: int = 10) -> List[Dict]:
        """Scrape posts from a hashtag page"""
        posts = []

        try:
            # Navigate to hashtag page
            hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            self.page.goto(hashtag_url, wait_until="networkidle")
            time.sleep(3)

            self.logger.info(f"Scraping posts from #{hashtag}")

            # Find post links
            post_links = self.page.locator('article a[href*="/p/"]')
            post_count = min(post_links.count(), limit)

            # Collect URLs
            post_urls = []
            for i in range(post_count):
                try:
                    url = post_links.nth(i).get_attribute("href")
                    if url and "/p/" in url:
                        full_url = f"https://www.instagram.com{url}" if not url.startswith("http") else url
                        post_urls.append(full_url)
                except (requests.RequestException, ConnectionError) as e:
                    continue

            # Scrape each post
            for i, post_url in enumerate(post_urls):
                self.logger.info(f"Scraping post {i+1}/{len(post_urls)} from #{hashtag}")

                post_data = self.scrape_single_post(post_url)
                if post_data:
                    post_data["metadata"]["hashtag_source"] = hashtag
                    posts.append(post_data)

                time.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping hashtag #{hashtag}: {e}")

        return posts

    def scrape(self, method: str = "location", limit: int = 50) -> List[Dict]:
        """Main scraping method"""
        if not self.browser:
            self.browser, self.page = self.setup_browser()

        if not self.logged_in:
            if not self.login():
                self.logger.error("Failed to login to Instagram")
                return []

        spots = []

        if method == "location":
            # Scrape by location
            for location in self.OCCITANIE_LOCATIONS:
                if len(spots) >= limit:
                    break

                location_url = self.search_location(location)
                if location_url:
                    location_posts = self.scrape_location_posts(location_url, limit=10)

                    # Process and filter posts
                    for post in location_posts:
                        # Enhance with geocoding
                        post = self.enhance_spot_with_geocoding(post)

                        # Only keep if in Occitanie
                        if post.get("department") in self.OCCITANIE_DEPARTMENTS:
                            spots.append(post)

                        if len(spots) >= limit:
                            break

        else:
            # Scrape by hashtag
            for hashtag in self.HASHTAGS:
                if len(spots) >= limit:
                    break

                hashtag_posts = self.scrape_hashtag_posts(hashtag, limit=10)

                for post in hashtag_posts:
                    # Enhance with geocoding
                    post = self.enhance_spot_with_geocoding(post)

                    # Only keep if in Occitanie or location unknown
                    if not post.get("latitude") or self.is_in_occitanie(
                        post.get("latitude", 0), post.get("longitude", 0)
                    ):
                        spots.append(post)

                    if len(spots) >= limit:
                        break

        return spots

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

        return activities[:4]

    def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Instagram Playwright Scraper")
    parser.add_argument("--username", required=True, help="Instagram username/email")
    parser.add_argument("--password", required=True, help="Instagram password")
    parser.add_argument("--method", choices=["location", "hashtag"], default="location", help="Scraping method")
    parser.add_argument("--limit", type=int, default=50, help="Number of posts to scrape")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")

    args = parser.parse_args()

    # Create scraper
    scraper = PlaywrightInstagramScraper(username=args.username, password=args.password, headless=args.headless)

    try:
        # Scrape data
        logger.info(f"Scraping Instagram using {args.method} method...")
        spots = scraper.scrape(method=args.method, limit=args.limit)

        logger.info(f"\nFound {len(spots)} real Instagram spots:")
        for spot in spots[:5]:
            logger.info(f"\n- {spot['name']}")
            logger.info(f"  Type: {spot.get('type', 'unknown')}")
            logger.info(f"  Location: {spot.get('address_hint', 'Unknown')}")
            logger.info(f"  Activities: {', '.join(spot.get('activities', []))}")
            logger.info(f"  URL: {spot['source_url']}")

        # Save spots to database
        for spot in spots:
            scraper.save_spot(spot)

        logger.info(f"\nSaved {len(spots)} spots to database")

    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()
