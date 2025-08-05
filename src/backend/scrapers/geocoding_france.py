#!/usr/bin/env python3
"""Geocoding using French Base Adresse Nationale (BAN) API and IGN elevation service"""

import logging
import requests
from typing import Optional, Dict, List, Tuple
import time
from functools import lru_cache
from .geocoding_premium import PremiumGeocodingService


class FrenchGeocodingMixin:
    """Mixin to add French geocoding capabilities using BAN and IGN services"""

    def __init__(self):
        # BAN API endpoints (IGN hosted)
        self.ban_base_url = "https://data.geopf.fr/geocodage"
        self.ban_legacy_url = "https://api-adresse.data.gouv.fr"  # Fallback until 2026

        # IGN elevation service
        self.ign_elevation_url = "https://data.geopf.fr/altimetrie/1.0/calcul/alti"

        # Premium geocoding service
        self.premium_service = PremiumGeocodingService()

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.02  # 50 requests/second max

        self.logger = logging.getLogger(__name__)

    def _rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    @lru_cache(maxsize=1000)
    def geocode_address(self, address: str, limit: int = 1) -> Optional[Dict]:
        """
        Convert address to coordinates using geocoding services
        Priority: Premium -> BAN -> Legacy BAN

        Returns dict with:
        - latitude: float
        - longitude: float
        - formatted_address: str (label from BAN)
        - confidence: float (score from BAN, 0-1)
        - city: str
        - postcode: str
        - department: str (context)
        - precision: str ('premium', 'ban', or 'legacy')
        """
        # Try premium first if enabled
        if self.premium_service.enabled:
            self.logger.debug(f"Trying premium geocoding for: {address}")
            premium_result = self.premium_service.geocode_premium(address)
            if premium_result:
                self.logger.info(f"Premium geocoding success for: {address}")
                return premium_result

        # Fallback to standard BAN
        self._rate_limit()

        try:
            # Try new IGN endpoint first
            response = requests.get(
                f"{self.ban_base_url}/search",
                params={"q": address, "limit": limit, "type": "municipality,street,housenumber"},  # Focus on addresses
                timeout=10,
            )

            # Fallback to legacy endpoint if needed
            if response.status_code != 200:
                self.logger.info("Falling back to legacy BAN endpoint")
                response = requests.get(
                    f"{self.ban_legacy_url}/search", params={"q": address, "limit": limit}, timeout=10
                )

            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    feature = data["features"][0]
                    props = feature.get("properties", {})
                    coords = feature.get("geometry", {}).get("coordinates", [])

                    if len(coords) >= 2:
                        return {
                            "latitude": coords[1],  # BAN returns [lon, lat]
                            "longitude": coords[0],
                            "formatted_address": props.get("label", ""),
                            "confidence": props.get("score", 0.5),
                            "city": props.get("city", ""),
                            "postcode": props.get("postcode", ""),
                            "department": (
                                props.get("context", "").split(",")[0].strip() if props.get("context") else ""
                            ),
                            "type": props.get("type", ""),
                            "importance": props.get("importance", 0),
                            "precision": "ban" if "data.geopf.fr" in response.url else "legacy",
                        }

        except Exception as e:
            self.logger.error(f"Geocoding error for '{address}': {e}")

        return None

    @lru_cache(maxsize=1000)
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Convert coordinates to address using geocoding services
        Priority: Premium -> BAN -> Legacy BAN"""

        # Try premium first if enabled
        if self.premium_service.enabled:
            premium_result = self.premium_service.reverse_geocode_premium(lat, lon)
            if premium_result:
                return premium_result.get("address", "")

        # Fallback to standard BAN
        self._rate_limit()

        try:
            # Try new IGN endpoint
            response = requests.get(
                f"{self.ban_base_url}/reverse",
                params={"lon": lon, "lat": lat, "type": "municipality,street,housenumber"},
                timeout=10,
            )

            # Fallback to legacy endpoint
            if response.status_code != 200:
                response = requests.get(f"{self.ban_legacy_url}/reverse", params={"lon": lon, "lat": lat}, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    return data["features"][0]["properties"].get("label", "")

        except Exception as e:
            self.logger.error(f"Reverse geocoding error for {lat},{lon}: {e}")

        return None

    def get_elevation_ign(self, lat: float, lon: float) -> Optional[float]:
        """
        Get elevation using IGN altimetry service
        Free service, no API key required
        """
        self._rate_limit()

        try:
            # IGN expects lon,lat format
            response = requests.get(
                self.ign_elevation_url,
                params={
                    "lon": lon,
                    "lat": lat,
                    "resource": "ign_rge_alti_wld",  # RGE ALTI dataset
                    "zonly": "true",  # Only return elevation value
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if "elevations" in data and data["elevations"]:
                    return float(data["elevations"][0])

        except Exception as e:
            self.logger.error(f"IGN elevation error for {lat},{lon}: {e}")

        # Fallback to Open-Elevation API (global coverage)
        return self.get_elevation_open(lat, lon)

    def get_elevation_open(self, lat: float, lon: float) -> Optional[float]:
        """
        Fallback elevation service using Open-Elevation
        Free, no API key required
        """
        try:
            response = requests.get(
                "https://api.open-elevation.com/api/v1/lookup", params={"locations": f"{lat},{lon}"}, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    return float(data["results"][0]["elevation"])

        except Exception as e:
            self.logger.error(f"Open-Elevation error for {lat},{lon}: {e}")

        return None

    def get_elevation(self, lat: float, lon: float) -> Optional[float]:
        """Get elevation, trying IGN first then fallback"""
        elevation = self.get_elevation_ign(lat, lon)
        if elevation is None:
            self.logger.info(f"IGN elevation failed for {lat},{lon}, trying Open-Elevation")
            elevation = self.get_elevation_open(lat, lon)
        return elevation

    def search_places_ban(
        self, query: str, lat: Optional[float] = None, lon: Optional[float] = None, limit: int = 10
    ) -> List[Dict]:
        """
        Search for places using BAN API
        Can be biased towards a location if lat/lon provided
        """
        self._rate_limit()

        try:
            params = {"q": query, "limit": limit, "type": "municipality,locality,street"}

            # Add location bias if provided
            if lat and lon:
                params["lat"] = lat
                params["lon"] = lon

            response = requests.get(f"{self.ban_base_url}/search", params=params, timeout=10)

            if response.status_code != 200:
                response = requests.get(f"{self.ban_legacy_url}/search", params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                places = []

                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    coords = feature.get("geometry", {}).get("coordinates", [])

                    if len(coords) >= 2:
                        places.append(
                            {
                                "name": props.get("label", ""),
                                "latitude": coords[1],
                                "longitude": coords[0],
                                "type": props.get("type", ""),
                                "city": props.get("city", ""),
                                "postcode": props.get("postcode", ""),
                                "score": props.get("score", 0),
                            }
                        )

                return places

        except Exception as e:
            self.logger.error(f"Place search error for '{query}': {e}")

        return []

    def get_department_code(self, lat: float, lon: float) -> Optional[str]:
        """Get department code from coordinates"""
        address = self.reverse_geocode(lat, lon)
        if address:
            # Try to extract department from context
            response = self.geocode_address(address, limit=1)
            if response and response.get("department"):
                # Extract department number (e.g., "31" from "31, Haute-Garonne")
                dept = response["department"]
                if dept and len(dept) >= 2:
                    return dept[:2]
        return None

    def enhance_spot_with_geocoding(self, spot_data: Dict) -> Dict:
        """Enhance spot data with French geocoding information"""
        # If we have a name/description but no coordinates, try geocoding
        if not (spot_data.get("latitude") and spot_data.get("longitude")):
            location_text = spot_data.get("name", "") or spot_data.get("description", "")

            # Add Occitanie context for better results
            if location_text and "occitanie" not in location_text.lower():
                location_text = f"{location_text}, Occitanie, France"

            if location_text:
                geocoded = self.geocode_address(location_text)
                if geocoded:
                    spot_data["latitude"] = geocoded["latitude"]
                    spot_data["longitude"] = geocoded["longitude"]
                    spot_data["geocoding_confidence"] = geocoded["confidence"]
                    spot_data["address"] = geocoded["formatted_address"]
                    spot_data["city"] = geocoded.get("city", "")
                    spot_data["postcode"] = geocoded.get("postcode", "")
                    self.logger.info(f"Geocoded '{location_text}' to {geocoded['latitude']}, {geocoded['longitude']}")

        # If we have coordinates, enhance with address and elevation
        if spot_data.get("latitude") and spot_data.get("longitude"):
            lat, lon = spot_data["latitude"], spot_data["longitude"]

            # Get elevation
            if not spot_data.get("elevation"):
                elevation = self.get_elevation(lat, lon)
                if elevation is not None:
                    spot_data["elevation"] = elevation
                    self.logger.info(f"Added elevation {elevation}m for {lat}, {lon}")

            # Get address if missing
            if not spot_data.get("address"):
                address = self.reverse_geocode(lat, lon)
                if address:
                    spot_data["address"] = address
                    self.logger.info(f"Added address for {lat}, {lon}: {address}")

            # Get department code
            if not spot_data.get("department"):
                dept_code = self.get_department_code(lat, lon)
                if dept_code:
                    spot_data["department"] = dept_code

        return spot_data


# Occitanie-specific helper
class OccitanieGeocoder(FrenchGeocodingMixin):
    """Specialized geocoder for Occitanie region"""

    OCCITANIE_DEPARTMENTS = {
        "09": "Ariège",
        "11": "Aude",
        "12": "Aveyron",
        "30": "Gard",
        "31": "Haute-Garonne",
        "32": "Gers",
        "34": "Hérault",
        "46": "Lot",
        "48": "Lozère",
        "65": "Hautes-Pyrénées",
        "66": "Pyrénées-Orientales",
        "81": "Tarn",
        "82": "Tarn-et-Garonne",
    }

    def is_in_occitanie(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in Occitanie region"""
        dept_code = self.get_department_code(lat, lon)
        return dept_code in self.OCCITANIE_DEPARTMENTS

    def geocode_occitanie(self, address: str) -> Optional[Dict]:
        """Geocode with Occitanie context"""
        # Try as-is first
        result = self.geocode_address(address)

        # If low confidence or not in Occitanie, try with context
        if not result or result["confidence"] < 0.7:
            enhanced_address = f"{address}, Occitanie, France"
            enhanced_result = self.geocode_address(enhanced_address)

            if enhanced_result and enhanced_result["confidence"] > (result["confidence"] if result else 0):
                result = enhanced_result

        # Verify it's in Occitanie
        if result and self.is_in_occitanie(result["latitude"], result["longitude"]):
            return result

        return None
