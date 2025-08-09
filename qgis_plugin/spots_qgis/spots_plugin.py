"""
Main SPOTS QGIS Plugin Class
"""

import os
from pathlib import Path
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon, QAction
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar, QMenu
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsDataSourceUri,
    QgsMessageLog, Qgis, QgsMapLayerType,
    QgsField, QgsFields, QgsWkbTypes, QgsCoordinateReferenceSystem
)
from qgis.gui import QgsMapToolEmitPoint

# Import plugin components
from .core.db_manager import SpotsDBManager
from .core.spot_layer import SpotLayerManager
from .gui.spots_dock import SpotsDockWidget
from .gui.add_spot_dialog import AddSpotDialog
from .processing.provider import SpotsProcessingProvider

class SpotsPlugin:
    """Main SPOTS QGIS Plugin implementation"""
    
    def __init__(self, iface):
        """
        Constructor
        
        :param iface: Interface to QGIS
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'spots_{locale}.qm'
        )
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
            
        # Plugin components
        self.db_manager = None
        self.layer_manager = None
        self.spots_dock = None
        self.processing_provider = None
        
        # Actions
        self.actions = []
        self.menu = self.tr('&SPOTS Explorer')
        self.toolbar = None
        
        # Database path
        self.db_path = Path.home() / "Development/projects/spots/data/occitanie_spots.db"
        
    def tr(self, message):
        """
        Get translated string
        
        :param message: String for translation
        :type message: str
        :returns: Translated version of message
        :rtype: str
        """
        return QCoreApplication.translate('SpotsPlugin', message)
        
    def initGui(self):
        """Create GUI elements"""
        
        # Create toolbar
        self.toolbar = self.iface.addToolBar('SPOTS Explorer')
        self.toolbar.setObjectName('SPOTSToolbar')
        
        # Initialize database manager
        try:
            self.db_manager = SpotsDBManager(str(self.db_path))
            self.layer_manager = SpotLayerManager(self.iface, self.db_manager)
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Failed to initialize database: {e}",
                'SPOTS',
                Qgis.Critical
            )
            
        # Create actions
        self._create_actions()
        
        # Add menu
        self.iface.addPluginToDatabaseMenu(self.menu, self.actions[0])
        
        # Initialize Processing provider
        self.processing_provider = SpotsProcessingProvider()
        QgsApplication.processingRegistry().addProvider(self.processing_provider)
        
        # Create dock widget
        self.spots_dock = SpotsDockWidget(self.iface, self.db_manager)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.spots_dock)
        self.spots_dock.hide()
        
    def _create_actions(self):
        """Create plugin actions"""
        
        # Load Spots Layer action
        icon_path = os.path.join(self.plugin_dir, 'icons', 'load_spots.png')
        action_load = QAction(
            QIcon(icon_path),
            self.tr('Load Spots Layer'),
            self.iface.mainWindow()
        )
        action_load.triggered.connect(self.load_spots_layer)
        action_load.setEnabled(True)
        action_load.setStatusTip(self.tr('Load outdoor spots from database'))
        self.toolbar.addAction(action_load)
        self.actions.append(action_load)
        
        # Add Spot action
        icon_path = os.path.join(self.plugin_dir, 'icons', 'add_spot.png')
        action_add = QAction(
            QIcon(icon_path),
            self.tr('Add New Spot'),
            self.iface.mainWindow()
        )
        action_add.triggered.connect(self.add_spot)
        action_add.setStatusTip(self.tr('Add a new outdoor spot'))
        self.toolbar.addAction(action_add)
        self.actions.append(action_add)
        
        # Toggle Safety Mode action
        icon_path = os.path.join(self.plugin_dir, 'icons', 'safety.png')
        action_safety = QAction(
            QIcon(icon_path),
            self.tr('Toggle Safety Mode'),
            self.iface.mainWindow()
        )
        action_safety.setCheckable(True)
        action_safety.triggered.connect(self.toggle_safety_mode)
        action_safety.setStatusTip(self.tr('Show/hide safety information for urbex spots'))
        self.toolbar.addAction(action_safety)
        self.actions.append(action_safety)
        
        # Sync with Backend action
        icon_path = os.path.join(self.plugin_dir, 'icons', 'sync.png')
        action_sync = QAction(
            QIcon(icon_path),
            self.tr('Sync with Backend'),
            self.iface.mainWindow()
        )
        action_sync.triggered.connect(self.sync_with_backend)
        action_sync.setStatusTip(self.tr('Synchronize spots with SPOTS backend'))
        self.toolbar.addAction(action_sync)
        self.actions.append(action_sync)
        
        # Show/Hide Dock action
        icon_path = os.path.join(self.plugin_dir, 'icons', 'dock.png')
        action_dock = QAction(
            QIcon(icon_path),
            self.tr('Show Spots Panel'),
            self.iface.mainWindow()
        )
        action_dock.setCheckable(True)
        action_dock.triggered.connect(self.toggle_dock)
        action_dock.setStatusTip(self.tr('Show/hide spots information panel'))
        self.toolbar.addAction(action_dock)
        self.actions.append(action_dock)
        
    def load_spots_layer(self):
        """Load spots from database as QGIS layer"""
        try:
            if not self.db_manager:
                QMessageBox.warning(
                    self.iface.mainWindow(),
                    self.tr("Database Error"),
                    self.tr("Database connection not initialized")
                )
                return
                
            # Create SpatiaLite layer
            uri = QgsDataSourceUri()
            uri.setDatabase(str(self.db_path))
            uri.setDataSource('', 'spots', 'geometry', '', 'id')
            
            # Create vector layer
            layer = QgsVectorLayer(uri.uri(), 'SPOTS - Outdoor Spots', 'spatialite')
            
            if not layer.isValid():
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    self.tr("Layer Error"),
                    self.tr("Failed to create spots layer. Check database connection.")
                )
                return
                
            # Apply styling
            self.layer_manager.apply_spot_styling(layer)
            
            # Add to project
            QgsProject.instance().addMapLayer(layer)
            
            # Zoom to layer extent
            canvas = self.iface.mapCanvas()
            canvas.setExtent(layer.extent())
            canvas.refresh()
            
            # Show success message
            self.iface.messageBar().pushMessage(
                "Success",
                f"Loaded {layer.featureCount()} spots",
                level=Qgis.Success,
                duration=3
            )
            
            # Connect to selection changed signal
            layer.selectionChanged.connect(self.on_spot_selected)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error loading spots: {e}", 'SPOTS', Qgis.Critical)
            QMessageBox.critical(
                self.iface.mainWindow(),
                self.tr("Error"),
                self.tr(f"Failed to load spots layer: {str(e)}")
            )
            
    def add_spot(self):
        """Open dialog to add new spot"""
        try:
            # Open add spot dialog
            dialog = AddSpotDialog(self.iface, self.db_manager)
            
            if dialog.exec_():
                # Get spot data from dialog
                spot_data = dialog.get_spot_data()
                
                # Add to database
                spot_id = self.db_manager.add_spot(spot_data)
                
                if spot_id:
                    # Refresh layer
                    self.refresh_spots_layer()
                    
                    self.iface.messageBar().pushMessage(
                        "Success",
                        f"Added new spot: {spot_data.get('name', 'Unnamed')}",
                        level=Qgis.Success,
                        duration=3
                    )
                    
        except Exception as e:
            QgsMessageLog.logMessage(f"Error adding spot: {e}", 'SPOTS', Qgis.Critical)
            
    def toggle_safety_mode(self, checked):
        """Toggle safety visualization for urbex spots"""
        try:
            # Find spots layer
            layers = QgsProject.instance().mapLayersByName('SPOTS - Outdoor Spots')
            
            if not layers:
                self.iface.messageBar().pushMessage(
                    "Warning",
                    "Please load spots layer first",
                    level=Qgis.Warning,
                    duration=3
                )
                return
                
            layer = layers[0]
            
            if checked:
                # Apply safety styling
                self.layer_manager.apply_safety_styling(layer)
                self.iface.messageBar().pushMessage(
                    "Safety Mode",
                    "Enabled urbex safety visualization",
                    level=Qgis.Info,
                    duration=2
                )
            else:
                # Apply normal styling
                self.layer_manager.apply_spot_styling(layer)
                self.iface.messageBar().pushMessage(
                    "Safety Mode",
                    "Disabled safety visualization",
                    level=Qgis.Info,
                    duration=2
                )
                
            # Refresh canvas
            self.iface.mapCanvas().refresh()
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error toggling safety mode: {e}", 'SPOTS', Qgis.Critical)
            
    def sync_with_backend(self):
        """Synchronize with SPOTS backend"""
        try:
            from .core.api_client import SpotsAPIClient
            
            # Initialize API client
            api_client = SpotsAPIClient()
            
            # Show progress
            self.iface.messageBar().pushMessage(
                "Syncing",
                "Synchronizing with SPOTS backend...",
                level=Qgis.Info
            )
            
            # Perform sync
            result = api_client.sync_spots(self.db_manager)
            
            if result['success']:
                # Refresh layer
                self.refresh_spots_layer()
                
                self.iface.messageBar().pushMessage(
                    "Success",
                    f"Synced {result['synced_count']} spots",
                    level=Qgis.Success,
                    duration=3
                )
            else:
                self.iface.messageBar().pushMessage(
                    "Sync Failed",
                    result.get('error', 'Unknown error'),
                    level=Qgis.Critical,
                    duration=5
                )
                
        except Exception as e:
            QgsMessageLog.logMessage(f"Error syncing: {e}", 'SPOTS', Qgis.Critical)
            self.iface.messageBar().pushMessage(
                "Error",
                f"Sync failed: {str(e)}",
                level=Qgis.Critical,
                duration=5
            )
            
    def toggle_dock(self, checked):
        """Show/hide spots dock widget"""
        if checked:
            self.spots_dock.show()
        else:
            self.spots_dock.hide()
            
    def on_spot_selected(self, selected_ids):
        """Handle spot selection"""
        try:
            if selected_ids and self.spots_dock.isVisible():
                # Get first selected spot
                spot_id = selected_ids[0]
                
                # Load spot details in dock
                self.spots_dock.load_spot(spot_id)
                
        except Exception as e:
            QgsMessageLog.logMessage(f"Error handling selection: {e}", 'SPOTS', Qgis.Warning)
            
    def refresh_spots_layer(self):
        """Refresh spots layer after changes"""
        try:
            layers = QgsProject.instance().mapLayersByName('SPOTS - Outdoor Spots')
            if layers:
                layers[0].reload()
                self.iface.mapCanvas().refresh()
                
        except Exception as e:
            QgsMessageLog.logMessage(f"Error refreshing layer: {e}", 'SPOTS', Qgis.Warning)
            
    def unload(self):
        """Remove plugin menu items and icons"""
        
        # Remove Processing provider
        if self.processing_provider:
            QgsApplication.processingRegistry().removeProvider(self.processing_provider)
            
        # Remove dock widget
        if self.spots_dock:
            self.iface.removeDockWidget(self.spots_dock)
            self.spots_dock.deleteLater()
            
        # Remove menu and toolbar
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
            
        # Remove toolbar
        if self.toolbar:
            del self.toolbar
            
        # Clean up database connection
        if self.db_manager:
            self.db_manager.close()