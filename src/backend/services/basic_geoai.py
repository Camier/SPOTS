#!/usr/bin/env python3
"""
Basic GeoAI Service for SPOTS - Proof of Concept
Implements simple AI-powered features without heavy dependencies
"""

import math
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
from src.backend.core.logging_config import logger


class BasicGeoAI:
    """
    Basic GeoAI implementation using simple algorithms
    No ML dependencies required for initial proof of concept
    """

    def __init__(self):
        # Occitanie region bounds
        self.region_bounds = {"lat_min": 42.3, "lat_max": 45.0, "lon_min": -0.5, "lon_max": 4.0}

        # Terrain difficulty factors
        self.terrain_factors = {
            "slope_easy": 5,  # degrees
            "slope_moderate": 15,
            "slope_difficult": 25,
            "elevation_change_easy": 100,  # meters
            "elevation_change_moderate": 300,
            "elevation_change_difficult": 500,
        }

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def estimate_accessibility_score(self, spot: Dict) -> float:
        """
        Estimate accessibility based on simple heuristics
        Returns score 0-1 (1 being most accessible)
        """
        score = 1.0

        # Elevation penalty (higher = less accessible)
        if elevation := spot.get("elevation"):
            if elevation > 2000:
                score *= 0.5
            elif elevation > 1500:
                score *= 0.7
            elif elevation > 1000:
                score *= 0.85

        # Type-based accessibility
        spot_type = spot.get("type", "unknown")
        type_accessibility = {
            "waterfall": 0.8,  # Often requires hiking
            "cave": 0.7,  # Can be challenging to access
            "spring": 0.9,  # Usually easier
            "ruins": 0.85,  # Varies
            "unknown": 0.5,
        }
        score *= type_accessibility.get(spot_type, 0.5)

        # Description-based keywords (simple NLP)
        description = spot.get("description", "").lower()
        if any(word in description for word in ["facile", "easy", "accessible", "parking"]):
            score *= 1.2
        if any(word in description for word in ["difficile", "hard", "technique", "escalade"]):
            score *= 0.7
        if any(word in description for word in ["dangereux", "dangerous", "interdit"]):
            score *= 0.3

        # Weather sensitivity penalty
        if spot.get("weather_sensitive"):
            score *= 0.85

        return min(max(score, 0.0), 1.0)

    def predict_crowd_level(self, spot: Dict, date: Optional[datetime] = None) -> str:
        """
        Predict crowd levels based on various factors
        Returns: 'low', 'medium', or 'high'
        """
        if date is None:
            date = datetime.now()

        crowd_score = 0.0

        # Weekend factor
        if date.weekday() >= 5:  # Saturday or Sunday
            crowd_score += 0.4

        # Summer vacation factor (July-August)
        if date.month in [7, 8]:
            crowd_score += 0.3

        # Accessibility factor (easier = more crowded)
        accessibility = self.estimate_accessibility_score(spot)
        crowd_score += accessibility * 0.3

        # Popular spot types
        if spot.get("type") == "waterfall":
            crowd_score += 0.2

        # Confidence score (well-known spots are busier)
        if spot.get("confidence_score", 0) > 0.9:
            crowd_score += 0.2

        # Convert to category
        if crowd_score < 0.3:
            return "low"
        elif crowd_score < 0.7:
            return "medium"
        else:
            return "high"

    def calculate_difficulty_score(self, spot: Dict) -> Dict[str, any]:
        """
        Calculate difficulty score based on available data
        """
        difficulty = {"overall": "unknown", "score": 0.5, "factors": {}}

        # Elevation factor
        if elevation := spot.get("elevation"):
            if elevation > 2000:
                difficulty["factors"]["elevation"] = "difficult"
                difficulty["score"] += 0.3
            elif elevation > 1500:
                difficulty["factors"]["elevation"] = "moderate"
                difficulty["score"] += 0.2
            else:
                difficulty["factors"]["elevation"] = "easy"
                difficulty["score"] += 0.1

        # Type-based difficulty
        type_difficulty = {"waterfall": 0.6, "cave": 0.7, "spring": 0.3, "ruins": 0.5}
        if spot_type := spot.get("type"):
            difficulty["factors"]["type"] = spot_type
            difficulty["score"] = (difficulty["score"] + type_difficulty.get(spot_type, 0.5)) / 2

        # Accessibility inverse correlation
        accessibility = self.estimate_accessibility_score(spot)
        difficulty["factors"]["accessibility"] = round(accessibility, 2)
        difficulty["score"] = (difficulty["score"] + (1 - accessibility)) / 2

        # Overall rating
        if difficulty["score"] < 0.3:
            difficulty["overall"] = "easy"
        elif difficulty["score"] < 0.7:
            difficulty["overall"] = "moderate"
        else:
            difficulty["overall"] = "difficult"

        return difficulty

    def recommend_spots(
        self, user_lat: float, user_lon: float, preferences: Dict, spots: List[Dict], limit: int = 10
    ) -> List[Dict]:
        """
        Recommend spots based on user location and preferences
        """
        recommendations = []

        max_distance = preferences.get("max_distance", 50)
        preferred_types = preferences.get("types", ["all"])
        difficulty_pref = preferences.get("difficulty", "all")
        avoid_crowds = preferences.get("avoid_crowds", False)

        for spot in spots:
            # Calculate distance
            distance = self.calculate_distance(user_lat, user_lon, spot["latitude"], spot["longitude"])

            if distance > max_distance:
                continue

            # Type filter
            if "all" not in preferred_types and spot.get("type") not in preferred_types:
                continue

            # Calculate scores
            accessibility = self.estimate_accessibility_score(spot)
            crowd_level = self.predict_crowd_level(spot)
            difficulty = self.calculate_difficulty_score(spot)

            # Difficulty filter
            if difficulty_pref != "all" and difficulty["overall"] != difficulty_pref:
                continue

            # Crowd filter
            if avoid_crowds and crowd_level == "high":
                continue

            # Calculate recommendation score
            rec_score = 1.0

            # Distance factor (closer is better)
            rec_score *= 1 - (distance / max_distance)

            # Accessibility factor
            rec_score *= accessibility

            # Crowd avoidance factor
            if avoid_crowds:
                crowd_multiplier = {"low": 1.2, "medium": 1.0, "high": 0.5}
                rec_score *= crowd_multiplier.get(crowd_level, 1.0)

            # Confidence factor
            rec_score *= spot.get("confidence_score", 0.5)

            # Add to recommendations
            recommendations.append(
                {
                    "spot": spot,
                    "distance": round(distance, 1),
                    "recommendation_score": round(rec_score, 3),
                    "accessibility_score": round(accessibility, 2),
                    "crowd_level": crowd_level,
                    "difficulty": difficulty["overall"],
                    "reasons": self._generate_recommendation_reasons(
                        spot, distance, accessibility, crowd_level, difficulty
                    ),
                }
            )

        # Sort by recommendation score
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

        return recommendations[:limit]

    def _generate_recommendation_reasons(
        self, spot: Dict, distance: float, accessibility: float, crowd_level: str, difficulty: Dict
    ) -> List[str]:
        """Generate human-readable reasons for recommendation"""
        reasons = []

        if distance < 10:
            reasons.append(f"Very close ({distance:.1f} km away)")
        elif distance < 25:
            reasons.append(f"Nearby ({distance:.1f} km away)")

        if accessibility > 0.8:
            reasons.append("Easy to access")
        elif accessibility < 0.4:
            reasons.append("Adventure spot - challenging access")

        if crowd_level == "low":
            reasons.append("Usually not crowded")

        if difficulty["overall"] == "easy":
            reasons.append("Suitable for beginners")
        elif difficulty["overall"] == "difficult":
            reasons.append("For experienced hikers")

        if spot.get("type") == "waterfall" and not spot.get("weather_sensitive"):
            reasons.append("Waterfall with year-round flow")

        return reasons

    def analyze_spot_cluster(self, spots: List[Dict], center_lat: float, center_lon: float, radius: float = 20) -> Dict:
        """
        Analyze a cluster of spots for trip planning
        """
        cluster_spots = []

        for spot in spots:
            distance = self.calculate_distance(center_lat, center_lon, spot["latitude"], spot["longitude"])
            if distance <= radius:
                cluster_spots.append({"spot": spot, "distance_from_center": distance})

        if not cluster_spots:
            return {"spots": [], "analysis": {}}

        # Sort by distance
        cluster_spots.sort(key=lambda x: x["distance_from_center"])

        # Analyze the cluster
        analysis = {
            "total_spots": len(cluster_spots),
            "spot_types": {},
            "average_accessibility": 0,
            "difficulty_distribution": {"easy": 0, "moderate": 0, "difficult": 0},
            "suggested_order": [],
            "total_distance": 0,
        }

        # Type distribution
        for item in cluster_spots:
            spot_type = item["spot"].get("type", "unknown")
            analysis["spot_types"][spot_type] = analysis["spot_types"].get(spot_type, 0) + 1

        # Accessibility and difficulty
        total_accessibility = 0
        for item in cluster_spots:
            spot = item["spot"]
            accessibility = self.estimate_accessibility_score(spot)
            total_accessibility += accessibility

            difficulty = self.calculate_difficulty_score(spot)
            analysis["difficulty_distribution"][difficulty["overall"]] += 1

        analysis["average_accessibility"] = round(total_accessibility / len(cluster_spots), 2)

        # Suggest visiting order (simple TSP approximation)
        if len(cluster_spots) <= 5:
            # For small clusters, visit in order of distance from center
            analysis["suggested_order"] = [item["spot"]["id"] for item in cluster_spots]
        else:
            # For larger clusters, group by area
            analysis["suggested_order"] = self._calculate_visit_order(cluster_spots)

        return {"spots": cluster_spots, "analysis": analysis}

    def _calculate_visit_order(self, cluster_spots: List[Dict]) -> List[int]:
        """
        Simple nearest neighbor algorithm for visit order
        """
        if not cluster_spots:
            return []

        visited = []
        current = cluster_spots[0]["spot"]
        visited.append(current["id"])

        while len(visited) < len(cluster_spots):
            nearest_distance = float("inf")
            nearest_spot = None

            for item in cluster_spots:
                spot = item["spot"]
                if spot["id"] in visited:
                    continue

                distance = self.calculate_distance(
                    current["latitude"], current["longitude"], spot["latitude"], spot["longitude"]
                )

                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_spot = spot

            if nearest_spot:
                visited.append(nearest_spot["id"])
                current = nearest_spot
            else:
                break

        return visited


# Example usage and testing
if __name__ == "__main__":
    # Initialize GeoAI
    geoai = BasicGeoAI()

    # Test spot
    test_spot = {
        "id": 1,
        "name": "Cascade de Test",
        "type": "waterfall",
        "latitude": 43.5,
        "longitude": 1.8,
        "elevation": 1200,
        "confidence_score": 0.85,
        "weather_sensitive": True,
        "description": "Beautiful waterfall, easy access from parking",
    }

    # Test accessibility scoring
    accessibility = geoai.estimate_accessibility_score(test_spot)
    logger.info(f"Accessibility score: {accessibility}")

    # Test crowd prediction
    crowd_level = geoai.predict_crowd_level(test_spot)
    logger.info(f"Predicted crowd level: {crowd_level}")

    # Test difficulty calculation
    difficulty = geoai.calculate_difficulty_score(test_spot)
    logger.info(f"Difficulty: {difficulty}")

    # Test recommendations
    user_preferences = {"max_distance": 30, "types": ["waterfall", "cave"], "difficulty": "easy", "avoid_crowds": True}

    recommendations = geoai.recommend_spots(
        43.6,
        1.9,  # User location (near Toulouse)
        user_preferences,
        [test_spot],  # Would normally be full spot list
        limit=5,
    )

    logger.info(f"\nRecommendations: {json.dumps(recommendations, indent=2)}")
