#!/usr/bin/env python3
"""
Facebook Browser-based Scraper using Puppeteer MCP
Real data collection from public Facebook pages and groups
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging
from dataclasses import dataclass, asdict
import subprocess
from src.backend.core.logging_config import logger
from src.backend.validators.real_data_validator import enforce_real_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FacebookOutdoorSpot:
    """Facebook outdoor spot with full metadata"""

    name: str
    location_text: str
    coordinates: Optional[Tuple[float, float]]
    description: str
    activities: List[str]
    source_url: str
    source_name: str
    source_type: str  # 'group', 'page', 'event'
    author: str  # Anonymized
    post_date: str
    images: List[str]
    engagement: Dict[str, int]
    comments_sample: List[str]
    collected_at: str

    def sanitize(self) -> Dict:
        """Remove personal information"""
        data = asdict(self)
        # Sanitize author
        data["author"] = "Anonymous" if data["author"] else "Unknown"
        # Sanitize description
        data["description"] = self._clean_personal_info(data["description"])
        # Sanitize comments
        data["comments_sample"] = [self._clean_personal_info(c) for c in data["comments_sample"]]
        # Remove full URLs from images for privacy
        data["images"] = [f"image_{i}.jpg" for i in range(len(data["images"]))]
        return data

    def _clean_personal_info(self, text: str) -> str:
        """Remove personal info from text"""
        if not text:
            return text
        # Emails
        text = re.sub(r"\S+@\S+\.\S+", "[email]", text)
        # Phone numbers (French)
        text = re.sub(r"(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}", "[phone]", text)
        # Facebook profile URLs
        text = re.sub(r"facebook\.com/[^\s]+", "[profile]", text)
        # Usernames
        text = re.sub(r"@[\w.]+", "[user]", text)
        return text


class FacebookPuppeteerScraper:
    """Browser-based Facebook scraper using Puppeteer MCP"""

    def __init__(self):
        self.spots = []
        self.session_active = False

        # French outdoor keywords
        self.outdoor_keywords = [
            "randonnée",
            "baignade",
            "lac",
            "cascade",
            "gorge",
            "montagne",
            "escalade",
            "vtt",
            "kayak",
            "canoë",
            "camping",
            "bivouac",
            "sentier",
            "GR",
            "voie verte",
            "piscine naturelle",
            "source",
            "grotte",
            "falaise",
            "col",
            "pic",
            "sommet",
            "crête",
        ]

        # Occitanie locations
        self.occitanie_patterns = [
            r"\b(?:Ariège|Aude|Aveyron|Gard|Haute-Garonne|Gers|Hérault|Lot|Lozère|Hautes-Pyrénées|Pyrénées-Orientales|Tarn|Tarn-et-Garonne)\b",
            r"\b(?:Toulouse|Montpellier|Nîmes|Perpignan|Béziers|Narbonne|Carcassonne|Albi|Tarbes|Rodez|Cahors|Mende|Foix)\b",
            r"\b(?:Pyrénées|Cévennes|Causses|Corbières|Minervois|Camargue|Lauragais)\b",
            r"\bOccitanie\b",
        ]

        # Activity detection patterns
        self.activity_patterns = {
            "randonnée": [r"randonn", r"marche", r"trek", r"hiking", r"balade"],
            "baignade": [r"baign", r"nage", r"swim", r"trempe", r"plonge"],
            "escalade": [r"escalad", r"grimp", r"climb", r"varap"],
            "vtt": [r"vtt", r"vélo", r"cycl", r"bike"],
            "kayak": [r"kayak", r"canoë", r"canoe", r"paddle", r"raft"],
            "camping": [r"camp", r"bivouac", r"tente"],
            "pêche": [r"pêch", r"fish", r"truite"],
            "spéléo": [r"spéléo", r"grotte", r"cave", r"gouffre"],
        }

    async def start_session(self):
        """Start Puppeteer browser session"""
        logger.info("Starting Puppeteer browser session...")

        # Navigate to Facebook
        cmd = [
            "claude",
            "mcp",
            "mcp__puppeteer__puppeteer_navigate",
            json.dumps({"url": "https://www.facebook.com", "headless": False}),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            self.session_active = True
            logger.info("Browser session started successfully")
            return True
        else:
            logger.error(f"Failed to start browser: {result.stderr}")
            return False

    async def search_facebook(self, query: str):
        """Search Facebook for outdoor content"""
        if not self.session_active:
            logger.error("No active browser session")
            return

        logger.info(f"Searching Facebook for: {query}")

        # Construct search URL
        search_url = f"https://www.facebook.com/search/posts/?q={query}"

        # Navigate to search
        cmd = ["claude", "mcp", "mcp__puppeteer__puppeteer_navigate", json.dumps({"url": search_url})]
        subprocess.run(cmd, capture_output=True, text=True)

        # Wait for results
        await asyncio.sleep(3)

        # Take screenshot for debugging
        screenshot_cmd = [
            "claude",
            "mcp",
            "mcp__puppeteer__puppeteer_screenshot",
            json.dumps({"name": f"facebook_search_{query}", "encoded": True}),
        ]
        subprocess.run(screenshot_cmd, capture_output=True, text=True)

    async def extract_posts(self) -> List[Dict]:
        """Extract posts from current page"""
        # Get page content
        cmd = [
            "claude",
            "mcp",
            "mcp__puppeteer__puppeteer_evaluate",
            json.dumps(
                {
                    "script": """
                // Extract Facebook posts
                const posts = [];
                const postElements = document.querySelectorAll('[role="article"]');
                
                postElements.forEach(post => {
                    try {
                        // Extract text content
                        const textElement = post.querySelector('[data-ad-preview="message"]') || 
                                          post.querySelector('[dir="auto"]');
                        const text = textElement ? textElement.innerText : '';
                        
                        // Extract author (anonymized)
                        const authorElement = post.querySelector('strong');
                        const author = authorElement ? 'User' : 'Unknown';
                        
                        // Extract engagement
                        const likeElement = post.querySelector('[aria-label*="Like"]');
                        const likes = likeElement ? parseInt(likeElement.innerText) || 0 : 0;
                        
                        // Extract images
                        const images = Array.from(post.querySelectorAll('img'))
                            .filter(img => img.src && !img.src.includes('emoji'))
                            .map(img => 'image_found');
                        
                        posts.push({
                            text: text,
                            author: author,
                            likes: likes,
                            hasImages: images.length > 0,
                            timestamp: new Date().toISOString()
                        });
                    } catch (e) {
                        console.error('Error extracting post:', e);
                    }
                });
                
                return posts;
                """
                }
            ),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            try:
                posts = json.loads(result.stdout)
                return posts
            except (json.JSONDecodeError, ValueError) as e:
                return []
        return []

    def is_occitanie_outdoor_post(self, text: str) -> bool:
        """Check if post is about outdoor activities in Occitanie"""
        if not text:
            return False

        text_lower = text.lower()

        # Check for outdoor keywords
        has_outdoor = any(keyword in text_lower for keyword in self.outdoor_keywords)

        # Check for Occitanie references
        has_occitanie = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.occitanie_patterns)

        return has_outdoor and has_occitanie

    def extract_location_names(self, text: str) -> List[str]:
        """Extract location names from text"""
        locations = []

        # Specific location patterns
        patterns = [
            r"(?:Lac|Étang)\s+(?:de\s+|d')?([A-ZÀ-Ÿ][a-zà-ÿ\-]+(?:\s+[A-ZÀ-Ÿ]?[a-zà-ÿ\-]+)*)",
            r"(?:Mont|Pic|Puy)\s+(?:de\s+|du\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(?:Gorges?|Canyon)\s+(?:de\s+|du\s+|des\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(?:Cascade|Chute)\s+(?:de\s+|du\s+|des\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(?:Col|Cirque)\s+(?:de\s+|du\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(?:Forêt|Bois)\s+(?:de\s+|du\s+|des\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            locations.extend(matches)

        # Also look for capitalized place names after prepositions
        prep_pattern = r"(?:à|au|aux|vers|près de|proche de)\s+(?:la\s+|le\s+|les\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+(?:\s+[A-ZÀ-Ÿ]?[a-zà-ÿ\-]+)*)"
        prep_matches = re.findall(prep_pattern, text)
        locations.extend(prep_matches)

        # Clean and deduplicate
        cleaned = []
        for loc in locations:
            loc = loc.strip()
            if len(loc) > 2 and loc not in cleaned:
                cleaned.append(loc)

        return cleaned

    def detect_activities(self, text: str) -> List[str]:
        """Detect outdoor activities mentioned in text"""
        detected = []
        text_lower = text.lower()

        for activity, patterns in self.activity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected.append(activity)
                    break

        return list(set(detected))

    def process_post(self, post: Dict, source_info: Dict) -> Optional[FacebookOutdoorSpot]:
        """Process a single post into a spot"""
        text = post.get("text", "")

        if not self.is_occitanie_outdoor_post(text):
            return None

        # Extract information
        locations = self.extract_location_names(text)
        if not locations:
            return None

        activities = self.detect_activities(text)

        # Create spot
        spot = FacebookOutdoorSpot(
            name=locations[0],
            location_text=" | ".join(locations),
            coordinates=None,  # Would be geocoded later
            description=text[:500],  # Limit description length
            activities=activities,
            source_url=source_info.get("url", ""),
            source_name=source_info.get("name", "Facebook"),
            source_type=source_info.get("type", "post"),
            author=post.get("author", "Unknown"),
            post_date=post.get("timestamp", datetime.now().isoformat()),
            images=["image"] if post.get("hasImages") else [],
            engagement={"likes": post.get("likes", 0)},
            comments_sample=[],  # Would extract if needed
            collected_at=datetime.now().isoformat(),
        )

        return spot

    async def mine_outdoor_groups(self, group_urls: List[str]):
        """Mine outdoor-related Facebook groups"""
        all_spots = []

        for group_url in group_urls:
            logger.info(f"Mining group: {group_url}")

            # Navigate to group
            cmd = ["claude", "mcp", "mcp__puppeteer__puppeteer_navigate", json.dumps({"url": group_url})]
            subprocess.run(cmd, capture_output=True, text=True)

            await asyncio.sleep(3)

            # Scroll to load more posts
            for _ in range(3):
                scroll_cmd = [
                    "claude",
                    "mcp",
                    "mcp__puppeteer__puppeteer_evaluate",
                    json.dumps({"script": "window.scrollBy(0, 1000);"}),
                ]
                subprocess.run(scroll_cmd, capture_output=True, text=True)
                await asyncio.sleep(2)

            # Extract posts
            posts = await self.extract_posts()

            # Process posts
            source_info = {"url": group_url, "name": group_url.split("/")[-1], "type": "group"}

            for post in posts:
                spot = self.process_post(post, source_info)
                if spot:
                    all_spots.append(spot)

        self.spots.extend(all_spots)
        logger.info(f"Found {len(all_spots)} spots from groups")

    def export_spots(self, filename: str):
        """Export collected spots to JSON"""
        export_data = {
            "export_date": datetime.now().isoformat(),
            "source": "Facebook",
            "total_spots": len(self.spots),
            "spots": [spot.sanitize() for spot in self.spots],
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(self.spots)} spots to {filename}")

    def analyze_spots(self) -> pd.DataFrame:
        """Analyze collected spots"""
        if not self.spots:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame([spot.sanitize() for spot in self.spots])

        # Add analysis columns
        df["activity_count"] = df["activities"].apply(len)
        df["location_count"] = df["location_text"].apply(lambda x: len(x.split(" | ")))
        df["engagement_score"] = df["engagement"].apply(lambda x: x.get("likes", 0))

        return df


async def main():
    """Demo Facebook mining for Occitanie outdoor spots"""
    scraper = FacebookPuppeteerScraper()

    # Start browser session
    if not await scraper.start_session():
        logger.error("Failed to start browser session")
        return

    try:
        # Search queries
        queries = ["randonnée Occitanie 2025", "baignade lac Hérault", "camping sauvage Pyrénées"]

        # Search for content
        for query in queries:
            await scraper.search_facebook(query)
            await asyncio.sleep(5)
            posts = await scraper.extract_posts()

            # Process posts
            for post in posts:
                source_info = {"name": f"Search: {query}", "type": "search", "url": ""}
                spot = scraper.process_post(post, source_info)
                if spot:
                    scraper.spots.append(spot)

        # Mine specific outdoor groups (if logged in)
        # group_urls = [
        #     "https://www.facebook.com/groups/randonneeoccitanie",
        #     "https://www.facebook.com/groups/outdooroccitanie"
        # ]
        # await scraper.mine_outdoor_groups(group_urls)

        # Export results
        if scraper.spots:
            output_file = f"exports/facebook_spots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            scraper.export_spots(output_file)

            # Analyze
            df = scraper.analyze_spots()
            logger.info("\n📊 Facebook Mining Summary:")
            logger.info("=" * 50)
            logger.info(f"Total spots found: {len(df)}")
            logger.info(f"\n🎯 Top activities:")
            all_activities = []
            for activities in df["activities"]:
                all_activities.extend(activities)
            activity_counts = pd.Series(all_activities).value_counts()
            for activity, count in activity_counts.head().items():
                logger.info(f"  - {activity}: {count}")

            logger.info(f"\n📍 Top locations:")
            for idx, row in df.nlargest(5, "engagement_score").iterrows():
                logger.info(f"  - {row['name']} ({row['engagement_score']} likes)")

    except Exception as e:
        logger.error(f"Error during mining: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
