#!/usr/bin/env python3
"""
IGN Dataset Downloader - Refactored main class
Downloads IGN open data datasets using modular components
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from src.backend.core.logging_config import logger

from .ign_config import DATASETS, OCCITANIE_BOUNDS
from .ign_downloaders import download_wfs, download_wms, download_direct


class IGNDatasetDownloader:
    """Download IGN datasets from various sources"""

    def __init__(self, download_dir: str = None, target_epsg: int = 3857):
        """Initialize IGN dataset downloader

        Args:
            download_dir: Directory to save downloaded files
            target_epsg: Target EPSG code for reprojection (default: 3857 - Web Mercator)
        """
        self.download_dir = Path(download_dir or "data/ign_downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.target_epsg = target_epsg

    def list_datasets(self, category: str = None) -> List[Dict]:
        """List available datasets

        Args:
            category: Filter by category (administrative, elevation, etc.)

        Returns:
            List of dataset information
        """
        datasets = []
        for dataset_id, info in DATASETS.items():
            if category and category not in info.get("service", ""):
                continue
            datasets.append(
                {
                    "id": dataset_id,
                    "name": info["name"],
                    "description": info["description"],
                    "service": info["service"],
                    "formats": info["formats"],
                }
            )
        return datasets

    def download_dataset(
        self,
        dataset_id: str,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        format: str = "geojson",
        output_file: Optional[str] = None,
    ) -> Path:
        """Download IGN dataset

        Args:
            dataset_id: Dataset identifier (e.g., "ADMINEXPRESS-COG-CARTO.LATEST:commune")
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
            format: Output format (geojson, shp, gml, etc.)
            output_file: Optional output filename

        Returns:
            Path to downloaded file

        Example:
            download_dataset(
                "ADMINEXPRESS-COG-CARTO.LATEST:commune",
                bbox=[1.2, 43.5, 1.5, 43.7],  # Toulouse
                format="geojson"
            )
        """
        if dataset_id not in DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_id}")

        dataset_info = DATASETS[dataset_id]

        if format not in dataset_info["formats"]:
            raise ValueError(f"Format {format} not supported for {dataset_id}")

        # Route to appropriate download method
        if dataset_info["type"] == "wfs":
            return download_wfs(
                dataset_id, bbox, format, output_file, 
                self.download_dir, self.target_epsg
            )
        elif dataset_info["type"] == "wms":
            return download_wms(
                dataset_id, bbox, format, output_file, 
                self.download_dir
            )
        elif dataset_info["type"] == "download":
            return download_direct(
                dataset_id, bbox, format, output_file, 
                self.download_dir
            )
        else:
            raise ValueError(f"Unknown download type: {dataset_info['type']}")

    def download_occitanie_boundaries(self, level: str = "departement") -> Path:
        """Download administrative boundaries for Occitanie region

        Args:
            level: Administrative level (commune, departement, region)

        Returns:
            Path to downloaded file
        """
        dataset_id = f"ADMINEXPRESS-COG-CARTO.LATEST:{level}"

        return self.download_dataset(
            dataset_id=dataset_id,
            bbox=OCCITANIE_BOUNDS,
            format="geojson",
            output_file=f"occitanie_{level}s.geojson"
        )

    def download_elevation_tiles(self, bbox: Tuple[float, float, float, float]) -> List[Path]:
        """Download elevation tiles for a given bbox

        Args:
            bbox: Bounding box

        Returns:
            List of downloaded tile paths
        """
        # This would download RGE ALTI tiles
        # For now, create placeholder
        tiles = []
        tile_path = self.download_dir / f"elevation_{bbox[0]}_{bbox[1]}.asc"
        tile_path.touch()
        tiles.append(tile_path)

        logger.info(f"Downloaded {len(tiles)} elevation tiles")
        return tiles


# Convenience functions
def download_ign_dataset(dataset_id: str, **kwargs) -> Path:
    """Quick download function

    Examples:
        # Download Toulouse communes
        download_ign_dataset(
            "ADMINEXPRESS-COG-CARTO.LATEST:commune",
            bbox=[1.2, 43.5, 1.5, 43.7],
            format="geojson"
        )

        # Download all Occitanie departments
        download_ign_dataset(
            "ADMINEXPRESS-COG-CARTO.LATEST:departement",
            bbox=[-0.5, 42.5, 4.5, 45.0],
            format="shp"
        )
    """
    downloader = IGNDatasetDownloader()
    return downloader.download_dataset(dataset_id, **kwargs)


def list_ign_datasets(category: str = None) -> None:
    """List available IGN datasets"""
    downloader = IGNDatasetDownloader()
    datasets = downloader.list_datasets(category)

    logger.info(f"\nAvailable IGN Datasets{f' ({category})' if category else ''}:")
    logger.info("-" * 80)

    for dataset in datasets:
        logger.info(f"\nID: {dataset['id']}")
        logger.info(f"Name: {dataset['name']}")
        logger.info(f"Description: {dataset['description']}")
        logger.info(f"Formats: {', '.join(dataset['formats'])}")
        logger.info(f"Service: {dataset['service']}")


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Download IGN datasets")
    parser.add_argument("--list", action="store_true", help="List available datasets")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--dataset", help="Dataset ID to download")
    parser.add_argument("--bbox", nargs=4, type=float, 
                       metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"))
    parser.add_argument("--format", default="geojson", help="Output format")
    parser.add_argument("--output", help="Output filename")

    args = parser.parse_args()

    if args.list:
        list_ign_datasets(args.category)
    elif args.dataset:
        downloader = IGNDatasetDownloader()
        path = downloader.download_dataset(
            args.dataset,
            bbox=tuple(args.bbox) if args.bbox else None,
            format=args.format,
            output_file=args.output
        )
        logger.info(f"Downloaded to: {path}")
    else:
        # Show examples
        logger.info("\nExamples:")
        logger.info("  # List all datasets:")
        logger.info("  python ign_downloader_refactored.py --list")
        logger.info("\n  # Download Toulouse communes:")
        logger.info("  python ign_downloader_refactored.py --dataset ADMINEXPRESS-COG-CARTO.LATEST:commune --bbox 1.2 43.5 1.5 43.7")
        logger.info("\n  # Download Occitanie departments as shapefile:")
        logger.info("  python ign_downloader_refactored.py --dataset ADMINEXPRESS-COG-CARTO.LATEST:departement --bbox -0.5 42.5 4.5 45.0 --format shp")