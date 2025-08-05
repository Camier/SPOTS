#!/usr/bin/env python3
"""
IGN Download Methods - Specialized downloaders for different IGN services
"""

import os
import requests
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from src.backend.core.logging_config import logger

from .ign_config import (
    WFS_BASE_URL, WMS_BASE_URL, DOWNLOAD_BASE_URL,
    API_KEYS, DATASETS, RASTER_RESOLUTION
)
from .ign_geo_utils import reproject_bbox, get_bbox_in_meters, reproject_geojson


def download_wfs(
    dataset_id: str,
    bbox: Optional[Tuple[float, float, float, float]],
    format: str,
    output_file: Optional[str],
    download_dir: Path,
    target_epsg: int = 3857
) -> Path:
    """Download data via WFS service"""
    
    dataset_info = DATASETS[dataset_id]
    api_key = API_KEYS.get(dataset_info["service"], "essentiels")

    # Build WFS request
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAME": dataset_id,
        "SRSNAME": f"EPSG:{target_epsg}",  # Request data in target projection
    }

    # Add format
    if format == "geojson":
        params["OUTPUTFORMAT"] = "application/json"
    elif format == "shp":
        params["OUTPUTFORMAT"] = "SHAPE-ZIP"
    elif format == "gml":
        params["OUTPUTFORMAT"] = "application/gml+xml"

    # Add bbox filter if provided
    if bbox:
        # Convert bbox to target projection if needed
        if target_epsg != 4326:
            bbox_proj = reproject_bbox(bbox, 4326, target_epsg)
            params["BBOX"] = f"{bbox_proj[1]},{bbox_proj[0]},{bbox_proj[3]},{bbox_proj[2]},EPSG:{target_epsg}"
        else:
            params["BBOX"] = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]},EPSG:4326"

    # Make request
    url = WFS_BASE_URL.format(key=api_key)
    logger.info(f"Downloading {dataset_id} from WFS...")

    try:
        response = requests.get(url, params=params, stream=True)
        response.raise_for_status()

        # Determine filename
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "json" if format == "geojson" else format
            output_file = f"{dataset_id.replace(':', '_')}_{timestamp}.{ext}"

        output_path = download_dir / output_file

        # Handle zip files (shapefiles)
        if format == "shp" and response.headers.get("content-type") == "application/zip":
            # Save zip temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name

            # Extract zip
            extract_dir = output_path.with_suffix("")
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(tmp_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            os.unlink(tmp_path)
            logger.info(f"Extracted shapefile to {extract_dir}")
            return extract_dir
        else:
            # Save directly
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded to {output_path}")

            # Reproject if GeoJSON and not already in target projection
            if format == "geojson" and target_epsg != 4326:
                output_path = reproject_geojson(output_path, target_epsg)

            return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {dataset_id}: {e}")
        raise


def download_wms(
    dataset_id: str,
    bbox: Tuple[float, float, float, float],
    format: str,
    output_file: Optional[str],
    download_dir: Path
) -> Path:
    """Download data via WMS service (for raster layers)"""
    
    if not bbox:
        raise ValueError("Bbox required for WMS downloads")

    dataset_info = DATASETS[dataset_id]
    api_key = API_KEYS.get(dataset_info["service"], "essentiels")

    # Calculate image size based on bbox and resolution
    bbox_meters = get_bbox_in_meters(bbox)
    width_m = bbox_meters[2] - bbox_meters[0]
    height_m = bbox_meters[3] - bbox_meters[1]

    # Calculate pixel dimensions based on standard resolution
    width = int(width_m / RASTER_RESOLUTION)
    height = int(height_m / RASTER_RESOLUTION)

    # Limit size for WMS requests
    width = min(width, 4096)
    height = min(height, 4096)

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": dataset_id,
        "CRS": "EPSG:4326",
        "BBOX": f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}",
        "WIDTH": width,
        "HEIGHT": height,
        "FORMAT": f"image/{format}",
    }

    url = WMS_BASE_URL.format(key=api_key)

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{dataset_id.replace(':', '_')}_{timestamp}.{format}"

        output_path = download_dir / output_file

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Downloaded WMS image to {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading WMS {dataset_id}: {e}")
        raise


def download_direct(
    dataset_id: str,
    bbox: Optional[Tuple[float, float, float, float]],
    format: str,
    output_file: Optional[str],
    download_dir: Path
) -> Path:
    """Download via direct download service (for large datasets)"""
    
    from .ign_geo_utils import get_departments_in_bbox
    
    # For RGE ALTI and other large datasets, we need department codes
    if dataset_id == "RGEALTI" and bbox:
        # Determine which departments intersect the bbox
        departments = get_departments_in_bbox(bbox)
        logger.info(f"Downloading RGE ALTI for departments: {departments}")

        # This would typically use the IGN download service
        # For now, return a placeholder
        output_path = download_dir / f"rgealti_{departments[0]}.{format}"
        output_path.touch()

        logger.info(f"RGE ALTI download initiated for {departments}")
        return output_path
    else:
        raise NotImplementedError(f"Direct download not implemented for {dataset_id}")