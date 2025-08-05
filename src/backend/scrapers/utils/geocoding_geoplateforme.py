#!/usr/bin/env python3
"""
Géoplateforme (cartes.gouv.fr) Geocoding Integration
Official French government geocoding service - No API key required
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode
from src.backend.core.logging_config import logger


class GeoplatefomeGeocoder:
    """Geocoder using the official French Géoplateforme service"""

    def __init__(self):
        # Géoplateforme geocoding endpoint (2025) - no auth required
        # API Adresse has been integrated into Géoplateforme as of April 2025
        self.base_url = "https://data.geopf.fr/geocodage"
        self.search_endpoint = f"{self.base_url}/search"
        self.reverse_endpoint = f"{self.base_url}/reverse"
        self.autocomplete_endpoint = f"{self.base_url}/autocomplete"

        # Rate limiting: 50 requests/second max
        self.rate_limit = 40  # Conservative limit
        self.last_request_time = 0
        self.min_delay = 1.0 / self.rate_limit

        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "OccitanieSpotsProject/1.0", "Accept": "application/json"})

    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)

        self.last_request_time = time.time()

    def geocode(self, query: str, **kwargs) -> Optional[Dict]:
        """
        Geocode a location query using Géoplateforme

        Args:
            query: Location name to geocode
            **kwargs: Additional parameters:
                - limit: Max results (default 5)
                - postcode: Filter by postal code
                - lat/lon: Provide hint coordinates
                - returntruegeometry: Return full geometry
                - type: Filter by type (StreetAddress, PositionOfInterest, etc.)

        Returns:
            Dict with geocoding results or None
        """
        self._rate_limit()

        # Build parameters
        params = {
            "q": query,
            "limit": kwargs.get("limit", 5),
            "returntruegeometry": str(kwargs.get("returntruegeometry", True)).lower(),
        }

        # Add optional parameters
        if "postcode" in kwargs:
            params["postcode"] = kwargs["postcode"]
        if "lat" in kwargs and "lon" in kwargs:
            params["lat"] = kwargs["lat"]
            params["lon"] = kwargs["lon"]
        if "type" in kwargs:
            params["type"] = kwargs["type"]

        try:
            response = self.session.get(self.search_endpoint, params=params, timeout=10)

            if response.status_code == 429:
                logger.info("Rate limit exceeded, waiting...")
                time.sleep(2)
                return self.geocode(query, **kwargs)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.info(f"Géoplateforme geocoding error: {e}")
            return None

    def geocode_occitanie(self, location: str, department: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """
        Geocode specifically for Occitanie region

        Args:
            location: Place name
            department: Optional department code (09, 11, 12, etc.)

        Returns:
            Tuple of (latitude, longitude) or None
        """
        # Add Occitanie context
        query = f"{location}, Occitanie, France"

        # If department provided, use postal code hint
        dept_postcodes = {
            "09": "09000",  # Ariège
            "11": "11000",  # Aude
            "12": "12000",  # Aveyron
            "30": "30000",  # Gard
            "31": "31000",  # Haute-Garonne
            "32": "32000",  # Gers
            "34": "34000",  # Hérault
            "46": "46000",  # Lot
            "48": "48000",  # Lozère
            "65": "65000",  # Hautes-Pyrénées
            "66": "66000",  # Pyrénées-Orientales
            "81": "81000",  # Tarn
            "82": "82000",  # Tarn-et-Garonne
        }

        kwargs = {}
        if department and department in dept_postcodes:
            kwargs["postcode"] = dept_postcodes[department]

        result = self.geocode(query, **kwargs)

        if result and "features" in result and result["features"]:
            # Get first result
            feature = result["features"][0]
            if "geometry" in feature and "coordinates" in feature["geometry"]:
                lon, lat = feature["geometry"]["coordinates"]

                # Validate Occitanie bounds
                if 42.0 <= lat <= 45.0 and -0.5 <= lon <= 4.5:
                    return (lat, lon)

        return None

    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Reverse geocode coordinates to get location info

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with location information or None
        """
        self._rate_limit()

        params = {"lon": lon, "lat": lat}

        try:
            response = self.session.get(self.reverse_endpoint, params=params, timeout=10)

            if response.status_code == 429:
                logger.info("Rate limit exceeded, waiting...")
                time.sleep(2)
                return self.reverse_geocode(lat, lon)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.info(f"Géoplateforme reverse geocoding error: {e}")
            return None

    def batch_geocode(self, locations: List[str], delay: float = 0.1) -> List[Dict]:
        """
        Geocode multiple locations with rate limiting

        Args:
            locations: List of location names
            delay: Additional delay between requests

        Returns:
            List of geocoding results
        """
        results = []

        for location in locations:
            result = self.geocode_occitanie(location)
            results.append({"query": location, "coordinates": result, "success": result is not None})

            # Additional delay for batch operations
            time.sleep(delay)

        return results

    def search_poi(self, query: str, poi_type: Optional[str] = None) -> List[Dict]:
        """
        Search for Points of Interest

        Args:
            query: Search query
            poi_type: Filter by POI type (e.g., 'lac', 'cascade', 'mont')

        Returns:
            List of POI results
        """
        # For Géoplateforme, POI search doesn't use 'type' parameter
        # Just search with the query
        kwargs = {"limit": 20}

        result = self.geocode(query, **kwargs)

        if result and "features" in result:
            pois = []
            for feature in result["features"]:
                properties = feature.get("properties", {})

                # Filter by POI type if specified
                if poi_type and poi_type.lower() not in properties.get("label", "").lower():
                    continue

                poi = {
                    "name": properties.get("label", ""),
                    "type": properties.get("type", ""),
                    "city": properties.get("city", ""),
                    "postcode": properties.get("postcode", ""),
                    "coordinates": None,
                }

                if "geometry" in feature and "coordinates" in feature["geometry"]:
                    lon, lat = feature["geometry"]["coordinates"]
                    poi["coordinates"] = (lat, lon)

                pois.append(poi)

            return pois

        return []


def main():
    """Test Géoplateforme geocoding"""
    geocoder = GeoplatefomeGeocoder()

    logger.info("🗺️ Géoplateforme Geocoding Test")
    logger.info("=" * 50)

    # Test locations in Occitanie
    test_locations = [
        "Lac de Salagou",
        "Pic du Canigou",
        "Gorges du Tarn",
        "Cascade d'Ars",
        "Pont du Gard",
        "Cirque de Gavarnie",
    ]

    logger.info("\n📍 Geocoding Occitanie locations:")
    for location in test_locations:
        coords = geocoder.geocode_occitanie(location)
        if coords:
            logger.info(f"✅ {location}: {coords[0]:.6f}, {coords[1]:.6f}")
        else:
            logger.info(f"❌ {location}: Not found")

    # Test POI search
    logger.info("\n🔍 Searching for lakes in Occitanie:")
    lakes = geocoder.search_poi("lac", poi_type="lac")
    for lake in lakes[:5]:
        if lake["coordinates"]:
            logger.info(
                f"  - {lake['name']} ({lake['city']}): {lake['coordinates'][0]:.4f}, {lake['coordinates'][1]:.4f}"
            )

    # Test reverse geocoding
    logger.info("\n🔄 Reverse geocoding test:")
    # Coordinates of Toulouse
    result = geocoder.reverse_geocode(43.6047, 1.4442)
    if result and "features" in result and result["features"]:
        props = result["features"][0].get("properties", {})
        logger.info(f"  Location: {props.get('label', 'Unknown')}")
        logger.info(f"  City: {props.get('city', 'Unknown')}")
        logger.info(f"  Postcode: {props.get('postcode', 'Unknown')}")

    logger.info("\n✅ Géoplateforme integration ready!")
    logger.info("  - No API key required")
    logger.info("  - 50 requests/second limit")
    logger.info("  - Official French government service")


if __name__ == "__main__":
    main()
