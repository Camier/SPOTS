"""Dialog for adding new spots to the database."""

from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                 QFormLayout, QLineEdit, QComboBox,
                                 QTextEdit, QSpinBox, QDialogButtonBox,
                                 QPushButton, QMessageBox, QDoubleSpinBox)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapToolEmitPoint
from qgis.utils import iface
import sqlite3
from pathlib import Path
from datetime import datetime


class AddSpotDialog(QDialog):
    """Dialog for adding a new spot."""
    
    def __init__(self, parent=None, db_path=None):
        """Initialize the dialog."""
        super().__init__(parent)
        
        self.db_path = db_path or Path.home() / "Development" / "projects" / "spots" / "data" / "occitanie_spots.db"
        self.setWindowTitle("Add New Spot")
        self.setModal(True)
        self.resize(400, 500)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create form
        form_layout = QFormLayout()
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter spot name...")
        form_layout.addRow("Name:", self.name_input)
        
        # Type dropdown
        self.type_combo = QComboBox()
        self.type_combo.addItems(["waterfall", "cave", "viewpoint", "ruins", 
                                 "lake", "spring", "urbex", "forest", "beach", "other"])
        form_layout.addRow("Type:", self.type_combo)
        
        # Coordinates
        coord_layout = QHBoxLayout()
        self.lat_input = QDoubleSpinBox()
        self.lat_input.setRange(-90, 90)
        self.lat_input.setDecimals(6)
        self.lat_input.setValue(43.6)  # Default to Toulouse area
        
        self.lon_input = QDoubleSpinBox()
        self.lon_input.setRange(-180, 180)
        self.lon_input.setDecimals(6)
        self.lon_input.setValue(1.4)  # Default to Toulouse area
        
        self.pick_button = QPushButton("Pick from Map")
        self.pick_button.clicked.connect(self.pick_from_map)
        
        coord_layout.addWidget(QLineEdit("Lat:"))
        coord_layout.addWidget(self.lat_input)
        coord_layout.addWidget(QLineEdit("Lon:"))
        coord_layout.addWidget(self.lon_input)
        coord_layout.addWidget(self.pick_button)
        
        form_layout.addRow("Coordinates:", coord_layout)
        
        # Department
        self.dept_combo = QComboBox()
        self.dept_combo.addItems(["", "09", "11", "12", "30", "31", "32", 
                                 "34", "46", "48", "65", "66", "81", "82"])
        form_layout.addRow("Department:", self.dept_combo)
        
        # Description
        self.description_text = QTextEdit()
        self.description_text.setPlaceholderText("Enter description...")
        self.description_text.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_text)
        
        # Access info
        self.access_text = QTextEdit()
        self.access_text.setPlaceholderText("How to access this spot...")
        self.access_text.setMaximumHeight(100)
        form_layout.addRow("Access Info:", self.access_text)
        
        # Difficulty (for hiking spots)
        self.difficulty_spin = QSpinBox()
        self.difficulty_spin.setRange(1, 5)
        self.difficulty_spin.setValue(2)
        form_layout.addRow("Difficulty (1-5):", self.difficulty_spin)
        
        # Source
        self.source_input = QLineEdit()
        self.source_input.setText("manual_entry")
        form_layout.addRow("Source:", self.source_input)
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_spot)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.map_tool = None
    
    def pick_from_map(self):
        """Allow user to pick coordinates from the map."""
        if iface:
            QMessageBox.information(self, "Pick Location", 
                                  "Click on the map to select spot location")
            
            # Create map tool for picking points
            canvas = iface.mapCanvas()
            self.map_tool = QgsMapToolEmitPoint(canvas)
            self.map_tool.canvasClicked.connect(self.on_map_clicked)
            canvas.setMapTool(self.map_tool)
    
    def on_map_clicked(self, point, button):
        """Handle map click to get coordinates."""
        if button == Qt.LeftButton:
            # Transform to WGS84 if needed
            canvas_crs = iface.mapCanvas().mapSettings().destinationCrs()
            wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            
            if canvas_crs != wgs84_crs:
                transform = QgsCoordinateTransform(canvas_crs, wgs84_crs, QgsProject.instance())
                point = transform.transform(point)
            
            self.lat_input.setValue(point.y())
            self.lon_input.setValue(point.x())
            
            # Reset map tool
            iface.mapCanvas().unsetMapTool(self.map_tool)
            self.map_tool = None
    
    def save_spot(self):
        """Save the new spot to database."""
        # Validate input
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a spot name")
            return
        
        # Get all values
        spot_type = self.type_combo.currentText()
        lat = self.lat_input.value()
        lon = self.lon_input.value()
        department = self.dept_combo.currentText()
        description = self.description_text.toPlainText().strip()
        access_info = self.access_text.toPlainText().strip()
        source = self.source_input.text().strip()
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.enable_load_extension(True)
            
            # Try to load SpatiaLite
            try:
                conn.load_extension("mod_spatialite")
            except:
                pass  # Continue without spatial features
            
            cursor = conn.cursor()
            
            # Insert new spot
            cursor.execute("""
                INSERT INTO spots (
                    name, type, latitude, longitude, department,
                    description, access_info, source, 
                    created_at, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, spot_type, lat, lon, department,
                description, access_info, source,
                datetime.now().isoformat(), 0
            ))
            
            # Update geometry if SpatiaLite is available
            spot_id = cursor.lastrowid
            try:
                cursor.execute("""
                    UPDATE spots 
                    SET geometry = MakePoint(?, ?, 4326)
                    WHERE id = ?
                """, (lon, lat, spot_id))
            except:
                pass  # Geometry update failed, continue without it
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Success", f"Spot '{name}' added successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save spot: {str(e)}")