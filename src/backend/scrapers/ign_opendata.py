#!/usr/bin/env python3
"""
IGN OpenData Integration for SPOTS Project
Fetches and processes French geographic datasets to enrich spot information
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point, Polygon
import rasterio
from rasterio.mask import mask
import numpy as np
from src.backend.core.logging_config import logger
from src.backend.validators.real_data_validator import enforce_real_data

logger = logging.getLogger(__name__)


class IGNOpenDataService:
    """Service for integrating IGN France OpenData datasets"""

    # Base URLs for different datasets
    DATASETS = {
        "bd_foret": {
            "name": "BD Forêt",
            "description": "Forest coverage and types",
            "base_url": "https://wxs.ign.fr/forestier/telechargement/prepackage/BDFORET-PACK_2-0__SHP_LAMB93_{dept}_{year}/file/BDFORET-PACK_2-0__SHP_LAMB93_{dept}_{year}.7z",
            "format": "shp",
            "projection": "EPSG:2154",  # Lambert 93
        },
        "rgealti": {
            "name": "RGE ALTI",
            "description": "High-resolution altitude data",
            "base_url": "https://wxs.ign.fr/altimetrie/telechargement/prepackage/RGEALTI_PACK_{resolution}M_{dept}/file/RGEALTI_{resolution}M_{dept}.7z",
            "format": "asc",
            "projection": "EPSG:2154",
            "resolutions": ["1", "5", "25"],  # meters
        },
        "dnsb_haies": {
            "name": "DNSB-Haies",
            "description": "Hedgerows and landscape features",
            "base_url": "https://wxs.ign.fr/environnement/telechargement/prepackage/DNSB-HAIES-PACK_{dept}/file/DNSB-HAIES_{dept}.7z",
            "format": "shp",
            "projection": "EPSG:2154",
        },
        "rpg": {
            "name": "RPG",
            "description": "Agricultural parcels register",
            "base_url": "https://wxs.ign.fr/rpg/telechargement/prepackage/RPG-PACK_{year}_{dept}/file/RPG_{year}_{dept}.7z",
            "format": "shp",
            "projection": "EPSG:2154",
        },
    }

    # Occitanie department codes
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

    def __init__(self, cache_dir: str = "/tmp/ign_data"):
        """Initialize IGN OpenData service"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def analyze_spot_environment(self, lat: float, lon: float, radius: int = 1000) -> Dict:
        """
        Analyze the environment around a spot using IGN data

        Args:
            lat: Latitude of the spot
            lon: Longitude of the spot
            radius: Analysis radius in meters

        Returns:
            Environmental analysis including forest, elevation, land use
        """
        analysis = {
            "coordinates": {"latitude": lat, "longitude": lon},
            "radius_meters": radius,
            "forest": None,
            "elevation": None,
            "terrain": None,
            "land_use": None,
            "accessibility": None,
        }

        try:
            # Convert WGS84 to Lambert 93
            point_lambert = self._transform_coordinates(lat, lon)

            # Analyze forest coverage
            forest_data = self._analyze_forest_coverage(point_lambert, radius)
            if forest_data:
                analysis["forest"] = forest_data

            # Analyze elevation and terrain
            elevation_data = self._analyze_elevation(point_lambert, radius)
            if elevation_data:
                analysis["elevation"] = elevation_data
                analysis["terrain"] = self._calculate_terrain_difficulty(elevation_data)

            # Analyze land use from RPG
            land_use = self._analyze_land_use(point_lambert, radius)
            if land_use:
                analysis["land_use"] = land_use

            # Analyze accessibility (paths, roads from DNSB)
            accessibility = self._analyze_accessibility(point_lambert, radius)
            if accessibility:
                analysis["accessibility"] = accessibility

        except Exception as e:
            logger.error(f"Error analyzing spot environment: {str(e)}")

        return analysis

    def _transform_coordinates(self, lat: float, lon: float) -> Point:
        """Transform WGS84 coordinates to Lambert 93"""
        import pyproj

        transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
        x, y = transformer.transform(lon, lat)
        return Point(x, y)

    def _analyze_forest_coverage(self, point: Point, radius: int) -> Optional[Dict]:
        """Analyze forest coverage around a point"""
        # TODO: Implement actual BD Forêt data loading
        logger.warning("Forest coverage analysis not yet implemented with real data")
        return None  # Return None instead of mock data

    def _analyze_elevation(self, point: Point, radius: int) -> Optional[Dict]:
        """Analyze elevation profile around a point"""
        # TODO: Implement actual RGE ALTI data loading
        logger.warning("Elevation analysis not yet implemented with real data")
        return None  # Return None instead of mock data

    def _calculate_terrain_difficulty(self, elevation_data: Dict) -> Dict:
        """Calculate terrain difficulty based on elevation data"""
        slope = elevation_data.get("slope_average", 0)
        elevation_range = elevation_data.get("elevation_range", 0)
        ruggedness = elevation_data.get("ruggedness_index", 0)

        # Simple difficulty calculation
        difficulty_score = (slope / 45) * 0.4 + (elevation_range / 500) * 0.3 + ruggedness * 0.3

        if difficulty_score < 0.3:
            difficulty = "Easy"
            description = "Gentle terrain, suitable for all levels"
        elif difficulty_score < 0.5:
            difficulty = "Moderate"
            description = "Some elevation changes, basic fitness required"
        elif difficulty_score < 0.7:
            difficulty = "Challenging"
            description = "Steep sections, good fitness required"
        else:
            difficulty = "Expert"
            description = "Very steep and rugged, experienced hikers only"

        return {
            "level": difficulty,
            "score": round(difficulty_score, 2),
            "description": description,
            "factors": {
                "slope": f"{elevation_data.get('slope_average', 0):.1f}°",
                "elevation_gain": f"{elevation_data.get('elevation_range', 0)}m",
                "ruggedness": f"{ruggedness:.2f}",
            },
        }

    def _analyze_land_use(self, point: Point, radius: int) -> Optional[Dict]:
        """Analyze land use from RPG data"""
        # TODO: Implement actual RPG data loading
        logger.warning("Land use analysis not yet implemented with real data")
        return None  # Return None instead of mock data

    def _analyze_accessibility(self, point: Point, radius: int) -> Optional[Dict]:
        """Analyze accessibility using DNSB and other data"""
        # TODO: Implement actual DNSB data loading
        logger.warning("Accessibility analysis not yet implemented with real data")
        return None  # Return None instead of mock data

    def enrich_spot_data(self, spot: Dict) -> Dict:
        """Enrich a spot with IGN OpenData information"""
        if "latitude" not in spot or "longitude" not in spot:
            return spot

        # Get environmental analysis
        env_analysis = self.analyze_spot_environment(spot["latitude"], spot["longitude"], radius=1000)

        # Add enriched data to spot
        spot["environment"] = env_analysis

        # Add summary tags based on analysis
        tags = []

        if env_analysis.get("forest", {}).get("coverage_percent", 0) > 50:
            tags.append("forested")

        terrain = env_analysis.get("terrain", {})
        if terrain.get("level") in ["Challenging", "Expert"]:
            tags.append("challenging_terrain")
        elif terrain.get("level") == "Easy":
            tags.append("easy_access")

        if env_analysis.get("elevation", {}).get("spot_elevation", 0) > 1000:
            tags.append("high_altitude")

        spot["environment_tags"] = tags

        return spot

    def get_map_layers(self) -> Dict[str, str]:
        """Get WMS/WMTS URLs for IGN layers to add to map"""
        return {
            "forest": {
                "name": "Forêts",
                "url": "https://wxs.ign.fr/environnement/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=LANDCOVER.FORESTINVENTORY.V2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN BD Forêt",
                "opacity": 0.6,
                "type": "overlay",
            },
            "elevation_contours": {
                "name": "Courbes de niveau",
                "url": "https://wxs.ign.fr/altimetrie/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ELEVATION.CONTOUR.LINE&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN RGE ALTI",
                "opacity": 0.8,
                "type": "overlay",
            },
            "slopes": {
                "name": "Pentes",
                "url": "https://wxs.ign.fr/altimetrie/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ELEVATION.SLOPES&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png",
                "attribution": "© IGN",
                "opacity": 0.5,
                "type": "overlay",
            },
        }

    def download_department_data(self, dept_code: str, dataset: str, year: str = "2023") -> Optional[Path]:
        """
        Download IGN data for a specific department

        Args:
            dept_code: Department code (e.g., '31')
            dataset: Dataset name from DATASETS
            year: Year for temporal datasets

        Returns:
            Path to downloaded file or None
        """
        if dept_code not in self.OCCITANIE_DEPARTMENTS:
            logger.error(f"Department {dept_code} not in Occitanie")
            return None

        if dataset not in self.DATASETS:
            logger.error(f"Unknown dataset: {dataset}")
            return None

        dataset_info = self.DATASETS[dataset]

        # Build URL
        url = dataset_info["base_url"].format(
            dept=dept_code, year=year, resolution="5"  # Default resolution for RGEALTI
        )

        # Define local path
        filename = Path(url).name
        local_path = self.cache_dir / dataset / dept_code / filename

        if local_path.exists():
            logger.info(f"Using cached file: {local_path}")
            return local_path

        # Download file
        logger.info(f"Downloading {dataset} for department {dept_code}")
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded to: {local_path}")
            return local_path

        except Exception as e:
            logger.error(f"Error downloading {dataset}: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    service = IGNOpenDataService()

    # Example spot in Toulouse area
    spot = {"id": 1, "name": "Cascade secrète", "latitude": 43.6047, "longitude": 1.4442, "type": "waterfall"}

    # Enrich with IGN data
    enriched_spot = service.enrich_spot_data(spot)
    logger.info(json.dumps(enriched_spot, indent=2))

    # Get map layers for frontend
    layers = service.get_map_layers()
    logger.info("\nAvailable map layers:")
    for key, layer in layers.items():
        logger.info(f"- {layer['name']}: {key}")
