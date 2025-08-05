#!/usr/bin/env python3
"""
IGN Configuration - Constants and dataset definitions
"""

# IGN data download endpoints
WFS_BASE_URL = "https://wxs.ign.fr/{key}/geoportail/wfs"
WMS_BASE_URL = "https://wxs.ign.fr/{key}/geoportail/wms"
DOWNLOAD_BASE_URL = "https://geoservices.ign.fr/telechargement"
ATOM_FEED_URL = "https://geoservices.ign.fr/documentation/donnees/atom"

# Common IGN API keys for different services
API_KEYS = {
    "administratif": "administratif",
    "topographie": "topographie",
    "parcellaire": "parcellaire",
    "environnement": "environnement",
    "agriculture": "agriculture",
    "altimetrie": "altimetrie",
    "cartes": "cartes",
    "essentiels": "essentiels",  # General purpose key
}

# Standard resolution for raster data (10m recommended)
RASTER_RESOLUTION = 10  # meters

# Dataset configurations
DATASETS = {
    # Administrative boundaries
    "ADMINEXPRESS-COG-CARTO.LATEST:commune": {
        "name": "Communes (Admin Express)",
        "service": "administratif",
        "type": "wfs",
        "formats": ["geojson", "shp", "gml"],
        "description": "Limites communales de France",
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:departement": {
        "name": "Départements (Admin Express)",
        "service": "administratif",
        "type": "wfs",
        "formats": ["geojson", "shp", "gml"],
        "description": "Limites départementales de France",
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:region": {
        "name": "Régions (Admin Express)",
        "service": "administratif",
        "type": "wfs",
        "formats": ["geojson", "shp", "gml"],
        "description": "Limites régionales de France",
    },
    # Elevation data
    "RGEALTI": {
        "name": "RGE ALTI - Modèle numérique de terrain",
        "service": "altimetrie",
        "type": "download",
        "formats": ["asc", "xyz", "tif"],
        "description": "Données altimétriques haute résolution",
    },
    "ELEVATION.SLOPES": {
        "name": "Pentes",
        "service": "altimetrie",
        "type": "wms",
        "formats": ["png", "jpeg"],
        "description": "Carte des pentes",
    },
    # Hydrography
    "HYDROGRAPHIE.THEME": {
        "name": "Hydrographie",
        "service": "topographie",
        "type": "wfs",
        "formats": ["geojson", "shp"],
        "description": "Réseau hydrographique",
    },
    # Land use
    "LANDCOVER.FORESTINVENTORY.V2": {
        "name": "BD Forêt",
        "service": "environnement",
        "type": "wfs",
        "formats": ["geojson", "shp"],
        "description": "Inventaire forestier",
    },
    # Protected areas
    "PROTECTEDAREAS.ALL": {
        "name": "Zones protégées",
        "service": "environnement",
        "type": "wfs",
        "formats": ["geojson", "shp"],
        "description": "Toutes les zones protégées",
    },
    # Roads and paths
    "BDTOPO_V3:troncon_de_route": {
        "name": "Routes (BD TOPO)",
        "service": "topographie",
        "type": "wfs",
        "formats": ["geojson", "shp"],
        "description": "Réseau routier",
    },
}

# Occitanie region configuration
OCCITANIE_BOUNDS = [-0.5, 42.5, 4.5, 45.0]
OCCITANIE_DEPARTMENTS = ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"]