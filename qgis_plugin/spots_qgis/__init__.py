"""
SPOTS QGIS Plugin
Integrates hidden outdoor spots database with QGIS
"""

def classFactory(iface):
    """
    Load SpotsPlugin class from file spots_plugin.py
    
    :param iface: A QGIS interface instance
    :type iface: QgsInterface
    """
    from .spots_plugin import SpotsPlugin
    return SpotsPlugin(iface)