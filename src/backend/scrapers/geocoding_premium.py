#!/usr/bin/env python3
"""Premium geocoding using IGN ADRESSE-PREMIUM service"""

import logging
import requests
from typing import Optional, Dict, List, Tuple
import time
import os
from functools import lru_cache
from datetime import datetime, timedelta
import base64


class PremiumGeocodingService:
    """Premium geocoding with ADRESSE-PREMIUM API"""

    def __init__(self):
        # ADRESSE-PREMIUM endpoints
        self.premium_base_url = "https://data.geopf.fr/geocodage-premium"
        self.auth_url = "https://data.geopf.fr/auth/token"

        # Authentication
        self.api_key = os.getenv("ADRESSE_PREMIUM_API_KEY")
        self.username = os.getenv("ADRESSE_PREMIUM_USERNAME")
        self.password = os.getenv("ADRESSE_PREMIUM_PASSWORD")
        self.enabled = os.getenv("ADRESSE_PREMIUM_ENABLED", "false").lower() == "true"

        # Token management
        self.access_token = None
        self.token_expiry = None

        # Rate limiting (premium has higher limits)
        self.last_request_time = 0
        self.min_request_interval = 0.01  # 100 requests/second for premium

        self.logger = logging.getLogger(__name__)

        if self.enabled and not all([self.api_key, self.username, self.password]):
            self.logger.warning("ADRESSE-PREMIUM enabled but credentials missing")
            self.enabled = False

    def _get_auth_token(self) -> Optional[str]:
        """Get or refresh authentication token"""
        # Check if we have a valid token
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        try:
            # Create Basic auth header
            auth_string = f"{self.username}:{self.password}"
            auth_bytes = auth_string.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

            # Request new token
            response = requests.post(
                self.auth_url,
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials", "scope": "geocodage-premium"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Default 1 hour
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 min early
                self.logger.info("Successfully obtained ADRESSE-PREMIUM token")
                return self.access_token
            else:
                self.logger.error(f"Failed to get auth token: {response.status_code} - {response.text}")

        except Exception as e:
            self.logger.error(f"Authentication error: {e}")

        return None

    def _rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    @lru_cache(maxsize=2000)  # Larger cache for premium
    def geocode_premium(self, address: str, filters: Optional[Dict] = None) -> Optional[Dict]:
        """
        Premium geocoding with enhanced features

        Filters can include:
        - type: 'housenumber', 'street', 'locality', 'municipality'
        - citycode: INSEE code filter
        - postcode: Postal code filter
        - lat/lon: Geographic bias
        - limit: Number of results
        """
        if not self.enabled:
            return None

        token = self._get_auth_token()
        if not token:
            return None

        self._rate_limit()

        try:
            params = {
                "q": address,
                "limit": filters.get("limit", 1) if filters else 1,
                "autocomplete": 0,  # Full precision
            }

            # Add optional filters
            if filters:
                for key in ["type", "citycode", "postcode", "lat", "lon"]:
                    if key in filters:
                        params[key] = filters[key]

            response = requests.get(
                f"{self.premium_base_url}/search",
                headers={"Authorization": f"Bearer {token}", "X-API-Key": self.api_key},
                params=params,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    feature = data["features"][0]
                    props = feature.get("properties", {})
                    coords = feature.get("geometry", {}).get("coordinates", [])

                    if len(coords) >= 2:
                        return {
                            "latitude": coords[1],
                            "longitude": coords[0],
                            "formatted_address": props.get("label", ""),
                            "confidence": props.get("score", 0.95),  # Premium has higher confidence
                            "city": props.get("city", ""),
                            "postcode": props.get("postcode", ""),
                            "department": props.get("context", "").split(",")[0].strip(),
                            "type": props.get("type", ""),
                            "importance": props.get("importance", 0),
                            # Premium-specific fields
                            "housenumber": props.get("housenumber", ""),
                            "street": props.get("street", ""),
                            "locality": props.get("locality", ""),
                            "district": props.get("district", ""),
                            "oldcity": props.get("oldcity", ""),  # Historical name
                            "oldstreet": props.get("oldstreet", ""),  # Historical street
                            "entrance": props.get("entrance", ""),  # Building entrance
                            "quality": props.get("quality", ""),  # Data quality indicator
                            "precision": "premium",
                        }
            else:
                self.logger.error(f"Premium geocoding failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Premium geocoding error for '{address}': {e}")

        return None

    @lru_cache(maxsize=2000)
    def reverse_geocode_premium(self, lat: float, lon: float, zoom: int = 18) -> Optional[Dict]:
        """
        Premium reverse geocoding with detailed results

        Zoom levels:
        - 18: Building/entrance level
        - 16: Street level
        - 14: Locality level
        - 10: City level
        """
        if not self.enabled:
            return None

        token = self._get_auth_token()
        if not token:
            return None

        self._rate_limit()

        try:
            response = requests.get(
                f"{self.premium_base_url}/reverse",
                headers={"Authorization": f"Bearer {token}", "X-API-Key": self.api_key},
                params={"lon": lon, "lat": lat, "zoom": zoom, "type": "housenumber,street,locality,municipality"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    feature = data["features"][0]
                    props = feature.get("properties", {})

                    return {
                        "address": props.get("label", ""),
                        "housenumber": props.get("housenumber", ""),
                        "street": props.get("street", ""),
                        "locality": props.get("locality", ""),
                        "city": props.get("city", ""),
                        "postcode": props.get("postcode", ""),
                        "type": props.get("type", ""),
                        "distance": props.get("distance", 0),  # Distance from query point
                        "precision": "premium",
                    }

        except Exception as e:
            self.logger.error(f"Premium reverse geocoding error: {e}")

        return None

    def batch_geocode_premium(self, addresses: List[str], filters: Optional[Dict] = None) -> List[Optional[Dict]]:
        """
        Batch geocoding for multiple addresses
        Premium API supports batch operations for efficiency
        """
        if not self.enabled or not addresses:
            return [None] * len(addresses)

        token = self._get_auth_token()
        if not token:
            return [None] * len(addresses)

        results = []
        batch_size = 50  # Premium allows larger batches

        for i in range(0, len(addresses), batch_size):
            batch = addresses[i : i + batch_size]
            self._rate_limit()

            try:
                # Premium batch endpoint
                response = requests.post(
                    f"{self.premium_base_url}/batch",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={"queries": [{"q": addr} for addr in batch], "filters": filters or {}},
                    timeout=30,
                )

                if response.status_code == 200:
                    batch_data = response.json()
                    for result in batch_data.get("results", []):
                        if result.get("features"):
                            feature = result["features"][0]
                            props = feature.get("properties", {})
                            coords = feature.get("geometry", {}).get("coordinates", [])

                            if len(coords) >= 2:
                                results.append(
                                    {
                                        "latitude": coords[1],
                                        "longitude": coords[0],
                                        "formatted_address": props.get("label", ""),
                                        "confidence": props.get("score", 0.95),
                                        "precision": "premium",
                                    }
                                )
                            else:
                                results.append(None)
                        else:
                            results.append(None)
                else:
                    # Fallback to individual requests
                    for addr in batch:
                        results.append(self.geocode_premium(addr, filters))

            except Exception as e:
                self.logger.error(f"Batch geocoding error: {e}")
                # Fallback to individual requests
                for addr in batch:
                    results.append(self.geocode_premium(addr, filters))

        return results

    def search_poi_premium(self, query: str, lat: float, lon: float, radius: int = 1000) -> List[Dict]:
        """
        Search for Points of Interest near a location
        Premium feature for finding named places
        """
        if not self.enabled:
            return []

        token = self._get_auth_token()
        if not token:
            return []

        self._rate_limit()

        try:
            response = requests.get(
                f"{self.premium_base_url}/poi",
                headers={"Authorization": f"Bearer {token}", "X-API-Key": self.api_key},
                params={"q": query, "lat": lat, "lon": lon, "radius": radius, "limit": 20},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                places = []

                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    coords = feature.get("geometry", {}).get("coordinates", [])

                    if len(coords) >= 2:
                        places.append(
                            {
                                "name": props.get("name", ""),
                                "latitude": coords[1],
                                "longitude": coords[0],
                                "type": props.get("type", ""),
                                "subtype": props.get("subtype", ""),
                                "distance": props.get("distance", 0),
                                "address": props.get("address", ""),
                                "precision": "premium",
                            }
                        )

                return places

        except Exception as e:
            self.logger.error(f"POI search error: {e}")

        return []
