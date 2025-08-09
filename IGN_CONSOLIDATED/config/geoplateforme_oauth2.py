#!/usr/bin/env python3
"""Configure OAuth2 authentication for Géoplateforme in QGIS."""

from qgis.core import QgsAuthMethodConfig, QgsApplication, QgsAuthManager
from qgis.PyQt.QtCore import QSettings
import json

def setup_geoplateforme_oauth2():
    """Set up OAuth2 authentication for Géoplateforme."""
    
    auth_manager = QgsApplication.authManager()
    
    # Create OAuth2 configuration
    auth_config = QgsAuthMethodConfig()
    auth_config.setName("Géoplateforme OAuth2")
    auth_config.setMethod("OAuth2")
    
    # OAuth2 settings for Géoplateforme
    oauth2_config = {
        "version": 2,
        "grant_flow": 0,  # Authorization Code
        "auth_endpoint": "https://auth.cartes.gouv.fr/oauth2/authorize",
        "token_endpoint": "https://auth.cartes.gouv.fr/oauth2/token",
        "redirect_url": "http://127.0.0.1:7070",
        "client_id": "YOUR_CLIENT_ID",  # Replace with actual
        "client_secret": "YOUR_CLIENT_SECRET",  # Replace with actual
        "scope": "openid profile",
        "persistent_session": True,
        "access_method": 0,  # Header
        "request_timeout": 30
    }
    
    auth_config.setConfig("oauth2config", json.dumps(oauth2_config))
    
    # Store the configuration
    auth_id = "GEOPF01"
    if auth_manager.storeAuthenticationConfig(auth_config):
        print(f"✅ OAuth2 configuration stored with ID: {auth_id}")
        return auth_id
    else:
        print("❌ Failed to store OAuth2 configuration")
        return None

def create_service_connections(auth_id):
    """Create connections to Géoplateforme services."""
    
    settings = QSettings()
    
    # WMTS Connection for private data
    wmts_url = "https://data.geopf.fr/private/wmts"
    settings.setValue(f"qgis/connections-wmts/Géoplateforme Private/url", wmts_url)
    settings.setValue(f"qgis/connections-wmts/Géoplateforme Private/authcfg", auth_id)
    
    # WMS Connection for raster data
    wms_url = "https://data.geopf.fr/private/wms-r"
    settings.setValue(f"qgis/connections-wms/Géoplateforme Private/url", wms_url)
    settings.setValue(f"qgis/connections-wms/Géoplateforme Private/authcfg", auth_id)
    
    # Public services (no auth needed)
    public_wmts = "https://data.geopf.fr/wmts"
    settings.setValue(f"qgis/connections-wmts/Géoplateforme Public/url", public_wmts)
    
    print("✅ Service connections configured")
    print("   - Private WMTS: " + wmts_url)
    print("   - Private WMS: " + wms_url)
    print("   - Public WMTS: " + public_wmts)

if __name__ == "__main__":
    # Initialize QGIS
    from qgis.core import QgsApplication
    import sys
    
    QgsApplication.setPrefixPath("/usr", True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    # Set up authentication
    auth_id = setup_geoplateforme_oauth2()
    if auth_id:
        create_service_connections(auth_id)
    
    qgs.exitQgis()