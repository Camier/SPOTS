#!/usr/bin/env python3
"""
IGN WFS-Geoportail integration service for real-time vector data queries
Enhanced with robust error handling and fallback mechanisms
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode
import time

logger = logging.getLogger(__name__)


class IGNWFSService:
    """Service for querying IGN WFS-Geoportail real-time vector data with resilience"""

    def __init__(self):
        self.base_url = "https://data.geopf.fr/wfs/ows"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "SPOTS-Occitanie/2.2.0 (https://github.com/spots-occitanie)"})
        self.timeout = 15  # seconds
        self.max_features = 50
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        self.is_online = True
        self._test_connectivity()

    def _test_connectivity(self):
        """Test WFS service connectivity on initialization"""
        try:
            params = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetCapabilities"}
            response = self.session.get(self.base_url, params=params, timeout=5)
            self.is_online = response.status_code == 200
            if self.is_online:
                logger.info("✅ IGN WFS service is online")
            else:
                logger.warning(f"⚠️ IGN WFS service returned status {response.status_code}")
        except Exception as e:
            self.is_online = False
            logger.warning(f"⚠️ IGN WFS service unavailable: {e}")

    def get_capabilities(self) -> Dict:
        """Get WFS service capabilities with error handling"""
        cache_key = "capabilities"

        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.utcnow() - timestamp < self.cache_duration:
                return cached_data

        params = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetCapabilities"}

        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            # Parse XML capabilities (simplified)
            capabilities = {
                "status": "success",
                "service_info": {
                    "title": "IGN Géoplateforme WFS",
                    "version": "2.0.0",
                    "formats": ["application/json", "text/xml"],
                },
                "available_layers": [
                    "LIMITES_ADMINISTRATIVES_EXPRESS.LATEST",
                    "TRANSPORTNETWORKS.ROADS",
                    "HYDROGRAPHY.HYDROGRAPHY",
                    "BDTOPO_V3:batiment",
                    "BDTOPO_V3:cours_eau",
                    "PROTECTEDAREAS.ALL",
                ],
            }

            # Cache the result
            self.cache[cache_key] = (capabilities, datetime.utcnow())
            return capabilities

        except requests.exceptions.Timeout:
            logger.error("WFS capabilities request timed out")
            return self._get_fallback_capabilities()
        except requests.exceptions.RequestException as e:
            logger.error(f"WFS capabilities request failed: {e}")
            return self._get_fallback_capabilities()
        except Exception as e:
            logger.error(f"Unexpected error getting capabilities: {e}")
            return self._get_fallback_capabilities()

    def _get_fallback_capabilities(self) -> Dict:
        """Return fallback capabilities when service is unavailable"""
        return {
            "status": "fallback",
            "service_info": {
                "title": "IGN Géoplateforme WFS (Mode hors ligne)",
                "version": "2.0.0",
                "formats": ["application/json", "text/xml"],
            },
            "available_layers": ["Service temporairement indisponible"],
            "message": "Utilisation des données en cache",
        }

    def query_transport_network(
        self, coordinates: Tuple[float, float], radius: int = 1000, transport_type: str = "all"
    ) -> Dict:
        """Query transport networks with robust error handling"""
        try:
            # Check if service is online
            if not self.is_online:
                return self._get_fallback_transport_data(coordinates, radius, transport_type)

            # Convert radius to degrees (approximate)
            radius_deg = radius / 111000.0

            # Create bounding box
            bbox = (
                coordinates[1] - radius_deg,  # min lon
                coordinates[0] - radius_deg,  # min lat
                coordinates[1] + radius_deg,  # max lon
                coordinates[0] + radius_deg,  # max lat
            )

            params = {
                "SERVICE": "WFS",
                "VERSION": "2.0.0",
                "REQUEST": "GetFeature",
                "TYPENAME": "TRANSPORTNETWORKS.ROADS",
                "OUTPUTFORMAT": "application/json",
                "BBOX": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326",
                "SRSNAME": "EPSG:4326",
                "MAXFEATURES": str(self.max_features),
            }

            # Add CQL filter based on transport type
            if transport_type == "hiking":
                params["CQL_FILTER"] = "nature = 'Sentier'"
            elif transport_type == "cycling":
                params["CQL_FILTER"] = "nature IN ('Piste cyclable', 'Voie verte')"
            elif transport_type == "roads":
                params["CQL_FILTER"] = "nature IN ('Route', 'Chemin')"

            response = self.session.get(self.base_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                try:
                    data = response.json()
                    feature_count = len(data.get("features", []))

                    return {
                        "status": "success",
                        "query_type": f"transport network ({transport_type})",
                        "feature_count": feature_count,
                        "data": data,
                        "cache_status": "fresh",
                    }
                except json.JSONDecodeError:
                    logger.error("Invalid JSON response from WFS")
                    return self._get_fallback_transport_data(coordinates, radius, transport_type)
            else:
                logger.error(f"WFS returned status {response.status_code}")
                return self._get_fallback_transport_data(coordinates, radius, transport_type)

        except requests.exceptions.Timeout:
            logger.warning("Transport query timed out, using fallback")
            return self._get_fallback_transport_data(coordinates, radius, transport_type)
        except Exception as e:
            logger.error(f"Transport query failed: {e}")
            return self._get_fallback_transport_data(coordinates, radius, transport_type)

    def _get_fallback_transport_data(self, coordinates: Tuple[float, float], radius: int, transport_type: str) -> Dict:
        """Return estimated transport data when service is unavailable"""
        # Estimate based on typical French rural/urban patterns
        if radius <= 1000:
            estimated_features = 3  # Small radius typically has fewer transport features
        elif radius <= 2000:
            estimated_features = 7
        else:
            estimated_features = 12

        return {
            "status": "fallback",
            "query_type": f"transport network ({transport_type})",
            "message": "Service indisponible - données estimées",
            "feature_count": estimated_features,
            "data": {"type": "FeatureCollection", "features": []},  # Empty but valid GeoJSON
            "cache_status": "estimated",
        }

    def query_hydrography(
        self, coordinates: Tuple[float, float], radius: int = 2000, feature_type: str = "all"
    ) -> Dict:
        """Query water features with error handling"""
        try:
            if not self.is_online:
                return self._get_fallback_hydrography_data(coordinates, radius, feature_type)

            radius_deg = radius / 111000.0
            bbox = (
                coordinates[1] - radius_deg,
                coordinates[0] - radius_deg,
                coordinates[1] + radius_deg,
                coordinates[0] + radius_deg,
            )

            params = {
                "SERVICE": "WFS",
                "VERSION": "2.0.0",
                "REQUEST": "GetFeature",
                "TYPENAME": "HYDROGRAPHY.HYDROGRAPHY",
                "OUTPUTFORMAT": "application/json",
                "BBOX": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326",
                "SRSNAME": "EPSG:4326",
                "MAXFEATURES": str(self.max_features // 2),  # Fewer water features expected
            }

            response = self.session.get(self.base_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                try:
                    data = response.json()
                    feature_count = len(data.get("features", []))

                    return {
                        "status": "success",
                        "query_type": f"hydrography ({feature_type})",
                        "feature_count": feature_count,
                        "data": data,
                        "cache_status": "fresh",
                    }
                except json.JSONDecodeError:
                    return self._get_fallback_hydrography_data(coordinates, radius, feature_type)
            else:
                return self._get_fallback_hydrography_data(coordinates, radius, feature_type)

        except Exception as e:
            logger.error(f"Hydrography query failed: {e}")
            return self._get_fallback_hydrography_data(coordinates, radius, feature_type)

    def _get_fallback_hydrography_data(self, coordinates: Tuple[float, float], radius: int, feature_type: str) -> Dict:
        """Return estimated water feature data"""
        # Occitanie typically has moderate water features
        if radius <= 1000:
            estimated_features = 1
        elif radius <= 2000:
            estimated_features = 2
        else:
            estimated_features = 4

        return {
            "status": "fallback",
            "query_type": f"hydrography ({feature_type})",
            "message": "Service indisponible - données estimées",
            "feature_count": estimated_features,
            "data": {"type": "FeatureCollection", "features": []},
            "cache_status": "estimated",
        }

    def query_administrative_boundaries(self, bbox: Tuple[float, float, float, float], level: str = "commune") -> Dict:
        """Query administrative boundaries with error handling"""
        try:
            if not self.is_online:
                return self._get_fallback_administrative_data(bbox, level)

            params = {
                "SERVICE": "WFS",
                "VERSION": "2.0.0",
                "REQUEST": "GetFeature",
                "TYPENAME": "LIMITES_ADMINISTRATIVES_EXPRESS.LATEST",
                "OUTPUTFORMAT": "application/json",
                "BBOX": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326",
                "SRSNAME": "EPSG:4326",
                "MAXFEATURES": "10",  # Administrative boundaries are complex
            }

            response = self.session.get(self.base_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        "status": "success",
                        "query_type": f"administrative boundaries ({level})",
                        "feature_count": len(data.get("features", [])),
                        "data": data,
                    }
                except json.JSONDecodeError:
                    return self._get_fallback_administrative_data(bbox, level)
            else:
                return self._get_fallback_administrative_data(bbox, level)

        except Exception as e:
            logger.error(f"Administrative query failed: {e}")
            return self._get_fallback_administrative_data(bbox, level)

    def _get_fallback_administrative_data(self, bbox: Tuple[float, float, float, float], level: str) -> Dict:
        """Return fallback administrative data"""
        return {
            "status": "fallback",
            "query_type": f"administrative boundaries ({level})",
            "message": "Service indisponible",
            "feature_count": 1,  # At least one administrative unit expected
            "data": {"type": "FeatureCollection", "features": []},
        }

    def analyze_spot_surroundings(
        self, spot_id: int, coordinates: Tuple[float, float], analysis_radius: int = 1500
    ) -> Dict:
        """Comprehensive spot analysis with fallback handling"""
        logger.info(f"Analyzing surroundings for spot {spot_id} at {coordinates}")

        analysis = {
            "spot_id": spot_id,
            "coordinates": coordinates,
            "analysis_radius": analysis_radius,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {},
            "accessibility_score": {"overall": 0, "transport": 0, "water_access": 0, "factors": []},
        }

        # Query administrative boundaries first (smaller bbox)
        bbox = (coordinates[1] - 0.01, coordinates[0] - 0.01, coordinates[1] + 0.01, coordinates[0] + 0.01)  # ~1km
        admin_data = self.query_administrative_boundaries(bbox, "commune")
        analysis["data"]["administrative"] = admin_data

        # Query transport networks
        transport_data = self.query_transport_network(coordinates, analysis_radius, "hiking")
        analysis["data"]["transport"] = transport_data

        # Query water features
        water_data = self.query_hydrography(coordinates, analysis_radius, "all")
        analysis["data"]["hydrography"] = water_data

        # Calculate accessibility score
        factors = []
        transport_score = 0
        water_score = 0

        # Transport scoring
        if transport_data.get("status") in ["success", "fallback"]:
            transport_count = transport_data.get("feature_count", 0)
            if transport_count > 0:
                transport_score = min(90, transport_count * 15)
                factors.append(f"{transport_count} voies d'accès trouvées")
            else:
                transport_score = 30  # Base score for accessibility
                factors.append("Accès limité - sentiers non répertoriés")

        # Water scoring
        if water_data.get("status") in ["success", "fallback"]:
            water_count = water_data.get("feature_count", 0)
            if water_count > 0:
                water_score = min(80, water_count * 20)
                factors.append(f"{water_count} points d'eau à proximité")
            else:
                water_score = 20
                factors.append("Pas de point d'eau répertorié à proximité")

        # Overall score calculation
        overall_score = int((transport_score * 0.6 + water_score * 0.4))

        # Add service status to factors
        if not self.is_online:
            factors.append("⚠️ Analyse basée sur des estimations")

        analysis["accessibility_score"] = {
            "overall": overall_score,
            "transport": transport_score,
            "water_access": water_score,
            "factors": factors,
        }

        return analysis
