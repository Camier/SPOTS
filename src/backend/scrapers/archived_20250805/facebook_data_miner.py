#!/usr/bin/env python3
"""
Facebook Data Mining for Occitanie Outdoor Spots
Uses async patterns and focuses on publicly accessible data
"""

import asyncio
import aiohttp
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re
from dataclasses import dataclass, asdict
import logging
from urllib.parse import urlencode, urlparse
from src.backend.core.logging_config import logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FacebookSpot:
    """Data model for a Facebook-sourced outdoor spot"""

    name: str
    location_text: str
    coordinates: Optional[Dict[str, float]]
    description: str
    activities: List[str]
    source_type: str  # 'group', 'page', 'event'
    source_name: str
    post_date: str
    engagement: Dict[str, int]  # likes, comments, shares
    collected_at: str

    def to_dict(self) -> Dict:
        """Convert to dictionary with privacy sanitization"""
        data = asdict(self)
        # Remove any personal information
        data["description"] = self._sanitize_text(data["description"])
        return data

    def _sanitize_text(self, text: str) -> str:
        """Remove personal information from text"""
        # Remove email addresses
        text = re.sub(r"\S+@\S+", "[email]", text)
        # Remove phone numbers (French format)
        text = re.sub(r"(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}", "[phone]", text)
        # Remove URLs that might contain personal info
        text = re.sub(r"https?://\S+", "[url]", text)
        # Remove potential usernames
        text = re.sub(r"@\w+", "[user]", text)
        return text


class FacebookDataMiner:
    """Async Facebook data miner for outdoor spots"""

    def __init__(self):
        self.session = None
        self.rate_limit = asyncio.Semaphore(10)  # 10 concurrent requests
        self.spots_data = []

        # Occitanie-related keywords
        self.occitanie_keywords = [
            "occitanie",
            "toulouse",
            "montpellier",
            "perpignan",
            "nîmes",
            "carcassonne",
            "béziers",
            "narbonne",
            "albi",
            "tarbes",
            "pyrénées",
            "cévennes",
            "camargue",
            "languedoc",
            "roussillon",
        ]

        # Outdoor activity patterns (French)
        self.activity_patterns = {
            "randonnée": [r"\brand[oô]nn?[ée]e?\b", r"\bhiking\b", r"\bmarche\b"],
            "baignade": [r"\bbaignade\b", r"\bnage\b", r"\bswim", r"\bpiscine naturelle\b"],
            "escalade": [r"\bescalade\b", r"\bgrimpe\b", r"\bclimbing\b"],
            "vtt": [r"\bvtt\b", r"\bvélo\b", r"\bcycl"],
            "kayak": [r"\bkayak\b", r"\bcano[eë]\b", r"\bpaddle\b"],
            "camping": [r"\bcamping\b", r"\bbivouac\b", r"\bcampement\b"],
            "pêche": [r"\bpêche\b", r"\bpêcher\b", r"\bfishing\b"],
        }

        # Location extraction patterns
        self.location_patterns = [
            # Near/at patterns
            r"(?:près de |à |au |aux )?(?:la |le |les |l')?([A-ZÀ-Ÿ][a-zà-ÿ\-]+(?:\s+[A-ZÀ-Ÿ]?[a-zà-ÿ\-]+)*)",
            # Specific place types
            r"(Lac\s+(?:de\s+|d')?[A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(Mont\s+[A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(Pic\s+(?:de\s+|du\s+)?[A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(Gorges?\s+(?:de\s+|du\s+|des\s+)?[A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(Cascade\s+(?:de\s+|du\s+|des\s+)?[A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            r"(Col\s+(?:de\s+|du\s+)?[A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
        ]

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def extract_activities(self, text: str) -> List[str]:
        """Extract outdoor activities from text"""
        activities = []
        text_lower = text.lower()

        for activity, patterns in self.activity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    activities.append(activity)
                    break

        return list(set(activities))

    def extract_locations(self, text: str) -> List[str]:
        """Extract location names from text"""
        locations = []

        for pattern in self.location_patterns:
            matches = re.findall(pattern, text)
            locations.extend(matches)

        # Filter out common words and clean up
        filtered_locations = []
        for loc in locations:
            if isinstance(loc, tuple):
                loc = loc[0]
            loc = loc.strip()
            # Skip if too short or common words
            if len(loc) > 3 and loc.lower() not in ["dans", "avec", "pour", "vers"]:
                filtered_locations.append(loc)

        return list(set(filtered_locations))

    def is_occitanie_related(self, text: str) -> bool:
        """Check if text is related to Occitanie region"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.occitanie_keywords)

    async def search_public_pages(self, query: str) -> List[Dict]:
        """Search public Facebook pages (simulation for demo)"""
        # Note: In reality, this would use Facebook Graph API or web scraping
        # For now, we'll create a structure that shows how it would work

        logger.info(f"Searching Facebook pages for: {query}")

        # Simulated search results structure
        pages = [
            {"id": "page_1", "name": "Randonnées en Occitanie", "category": "Outdoor Recreation", "posts": []},
            {
                "id": "page_2",
                "name": "Lacs et Baignades Naturelles Occitanie",
                "category": "Travel & Tourism",
                "posts": [],
            },
        ]

        return pages

    async def get_page_posts(self, page_id: str, page_name: str) -> List[Dict]:
        """Get posts from a Facebook page"""
        async with self.rate_limit:
            # In reality, this would fetch from Facebook API
            # Simulated posts for demonstration

            sample_posts = [
                {
                    "id": f"{page_id}_post_1",
                    "message": "Magnifique journée au Lac de Salagou! 🏊‍♂️ Eau cristalline, parfait pour la baignade et randonnée autour du lac. #Occitanie #OutdoorLife",
                    "created_time": datetime.now().isoformat(),
                    "reactions": {"like": 156, "love": 42},
                    "comments": 23,
                    "shares": 8,
                },
                {
                    "id": f"{page_id}_post_2",
                    "message": "Découverte des Gorges d'Héric près de Mons-la-Trivalle. Cascade impressionnante et bassins naturels pour se baigner! Randonnée de 2h aller-retour.",
                    "created_time": datetime.now().isoformat(),
                    "reactions": {"like": 89, "love": 31},
                    "comments": 15,
                    "shares": 5,
                },
            ]

            return sample_posts

    async def process_post(self, post: Dict, source_name: str, source_type: str) -> Optional[FacebookSpot]:
        """Process a single post to extract spot information"""
        message = post.get("message", "")

        # Skip if not Occitanie related
        if not self.is_occitanie_related(message):
            return None

        # Extract locations
        locations = self.extract_locations(message)
        if not locations:
            return None

        # Extract activities
        activities = self.extract_activities(message)

        # Calculate engagement
        reactions = post.get("reactions", {})
        engagement = {
            "likes": sum(reactions.values()) if isinstance(reactions, dict) else 0,
            "comments": post.get("comments", 0),
            "shares": post.get("shares", 0),
        }

        # Create spot object
        spot = FacebookSpot(
            name=locations[0] if locations else "Unknown",
            location_text=" ".join(locations),
            coordinates=None,  # Would be geocoded later
            description=message,
            activities=activities,
            source_type=source_type,
            source_name=source_name,
            post_date=post.get("created_time", ""),
            engagement=engagement,
            collected_at=datetime.now().isoformat(),
        )

        return spot

    async def mine_facebook_data(self, search_queries: List[str]) -> pd.DataFrame:
        """Main mining function"""
        logger.info(f"Starting Facebook data mining with {len(search_queries)} queries")

        all_spots = []

        for query in search_queries:
            # Search for pages
            pages = await self.search_public_pages(query)

            # Process each page
            for page in pages:
                posts = await self.get_page_posts(page["id"], page["name"])

                # Process posts concurrently
                tasks = [self.process_post(post, page["name"], "page") for post in posts]

                spots = await asyncio.gather(*tasks)
                all_spots.extend([s for s in spots if s is not None])

        # Convert to DataFrame
        if all_spots:
            df = pd.DataFrame([spot.to_dict() for spot in all_spots])
            logger.info(f"Collected {len(df)} spots from Facebook")
            return df
        else:
            logger.warning("No spots found")
            return pd.DataFrame()

    def analyze_engagement(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze engagement metrics"""
        if df.empty:
            return {}

        # Calculate engagement scores
        df["total_engagement"] = df["engagement"].apply(
            lambda x: x.get("likes", 0) + x.get("comments", 0) * 2 + x.get("shares", 0) * 3
        )

        # Top spots by engagement
        top_spots = df.nlargest(5, "total_engagement")[["name", "total_engagement", "activities"]]

        # Activity popularity
        all_activities = []
        for activities in df["activities"]:
            all_activities.extend(activities)

        activity_counts = pd.Series(all_activities).value_counts()

        return {
            "total_spots": len(df),
            "avg_engagement": df["total_engagement"].mean(),
            "top_spots": top_spots.to_dict("records"),
            "popular_activities": activity_counts.to_dict(),
        }


async def main():
    """Demo Facebook data mining"""
    # Search queries for Occitanie outdoor spots
    search_queries = [
        "randonnée Occitanie",
        "baignade naturelle Languedoc",
        "lacs Pyrénées",
        "escalade Cévennes",
        "camping sauvage Occitanie",
    ]

    async with FacebookDataMiner() as miner:
        # Mine data
        df = await miner.mine_facebook_data(search_queries)

        if not df.empty:
            # Save raw data
            output_file = f"exports/facebook_spots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Convert to export format
            export_data = {
                "export_date": datetime.now().isoformat(),
                "source": "Facebook",
                "total_spots": len(df),
                "spots": df.to_dict("records"),
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(df)} spots to {output_file}")

            # Analyze engagement
            analysis = miner.analyze_engagement(df)

            logger.info("\n📊 Facebook Mining Results:")
            logger.info("=" * 50)
            logger.info(f"Total spots found: {analysis['total_spots']}")
            logger.info(f"Average engagement: {analysis['avg_engagement']:.1f}")
            logger.info("\n🏆 Top Spots by Engagement:")
            for spot in analysis["top_spots"]:
                logger.info(f"  - {spot['name']}: {spot['total_engagement']} engagement")
            logger.info("\n🎯 Popular Activities:")
            for activity, count in analysis["popular_activities"].items():
                logger.info(f"  - {activity}: {count} mentions")


if __name__ == "__main__":
    asyncio.run(main())
