"""Processing provider for SPOTS plugin algorithms."""

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from pathlib import Path


class SpotsProcessingProvider(QgsProcessingProvider):
    """Processing provider for SPOTS algorithms."""
    
    def __init__(self):
        """Initialize the provider."""
        super().__init__()
    
    def id(self):
        """Return the unique provider ID."""
        return 'spots'
    
    def name(self):
        """Return the provider name."""
        return 'SPOTS Tools'
    
    def icon(self):
        """Return the provider icon."""
        icon_path = Path(__file__).parent.parent / 'icons' / 'spots.png'
        if icon_path.exists():
            return QIcon(str(icon_path))
        return super().icon()
    
    def loadAlgorithms(self):
        """Load algorithms into the provider."""
        # Add algorithms here as they are developed
        # Example:
        # from .algorithms.spot_density import SpotDensityAlgorithm
        # self.addAlgorithm(SpotDensityAlgorithm())
        pass
    
    def longName(self):
        """Return the full provider name."""
        return 'SPOTS - Hidden Outdoor Spots Explorer Processing Tools'