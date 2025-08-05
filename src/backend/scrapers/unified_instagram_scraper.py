"""
Unified Instagram Scraper - Consolidates all Instagram scraping functionality
Combines the best features from all previous implementations
"""

import os
import re
import time
import json
import random
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from abc import ABC, abstractmethod
import logging
from src.backend.core.logging_config import logger

from playwright.async_api import async_playwright
from pydantic import ValidationError

# Optional imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from src.backend.scrapers.base_scraper import BaseScraper
from src.backend.scrapers.geocoding_mixin import GeocodingMixin
from src.backend.validators.social_media_schemas import DataValidator
from src.backend.validators.real_data_validator import enforce_real_data


class ScrapingStrategy(ABC):
    """Abstract base class for scraping strategies"""

    @abstractmethod
    @enforce_real_data
    async def scrape(self, query: str, **kwargs) -> List[Dict]:
        pass


class PlaywrightStrategy(ScrapingStrategy):
    """Playwright-based scraping strategy (from instagram_playwright_scraper.py)"""

    def __init__(self, logger):
        self.logger = logger

    @enforce_real_data
    async def scrape(self, query: str, **kwargs) -> List[Dict]:
        async with async_playwright() as p:
            # Try to use system chromium if Playwright's version fails
            try:
                browser = await p.chromium.launch(headless=kwargs.get("headless", True))
            except Exception:
                browser = await p.chromium.launch(
                    headless=kwargs.get("headless", True),
                    executable_path="/usr/bin/chromium-browser"
                )
            page = await browser.new_page()

            try:
                # Implementation from PlaywrightInstagramScraper
                await page.goto(f"https://www.instagram.com/explore/tags/{query}/")
                await page.wait_for_selector(".v1Nh3", timeout=15000)

                posts = await page.query_selector_all(".v1Nh3 a")
                results = []

                for post in posts[: kwargs.get("limit", 10)]:
                    href = await post.get_attribute("href")
                    if href:
                        results.append({"url": f"https://www.instagram.com{href}", "source": "playwright"})

                return results

            finally:
                await browser.close()


class SeleniumStrategy(ScrapingStrategy):
    """Selenium-based scraping strategy (from instagram_real_scraper.py)"""

    def __init__(self, logger):
        self.logger = logger

    @enforce_real_data
    async def scrape(self, query: str, **kwargs) -> List[Dict]:
        # Convert to sync for Selenium
        return await asyncio.to_thread(self._scrape_sync, query, **kwargs)

    def _scrape_sync(self, query: str, **kwargs) -> List[Dict]:
        if not SELENIUM_AVAILABLE:
            self.logger.warning("Selenium not available, returning empty results")
            return []

        options = webdriver.ChromeOptions()
        if kwargs.get("headless", True):
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=options)
        try:
            driver.get(f"https://www.instagram.com/explore/locations/{query}/")
            time.sleep(3)

            posts = driver.find_elements(By.CSS_SELECTOR, "article a")
            results = []

            for post in posts[: kwargs.get("limit", 10)]:
                href = post.get_attribute("href")
                if href:
                    results.append({"url": href, "source": "selenium"})

            return results

        finally:
            driver.quit()


class APIStrategy(ScrapingStrategy):
    """API-based strategy (from instagram_alternative_scraper.py)"""

    def __init__(self, logger):
        self.logger = logger

    @enforce_real_data
    async def scrape(self, query: str, **kwargs) -> List[Dict]:
        # Simulated API approach - would use actual API in production
        self.logger.info("Using API strategy for Instagram data")
        # This would integrate with Instagram Graph API or similar
        return []


class UnifiedInstagramScraper(BaseScraper, GeocodingMixin):
    """
    Unified Instagram scraper that combines all strategies
    Automatically selects the best strategy based on requirements
    """

    def __init__(self, strategy: str = "auto", validate: bool = True, rate_limit: float = 2.0, **kwargs):
        """
        Initialize unified scraper

        Args:
            strategy: 'playwright', 'selenium', 'api', or 'auto'
            validate: Whether to validate scraped data
            rate_limit: Seconds between requests
        """
        BaseScraper.__init__(self, source_name="instagram")
        GeocodingMixin.__init__(self)
        self.strategy_name = strategy
        self.validate = validate
        self.rate_limit = rate_limit
        self.config = kwargs

        # Initialize strategies
        self.strategies = {
            "playwright": PlaywrightStrategy(self.logger),
            "selenium": SeleniumStrategy(self.logger),
            "api": APIStrategy(self.logger),
        }

    def _select_strategy(self) -> ScrapingStrategy:
        """Select best strategy based on current conditions"""
        if self.strategy_name != "auto":
            return self.strategies[self.strategy_name]

        # Auto-selection logic
        # Try Playwright first (fastest and most reliable)
        try:
            import playwright

            return self.strategies["playwright"]
        except ImportError:
            pass

        # Fallback to Selenium if available
        if SELENIUM_AVAILABLE:
            return self.strategies["selenium"]

        # Last resort: API
        return self.strategies["api"]

    @enforce_real_data
    async def scrape_location(self, location: str, limit: int = 20, **kwargs) -> List[Dict]:
        """
        Main scraping method - consolidates all scraping logic
        """
        self.logger.info(f"Scraping Instagram for location: {location}")

        # Rate limiting
        if hasattr(self, "_last_request_time"):
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)

        self._last_request_time = time.time()

        # Select and execute strategy
        strategy = self._select_strategy()
        self.logger.info(f"Using strategy: {strategy.__class__.__name__}")

        try:
            raw_results = await strategy.scrape(location, limit=limit, **self.config, **kwargs)

            # Process and validate results
            processed_results = []
            for item in raw_results:
                processed = await self._process_item(item)
                if processed:
                    if self.validate:
                        validated = self._validate_item(processed)
                        if validated:
                            processed_results.append(validated)
                    else:
                        processed_results.append(processed)

            return processed_results

        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return []

    async def _process_item(self, item: Dict) -> Optional[Dict]:
        """Process raw scraped item"""
        try:
            # Extract location if available
            location_text = item.get("location", "")
            if location_text:
                geocoded = self.geocode_address(location_text)
                if geocoded and "geometry" in geocoded:
                    item["latitude"] = geocoded["geometry"]["lat"]
                    item["longitude"] = geocoded["geometry"]["lng"]

            # Ensure required fields
            item["source"] = "instagram"
            item["scraped_at"] = datetime.now().isoformat()

            return item

        except Exception as e:
            self.logger.error(f"Error processing item: {e}")
            return None

    def _validate_item(self, item: Dict) -> Optional[Dict]:
        """Validate item against schema"""
        try:
            validator = DataValidator()
            if validator.validate_instagram_post(item):
                return item
            else:
                self.logger.warning("Instagram post validation failed")
                return None
        except Exception as e:
            self.logger.warning(f"Validation error: {e}")
            return None

    @enforce_real_data
    async def scrape(self, query: str, location_type: str = "hashtag", **kwargs) -> List[Dict]:
        """
        Main public scraping interface
        Maintains compatibility with existing code
        """
        return await self.scrape_location(query, **kwargs)

    def scrape_sync(self, query: str, **kwargs) -> List[Dict]:
        """Synchronous wrapper for compatibility"""
        return asyncio.run(self.scrape(query, **kwargs))


# Backwards compatibility aliases
InstagramScraper = UnifiedInstagramScraper
RealInstagramScraper = UnifiedInstagramScraper
PlaywrightInstagramScraper = UnifiedInstagramScraper


if __name__ == "__main__":
    # Test the unified scraper
    async def test():
        scraper = UnifiedInstagramScraper(strategy="auto")
        results = await scraper.scrape("toulouse", limit=5)
        logger.info(f"Found {len(results)} results")
        for r in results:
            logger.info(f"- {r.get('url', 'N/A')}")

    asyncio.run(test())
