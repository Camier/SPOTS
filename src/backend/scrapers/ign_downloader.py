#!/usr/bin/env python3
"""
IGN Dataset Downloader - Compatibility wrapper
This module now imports from the refactored modules for backward compatibility
"""

# Import everything from the refactored modules
from .ign_config import *
from .ign_geo_utils import *
from .ign_downloaders import *
from .ign_downloader_refactored import (
    IGNDatasetDownloader,
    download_ign_dataset,
    list_ign_datasets
)

# Maintain backward compatibility
__all__ = [
    'IGNDatasetDownloader',
    'download_ign_dataset', 
    'list_ign_datasets',
    'WFS_BASE_URL',
    'WMS_BASE_URL',
    'DOWNLOAD_BASE_URL',
    'ATOM_FEED_URL',
    'API_KEYS',
    'DATASETS',
    'RASTER_RESOLUTION',
    'OCCITANIE_BOUNDS',
    'OCCITANIE_DEPARTMENTS'
]