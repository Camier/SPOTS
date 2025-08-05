#!/usr/bin/env python3
"""
Pandas-based Data Processor for Large-Scale Facebook Analysis
Handles data from <1GB to >100GB with appropriate scaling strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Iterator
import json
from pathlib import Path
import logging
from datetime import datetime
import re
import gc
from functools import partial
import multiprocessing as mp
from src.backend.core.logging_config import logger

# For large-scale processing
try:
    import dask.dataframe as dd

    DASK_AVAILABLE = True
except ImportError:
    DASK_AVAILABLE = False

try:
    from pyspark.sql import SparkSession

    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FacebookDataProcessor:
    """
    Scalable Facebook data processor with multiple processing backends
    """

    def __init__(self, backend: str = "auto"):
        """
        Initialize processor with specified backend

        Args:
            backend: 'pandas', 'dask', 'spark', or 'auto' (auto-selects based on data size)
        """
        self.backend = backend
        self.chunk_size = 10000  # For pandas chunking

        # Regex patterns for extraction
        self.location_patterns = [
            # Lakes and water bodies
            r"(?:Lac|Étang|Plan d'eau)\s+(?:de\s+|d')?([A-ZÀ-Ÿ][a-zà-ÿ\-]+(?:\s+[A-ZÀ-Ÿ]?[a-zà-ÿ\-]+)*)",
            # Mountains and peaks
            r"(?:Mont|Pic|Puy|Sommet)\s+(?:de\s+|du\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            # Gorges and valleys
            r"(?:Gorges?|Vallée|Canyon)\s+(?:de\s+|du\s+|des\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            # General locations after prepositions
            r"(?:à|au|aux|près de|proche de)\s+(?:la\s+|le\s+|les\s+)?([A-ZÀ-Ÿ][a-zà-ÿ\-]+(?:\s+[A-ZÀ-Ÿ]?[a-zà-ÿ\-]+){0,2})",
        ]

        # Activity keywords
        self.activity_keywords = {
            "randonnée": ["randonn", "marche", "balade", "trek", "gr10", "gr36", "sentier"],
            "baignade": ["baign", "nage", "plong", "piscine naturelle", "bassin"],
            "escalade": ["escalad", "grimp", "varap", "bloc", "voie", "falaise"],
            "vtt": ["vtt", "vélo", "cycl", "piste", "bike"],
            "kayak": ["kayak", "canoë", "paddle", "raft", "rivière"],
            "camping": ["camp", "bivouac", "tente", "nuit", "dormir"],
            "pêche": ["pêch", "poisson", "truite", "carpe"],
            "spéléo": ["spéléo", "grotte", "caverne", "gouffre", "aven"],
        }

    def estimate_data_size(self, file_path: Union[str, Path]) -> float:
        """Estimate data size in GB"""
        path = Path(file_path)
        if path.exists():
            return path.stat().st_size / (1024**3)  # Convert to GB
        return 0.0

    def select_backend(self, data_size_gb: float) -> str:
        """Auto-select backend based on data size"""
        if self.backend != "auto":
            return self.backend

        if data_size_gb < 1:
            return "pandas"
        elif data_size_gb < 10:
            return "pandas_chunked"
        elif data_size_gb < 100 and DASK_AVAILABLE:
            return "dask"
        elif SPARK_AVAILABLE:
            return "spark"
        else:
            logger.warning("Large dataset but no Dask/Spark available, using chunked pandas")
            return "pandas_chunked"

    def process_text_batch(self, texts: pd.Series) -> pd.DataFrame:
        """Process a batch of text to extract features"""
        results = []

        for text in texts:
            if pd.isna(text):
                results.append(
                    {
                        "locations": [],
                        "activities": [],
                        "location_count": 0,
                        "activity_count": 0,
                        "text_length": 0,
                        "has_coordinates": False,
                    }
                )
                continue

            # Extract locations
            locations = []
            for pattern in self.location_patterns:
                matches = re.findall(pattern, str(text), re.IGNORECASE)
                locations.extend([m for m in matches if isinstance(m, str)])

            # Extract activities
            activities = []
            text_lower = str(text).lower()
            for activity, keywords in self.activity_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    activities.append(activity)

            # Check for coordinates
            coord_pattern = r"(\d{1,2}[.,]\d+)[°\s,]+(\d{1,3}[.,]\d+)"
            has_coords = bool(re.search(coord_pattern, str(text)))

            results.append(
                {
                    "locations": list(set(locations)),
                    "activities": list(set(activities)),
                    "location_count": len(set(locations)),
                    "activity_count": len(set(activities)),
                    "text_length": len(str(text)),
                    "has_coordinates": has_coords,
                }
            )

        return pd.DataFrame(results)

    def calculate_engagement_score(self, row: pd.Series) -> float:
        """Calculate weighted engagement score"""
        likes = row.get("likes", 0) or 0
        comments = row.get("comments", 0) or 0
        shares = row.get("shares", 0) or 0

        # Weighted formula: shares are most valuable
        return likes + (comments * 2) + (shares * 5)

    def process_with_pandas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process data using standard pandas (for <1GB)"""
        logger.info(f"Processing {len(df)} rows with pandas")

        # Extract text features
        text_features = self.process_text_batch(df["text"])
        df = pd.concat([df, text_features], axis=1)

        # Calculate engagement
        df["engagement_score"] = df.apply(self.calculate_engagement_score, axis=1)

        # Parse dates
        if "created_time" in df.columns:
            df["created_time"] = pd.to_datetime(df["created_time"], errors="coerce")
            df["year"] = df["created_time"].dt.year
            df["month"] = df["created_time"].dt.month
            df["day_of_week"] = df["created_time"].dt.day_name()
            df["hour"] = df["created_time"].dt.hour

        # Filter Occitanie-related posts
        occitanie_keywords = [
            "occitanie",
            "toulouse",
            "montpellier",
            "perpignan",
            "nîmes",
            "pyrénées",
            "cévennes",
            "hérault",
            "gard",
            "aude",
            "ariège",
        ]

        df["is_occitanie"] = df["text"].str.lower().str.contains("|".join(occitanie_keywords), na=False)

        return df

    def process_with_chunks(self, file_path: str, output_path: Optional[str] = None) -> Dict:
        """Process large files in chunks (1-10GB)"""
        logger.info(f"Processing file in chunks: {file_path}")

        # Statistics accumulators
        total_rows = 0
        location_counts = {}
        activity_counts = {}
        engagement_sum = 0
        occitanie_count = 0

        # Process in chunks
        for chunk_num, chunk in enumerate(pd.read_json(file_path, lines=True, chunksize=self.chunk_size)):
            logger.info(f"Processing chunk {chunk_num + 1}")

            # Process chunk
            processed_chunk = self.process_with_pandas(chunk)

            # Update statistics
            total_rows += len(processed_chunk)
            engagement_sum += processed_chunk["engagement_score"].sum()
            occitanie_count += processed_chunk["is_occitanie"].sum()

            # Count locations
            for locations in processed_chunk["locations"]:
                for loc in locations:
                    location_counts[loc] = location_counts.get(loc, 0) + 1

            # Count activities
            for activities in processed_chunk["activities"]:
                for act in activities:
                    activity_counts[act] = activity_counts.get(act, 0) + 1

            # Save processed chunk if output specified
            if output_path:
                mode = "w" if chunk_num == 0 else "a"
                processed_chunk.to_json(output_path, orient="records", lines=True, mode=mode)

            # Clear memory
            del processed_chunk
            gc.collect()

        # Return summary statistics
        return {
            "total_rows": total_rows,
            "occitanie_posts": occitanie_count,
            "avg_engagement": engagement_sum / total_rows if total_rows > 0 else 0,
            "top_locations": sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:20],
            "top_activities": sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    def process_with_dask(self, file_path: str):
        """Process very large files with Dask (10-100GB)"""
        if not DASK_AVAILABLE:
            raise ImportError("Dask not installed. Install with: pip install dask[complete]")

        logger.info(f"Processing with Dask: {file_path}")

        # Read as Dask DataFrame
        ddf = dd.read_json(file_path, lines=True, blocksize="64MB")

        # Apply text processing
        meta = pd.DataFrame(
            {
                "locations": [[]],
                "activities": [[]],
                "location_count": [0],
                "activity_count": [0],
                "text_length": [0],
                "has_coordinates": [False],
            }
        )

        text_features = ddf["text"].map_partitions(self.process_text_batch, meta=meta)

        # Combine with original data
        ddf = dd.concat([ddf, text_features], axis=1)

        # Calculate engagement score
        ddf["engagement_score"] = ddf.apply(
            self.calculate_engagement_score, axis=1, meta=("engagement_score", "float64")
        )

        return ddf

    def analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze posting patterns over time"""
        if "created_time" not in df.columns:
            return {}

        # Best posting times
        hourly_engagement = df.groupby("hour")["engagement_score"].mean()
        best_hours = hourly_engagement.nlargest(3).index.tolist()

        # Best days
        daily_engagement = df.groupby("day_of_week")["engagement_score"].mean()
        best_days = daily_engagement.nlargest(3).index.tolist()

        # Seasonal patterns
        monthly_posts = df.groupby("month").size()
        peak_months = monthly_posts.nlargest(3).index.tolist()

        return {
            "best_posting_hours": best_hours,
            "best_posting_days": best_days,
            "peak_months": peak_months,
            "hourly_pattern": hourly_engagement.to_dict(),
            "daily_pattern": daily_engagement.to_dict(),
        }

    def find_spot_clusters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify clusters of related outdoor spots"""
        # Filter for outdoor posts with locations
        outdoor_df = df[(df["location_count"] > 0) & (df["activity_count"] > 0) & (df["is_occitanie"] == True)].copy()

        if outdoor_df.empty:
            return pd.DataFrame()

        # Group by primary location
        outdoor_df["primary_location"] = outdoor_df["locations"].apply(lambda x: x[0] if x else "Unknown")

        # Aggregate by location
        location_stats = (
            outdoor_df.groupby("primary_location")
            .agg(
                {
                    "engagement_score": ["sum", "mean", "count"],
                    "activities": lambda x: list(set([act for acts in x for act in acts])),
                    "text": lambda x: " ".join(x.astype(str))[:500],  # Sample text
                }
            )
            .reset_index()
        )

        # Flatten column names
        location_stats.columns = [
            "location",
            "total_engagement",
            "avg_engagement",
            "post_count",
            "activities",
            "sample_text",
        ]

        # Calculate popularity score
        location_stats["popularity_score"] = (
            location_stats["total_engagement"] * 0.3
            + location_stats["avg_engagement"] * 0.5
            + location_stats["post_count"] * 0.2
        )

        return location_stats.sort_values("popularity_score", ascending=False)

    def export_insights(self, df: pd.DataFrame, output_dir: str):
        """Export analysis insights to multiple formats"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 1. Top spots for outdoor activities
        spot_clusters = self.find_spot_clusters(df)
        if not spot_clusters.empty:
            spot_clusters.head(50).to_csv(output_path / "top_outdoor_spots.csv", index=False)

        # 2. Activity popularity
        all_activities = []
        for acts in df["activities"]:
            if isinstance(acts, list):
                all_activities.extend(acts)

        activity_df = pd.DataFrame(pd.Series(all_activities).value_counts()).reset_index()
        activity_df.columns = ["activity", "mention_count"]
        activity_df.to_csv(output_path / "activity_popularity.csv", index=False)

        # 3. Temporal insights
        temporal = self.analyze_temporal_patterns(df)
        with open(output_path / "temporal_insights.json", "w") as f:
            json.dump(temporal, f, indent=2)

        # 4. High-engagement posts
        top_posts = df.nlargest(100, "engagement_score")[
            ["text", "engagement_score", "locations", "activities", "created_time"]
        ]
        top_posts.to_json(output_path / "high_engagement_posts.json", orient="records", indent=2)

        logger.info(f"Insights exported to {output_path}")


def demo_processor():
    """Demonstrate the Facebook data processor"""
    processor = FacebookDataProcessor()

    # Create sample data
    sample_data = {
        "text": [
            "Magnifique randonnée au Pic du Canigou! Vue incroyable sur toute l'Occitanie 🏔️",
            "Baignade rafraîchissante au Lac de Salagou, eau turquoise parfaite! #Hérault",
            "Escalade aux Gorges du Tarn ce weekend, voies magnifiques pour tous niveaux",
            "Camping sauvage dans les Cévennes, nuit étoilée inoubliable ⛺",
            "VTT dans la forêt de Fontfroide près de Narbonne, 30km de pur plaisir!",
        ],
        "likes": [245, 189, 156, 298, 97],
        "comments": [34, 28, 19, 45, 12],
        "shares": [12, 8, 5, 18, 3],
        "created_time": pd.date_range("2025-01-01", periods=5, freq="D"),
    }

    df = pd.DataFrame(sample_data)

    # Process data
    processed_df = processor.process_with_pandas(df)

    logger.info("📊 Processed Facebook Data:")
    logger.info("=" * 60)
    logger.info(processed_df[["locations", "activities", "engagement_score"]].to_string())

    # Find spot clusters
    clusters = processor.find_spot_clusters(processed_df)
    logger.info("\n🏆 Top Outdoor Spots:")
    logger.info("=" * 60)
    if not clusters.empty:
        logger.info(clusters[["location", "activities", "popularity_score"]].to_string())

    # Export insights
    processor.export_insights(processed_df, "exports/facebook_insights")


if __name__ == "__main__":
    demo_processor()
