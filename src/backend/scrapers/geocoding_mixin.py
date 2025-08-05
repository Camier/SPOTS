#!/usr/bin/env python3
"""Geocoding mixin for scrapers using Ola Maps API"""

import os
import logging
import requests
from typing import Optional, Tuple, Dict
import time


class GeocodingMixin:
    """Mixin to add Ola Maps geocoding capabilities to scrapers"""

    def __init__(self):
        self.ola_api_key = os.getenv("OLA_MAPS_API_KEY", "")
        self.ola_base_url = "https://api.olamaps.io/places/v1"
        self.geocoding_cache = {}

    def geocode_address(self, address: str) -> Optional[Dict]:
        """Convert address to coordinates using Ola Maps"""
        if not self.ola_api_key:
            logging.warning("OLA_MAPS_API_KEY not set, skipping geocoding")
            return None

        # Check cache first
        if address in self.geocoding_cache:
            return self.geocoding_cache[address]

        try:
            # Add region context for better results
            search_query = f"{address}, Occitanie, France"

            response = requests.get(
                f"{self.ola_base_url}/geocode",
                params={"address": search_query, "api_key": self.ola_api_key},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and data.get("results"):
                    result = data["results"][0]
                    geocoded = {
                        "latitude": result["geometry"]["location"]["lat"],
                        "longitude": result["geometry"]["location"]["lng"],
                        "formatted_address": result.get("formatted_address", ""),
                        "confidence": result.get("confidence", 0.5),
                        "place_id": result.get("place_id"),
                    }
                    self.geocoding_cache[address] = geocoded
                    return geocoded

        except Exception as e:
            logging.error(f"Geocoding error for '{address}': {e}")

        return None

    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Convert coordinates to address using Ola Maps"""
        if not self.ola_api_key:
            return None

        cache_key = f"{lat},{lon}"
        if cache_key in self.geocoding_cache:
            return self.geocoding_cache[cache_key]

        try:
            response = requests.get(
                f"{self.ola_base_url}/reverse-geocode",
                params={"latlng": f"{lat},{lon}", "api_key": self.ola_api_key},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and data.get("results"):
                    address = data["results"][0].get("formatted_address", "")
                    self.geocoding_cache[cache_key] = address
                    return address

        except Exception as e:
            logging.error(f"Reverse geocoding error for {lat},{lon}: {e}")

        return None

    def get_elevation(self, lat: float, lon: float) -> Optional[float]:
        """Get elevation for coordinates using Ola Maps"""
        if not self.ola_api_key:
            return None

        try:
            response = requests.get(
                f"{self.ola_base_url}/elevation",
                params={"locations": f"{lat},{lon}", "api_key": self.ola_api_key},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and data.get("results"):
                    return data["results"][0].get("elevation")

        except Exception as e:
            logging.error(f"Elevation lookup error for {lat},{lon}: {e}")

        return None

    def find_nearby_places(self, lat: float, lon: float, radius: int = 1000, category: str = None) -> list:
        """Find nearby places using Ola Maps"""
        if not self.ola_api_key:
            return []

        try:
            params = {"location": f"{lat},{lon}", "radius": radius, "api_key": self.ola_api_key}

            if category:
                params["types"] = category

            response = requests.get(f"{self.ola_base_url}/nearbysearch", params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return data.get("results", [])

        except Exception as e:
            logging.error(f"Nearby search error: {e}")

        return []

    def enhance_spot_with_geocoding(self, spot_data: Dict) -> Dict:
        """Enhance spot data with geocoding information"""
        # If we have a name/description but no coordinates, try geocoding
        if not (spot_data.get("latitude") and spot_data.get("longitude")):
            location_text = spot_data.get("name", "") or spot_data.get("description", "")
            if location_text:
                geocoded = self.geocode_address(location_text)
                if geocoded:
                    spot_data["latitude"] = geocoded["latitude"]
                    spot_data["longitude"] = geocoded["longitude"]
                    spot_data["geocoding_confidence"] = geocoded["confidence"]
                    spot_data["address"] = geocoded["formatted_address"]
                    logging.info(f"Geocoded '{location_text}' to {geocoded['latitude']}, {geocoded['longitude']}")

        # If we have coordinates, enhance with address and elevation
        if spot_data.get("latitude") and spot_data.get("longitude"):
            lat, lon = spot_data["latitude"], spot_data["longitude"]

            # Get elevation
            if not spot_data.get("elevation"):
                elevation = self.get_elevation(lat, lon)
                if elevation is not None:
                    spot_data["elevation"] = elevation
                    logging.info(f"Added elevation {elevation}m for {lat}, {lon}")

            # Get address if missing
            if not spot_data.get("address"):
                address = self.reverse_geocode(lat, lon)
                if address:
                    spot_data["address"] = address
                    logging.info(f"Added address for {lat}, {lon}: {address}")

        return spot_data
