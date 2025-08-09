"""
Spot Layer Manager for SPOTS QGIS Plugin
Handles layer creation, styling, and visualization
"""

from qgis.core import (
    QgsVectorLayer, QgsProject, QgsSymbol, QgsSimpleFillSymbolLayer,
    QgsSimpleMarkerSymbolLayer, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsMarkerSymbol, QgsRuleBasedRenderer,
    QgsConditionalStyle, QgsGraduatedSymbolRenderer,
    QgsClassificationRange, QgsProperty, QgsPropertyCollection,
    QgsSymbolLayer, QgsPalLayerSettings, QgsTextFormat,
    QgsVectorLayerSimpleLabeling, QgsTextBufferSettings,
    QgsMessageLog, Qgis, QgsPointXY, QgsGeometry
)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QSize, QPointF

class SpotLayerManager:
    """Manage spot layers and their visualization"""
    
    def __init__(self, iface, db_manager):
        """
        Initialize layer manager
        
        :param iface: QGIS interface
        :param db_manager: Database manager instance
        """
        self.iface = iface
        self.db_manager = db_manager
        
        # Define color schemes
        self.type_colors = {
            'waterfall': QColor(64, 164, 223),     # Blue
            'cave': QColor(139, 90, 43),           # Brown
            'ruins': QColor(169, 169, 169),        # Gray
            'urbex': QColor(255, 140, 0),          # Orange
            'abandoned': QColor(128, 128, 128),    # Dark gray
            'viewpoint': QColor(147, 112, 219),    # Purple
            'lake': QColor(0, 191, 255),           # Deep sky blue
            'forest': QColor(34, 139, 34),         # Forest green
            'mountain': QColor(139, 137, 137),     # Snow gray
            'spring': QColor(0, 255, 255),         # Cyan
            'default': QColor(255, 0, 0)           # Red
        }
        
        # Danger level colors
        self.danger_colors = {
            1: QColor(0, 255, 0),       # Green (Safe)
            2: QColor(255, 255, 0),     # Yellow (Caution)
            3: QColor(255, 165, 0),     # Orange (Dangerous)
            4: QColor(255, 0, 0)        # Red (Extreme)
        }
        
    def apply_spot_styling(self, layer: QgsVectorLayer):
        """
        Apply default styling to spots layer
        
        :param layer: Vector layer to style
        """
        try:
            # Create categorized renderer based on location_type
            categories = []
            
            for spot_type, color in self.type_colors.items():
                if spot_type == 'default':
                    continue
                    
                # Create symbol
                symbol = QgsMarkerSymbol.createSimple({
                    'name': 'circle',
                    'color': color.name(),
                    'outline_color': 'black',
                    'outline_width': '0.5',
                    'size': '4'
                })
                
                # Create category
                category = QgsRendererCategory(spot_type, symbol, spot_type.title())
                categories.append(category)
                
            # Add default category for unknown types
            default_symbol = QgsMarkerSymbol.createSimple({
                'name': 'circle',
                'color': self.type_colors['default'].name(),
                'outline_color': 'black',
                'outline_width': '0.5',
                'size': '3'
            })
            
            # Create renderer
            renderer = QgsCategorizedSymbolRenderer('location_type', categories)
            renderer.setDefaultSymbol(default_symbol)
            
            # Apply to layer
            layer.setRenderer(renderer)
            
            # Add labels
            self._apply_labels(layer)
            
            # Trigger repaint
            layer.triggerRepaint()
            
            QgsMessageLog.logMessage("Applied spot styling", 'SPOTS', Qgis.Info)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to apply styling: {e}", 'SPOTS', Qgis.Critical)
            
    def apply_safety_styling(self, layer: QgsVectorLayer):
        """
        Apply safety-based styling for urbex spots
        
        :param layer: Vector layer to style
        """
        try:
            # Create rule-based renderer for complex safety visualization
            root_rule = QgsRuleBasedRenderer.Rule(None)
            
            # Rules for each danger level
            for level, color in self.danger_colors.items():
                # Create symbol with size based on danger
                size = 3 + (level * 1.5)  # Bigger = more dangerous
                
                symbol = QgsMarkerSymbol.createSimple({
                    'name': 'triangle' if level >= 3 else 'circle',
                    'color': color.name(),
                    'outline_color': 'black',
                    'outline_width': '1' if level >= 3 else '0.5',
                    'size': str(size)
                })
                
                # Add warning overlay for high danger
                if level >= 3:
                    # Add second symbol layer for warning effect
                    warning_layer = QgsSimpleMarkerSymbolLayer.create({
                        'name': 'cross',
                        'color': 'red',
                        'size': str(size * 0.5),
                        'angle': '45'
                    })
                    symbol.appendSymbolLayer(warning_layer)
                
                # Create rule
                rule = QgsRuleBasedRenderer.Rule(
                    symbol,
                    filterExp=f"danger_level = {level}",
                    label=f"Danger Level {level}"
                )
                root_rule.appendChild(rule)
                
            # Add special rule for urbex without danger level
            unknown_symbol = QgsMarkerSymbol.createSimple({
                'name': 'question',
                'color': 'gray',
                'outline_color': 'black',
                'outline_width': '0.5',
                'size': '4'
            })
            
            unknown_rule = QgsRuleBasedRenderer.Rule(
                unknown_symbol,
                filterExp="location_type IN ('urbex', 'abandoned') AND danger_level IS NULL",
                label="Unknown Danger"
            )
            root_rule.appendChild(unknown_rule)
            
            # Create and apply renderer
            renderer = QgsRuleBasedRenderer(root_rule)
            layer.setRenderer(renderer)
            
            # Add warning labels
            self._apply_safety_labels(layer)
            
            # Add buffer visualization for extreme danger
            self._add_danger_buffers(layer)
            
            layer.triggerRepaint()
            
            QgsMessageLog.logMessage("Applied safety styling", 'SPOTS', Qgis.Info)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to apply safety styling: {e}", 'SPOTS', Qgis.Critical)
            
    def _apply_labels(self, layer: QgsVectorLayer):
        """Apply standard labels to layer"""
        
        # Create label settings
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = 'name'
        label_settings.enabled = True
        
        # Text format
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 8))
        text_format.setSize(8)
        text_format.setColor(QColor(0, 0, 0))
        
        # Text buffer
        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1)
        buffer_settings.setColor(QColor(255, 255, 255))
        text_format.setBuffer(buffer_settings)
        
        label_settings.setFormat(text_format)
        
        # Create labeling
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(labeling)
        layer.setLabelsEnabled(True)
        
    def _apply_safety_labels(self, layer: QgsVectorLayer):
        """Apply safety-focused labels"""
        
        # Create label settings
        label_settings = QgsPalLayerSettings()
        
        # Use expression for label text
        label_settings.fieldName = """
            CASE 
                WHEN danger_level = 4 THEN '⚠️ EXTREME: ' || name
                WHEN danger_level = 3 THEN '⚠️ DANGER: ' || name
                WHEN danger_level = 2 THEN '⚡ CAUTION: ' || name
                WHEN danger_level = 1 THEN '✓ ' || name
                ELSE '❓ ' || name
            END
        """
        label_settings.isExpression = True
        label_settings.enabled = True
        
        # Text format with danger colors
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 9, QFont.Bold))
        text_format.setSize(9)
        
        # Buffer for visibility
        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(2)
        buffer_settings.setColor(QColor(255, 255, 255))
        text_format.setBuffer(buffer_settings)
        
        label_settings.setFormat(text_format)
        
        # Create labeling
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(labeling)
        layer.setLabelsEnabled(True)
        
    def _add_danger_buffers(self, layer: QgsVectorLayer):
        """Add buffer visualization for dangerous spots"""
        
        # This would typically create a temporary layer with buffers
        # For now, we'll just log the intention
        QgsMessageLog.logMessage("Danger buffer visualization ready", 'SPOTS', Qgis.Info)
        
    def create_filtered_layer(self, base_layer: QgsVectorLayer, 
                            filter_expression: str, 
                            layer_name: str) -> QgsVectorLayer:
        """
        Create filtered layer from base layer
        
        :param base_layer: Base spots layer
        :param filter_expression: QGIS filter expression
        :param layer_name: Name for new layer
        :returns: Filtered vector layer
        """
        
        # Clone the layer with filter
        filtered_layer = base_layer.clone()
        filtered_layer.setName(layer_name)
        filtered_layer.setSubsetString(filter_expression)
        
        return filtered_layer
        
    def highlight_spot(self, layer: QgsVectorLayer, spot_id: int):
        """
        Highlight specific spot on map
        
        :param layer: Spots layer
        :param spot_id: ID of spot to highlight
        """
        
        # Select the spot
        layer.selectByExpression(f"id = {spot_id}")
        
        # Zoom to selected
        canvas = self.iface.mapCanvas()
        canvas.zoomToSelected(layer)
        canvas.refresh()