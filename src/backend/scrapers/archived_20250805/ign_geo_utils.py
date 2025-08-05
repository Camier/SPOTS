#!/usr/bin/env python3
"""
IGN Geographic Utilities - Coordinate transformations and spatial calculations
"""

import math
from typing import Tuple, Optional
from pathlib import Path
from src.backend.core.logging_config import logger

try:
    from osgeo import gdal, ogr, osr
    GDAL_AVAILABLE = True
except ImportError:
    GDAL_AVAILABLE = False
    logger.warning("GDAL not available. Install with: pip install GDAL")


def reproject_bbox(
    bbox: Tuple[float, float, float, float], 
    source_epsg: int, 
    target_epsg: int
) -> Tuple[float, float, float, float]:
    """Reproject bounding box coordinates

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        source_epsg: Source EPSG code
        target_epsg: Target EPSG code

    Returns:
        Reprojected bbox
    """
    if not GDAL_AVAILABLE:
        logger.warning("GDAL not available, returning original bbox")
        return bbox

    # Create coordinate transformation
    source = osr.SpatialReference()
    source.ImportFromEPSG(source_epsg)

    target = osr.SpatialReference()
    target.ImportFromEPSG(target_epsg)

    transform = osr.CoordinateTransformation(source, target)

    # Transform corners
    min_x, min_y, _ = transform.TransformPoint(bbox[0], bbox[1])
    max_x, max_y, _ = transform.TransformPoint(bbox[2], bbox[3])

    return (min_x, min_y, max_x, max_y)


def get_bbox_in_meters(bbox: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    """Convert bbox to meters (Web Mercator)

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat) in WGS84

    Returns:
        Bbox in meters
    """
    return reproject_bbox(bbox, 4326, 3857)


def reproject_geojson(geojson_path: Path, target_epsg: int = 3857) -> Path:
    """Reproject a GeoJSON file to target EPSG

    Args:
        geojson_path: Path to input GeoJSON
        target_epsg: Target EPSG (default: 3857 - Web Mercator)

    Returns:
        Path to reprojected file
    """
    if not GDAL_AVAILABLE:
        logger.warning("GDAL not available, skipping reprojection")
        return geojson_path

    # Skip if already in target projection
    if target_epsg == 4326:
        return geojson_path

    # Output path
    output_path = geojson_path.parent / f"{geojson_path.stem}_epsg{target_epsg}.geojson"

    # Open source dataset
    driver = ogr.GetDriverByName("GeoJSON")
    source_ds = driver.Open(str(geojson_path))
    source_layer = source_ds.GetLayer()

    # Get source SRS (assume WGS84 if not specified)
    source_srs = source_layer.GetSpatialRef()
    if not source_srs:
        source_srs = osr.SpatialReference()
        source_srs.ImportFromEPSG(4326)

    # Create target SRS
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(target_epsg)

    # Create transformation
    transform = osr.CoordinateTransformation(source_srs, target_srs)

    # Create output dataset
    output_ds = driver.CreateDataSource(str(output_path))
    output_layer = output_ds.CreateLayer(
        source_layer.GetName(), 
        target_srs, 
        source_layer.GetGeomType()
    )

    # Copy fields
    layer_defn = source_layer.GetLayerDefn()
    for i in range(layer_defn.GetFieldCount()):
        field_defn = layer_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    # Copy and transform features
    output_layer_defn = output_layer.GetLayerDefn()
    for feature in source_layer:
        # Clone feature
        output_feature = ogr.Feature(output_layer_defn)

        # Copy attributes
        for i in range(layer_defn.GetFieldCount()):
            output_feature.SetField(i, feature.GetField(i))

        # Transform geometry
        geom = feature.GetGeometryRef()
        if geom:
            geom_clone = geom.Clone()
            geom_clone.Transform(transform)
            output_feature.SetGeometry(geom_clone)

        # Add to output
        output_layer.CreateFeature(output_feature)
        output_feature = None

    # Clean up
    source_ds = None
    output_ds = None

    logger.info(f"Reprojected to EPSG:{target_epsg} -> {output_path}")
    return output_path


def get_departments_in_bbox(bbox: Tuple[float, float, float, float]) -> list[str]:
    """Get department codes that intersect with bbox
    
    Simplified version - in reality would query administrative boundaries
    """
    try:
        from .ign_config import OCCITANIE_DEPARTMENTS
    except ImportError:
        from ign_config import OCCITANIE_DEPARTMENTS
    
    # Rough estimation based on bbox center
    center_lon = (bbox[0] + bbox[2]) / 2
    center_lat = (bbox[1] + bbox[3]) / 2

    if 43.5 < center_lat < 43.7 and 1.3 < center_lon < 1.5:
        return ["31"]  # Haute-Garonne (Toulouse)
    elif center_lat < 43:
        return ["09", "11", "66"]  # Pyrénées departments
    else:
        return ["31", "81", "82"]  # North Occitanie