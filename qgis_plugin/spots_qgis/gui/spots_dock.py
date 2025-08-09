"""Dock widget for SPOTS plugin in QGIS."""

from qgis.PyQt.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QPushButton, QTableWidget,
                                 QTableWidgetItem, QComboBox, QLineEdit,
                                 QLabel, QGroupBox, QMessageBox)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.core import QgsProject, QgsFeature, QgsGeometry, QgsPointXY
import sqlite3
from pathlib import Path


class SpotsDockWidget(QDockWidget):
    """Main dock widget for managing spots."""
    
    spot_selected = pyqtSignal(int)  # Emitted when a spot is selected
    
    def __init__(self, parent=None, db_path=None):
        """Initialize the dock widget."""
        super().__init__("SPOTS Explorer", parent)
        
        self.db_path = db_path or Path.home() / "Development" / "projects" / "spots" / "data" / "occitanie_spots.db"
        
        # Create main widget
        main_widget = QWidget()
        self.setWidget(main_widget)
        
        # Create layout
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Add search section
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout()
        
        # Search bar
        search_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search spots by name...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_spots)
        search_bar_layout.addWidget(self.search_input)
        search_bar_layout.addWidget(self.search_button)
        search_layout.addLayout(search_bar_layout)
        
        # Filter dropdowns
        filter_layout = QHBoxLayout()
        
        # Type filter
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "waterfall", "cave", "viewpoint", 
                                  "ruins", "lake", "spring", "urbex"])
        self.type_filter.currentTextChanged.connect(self.filter_spots)
        filter_layout.addWidget(self.type_filter)
        
        # Department filter  
        filter_layout.addWidget(QLabel("Department:"))
        self.dept_filter = QComboBox()
        self.dept_filter.addItems(["All", "09", "11", "12", "30", "31", 
                                  "32", "34", "46", "48", "65", "66", "81", "82"])
        self.dept_filter.currentTextChanged.connect(self.filter_spots)
        filter_layout.addWidget(self.dept_filter)
        
        search_layout.addLayout(filter_layout)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Add spots table
        self.spots_table = QTableWidget()
        self.spots_table.setColumnCount(5)
        self.spots_table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Department", "Verified"])
        self.spots_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.spots_table.itemSelectionChanged.connect(self.on_spot_selected)
        layout.addWidget(self.spots_table)
        
        # Add action buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Spot")
        self.add_button.clicked.connect(self.add_spot)
        button_layout.addWidget(self.add_button)
        
        self.zoom_button = QPushButton("Zoom to Selected")
        self.zoom_button.clicked.connect(self.zoom_to_spot)
        self.zoom_button.setEnabled(False)
        button_layout.addWidget(self.zoom_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_spots)
        button_layout.addWidget(self.refresh_button)
        
        layout.addLayout(button_layout)
        
        # Load initial data
        self.load_spots()
    
    def load_spots(self):
        """Load spots from database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, type, department, verified 
                FROM spots 
                ORDER BY name
            """)
            
            spots = cursor.fetchall()
            conn.close()
            
            self.spots_table.setRowCount(len(spots))
            
            for row, spot in enumerate(spots):
                for col, value in enumerate(spot):
                    if col == 4:  # Verified column
                        value = "✓" if value else "✗"
                    item = QTableWidgetItem(str(value) if value else "")
                    self.spots_table.setItem(row, col, item)
            
            self.spots_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"Failed to load spots: {str(e)}")
    
    def search_spots(self):
        """Search spots by name."""
        search_text = self.search_input.text()
        if not search_text:
            self.load_spots()
            return
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, type, department, verified 
                FROM spots 
                WHERE name LIKE ?
                ORDER BY name
            """, (f"%{search_text}%",))
            
            spots = cursor.fetchall()
            conn.close()
            
            self.spots_table.setRowCount(len(spots))
            
            for row, spot in enumerate(spots):
                for col, value in enumerate(spot):
                    if col == 4:  # Verified column
                        value = "✓" if value else "✗"
                    item = QTableWidgetItem(str(value) if value else "")
                    self.spots_table.setItem(row, col, item)
            
            self.spots_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Search Error", f"Failed to search spots: {str(e)}")
    
    def filter_spots(self):
        """Filter spots by type and department."""
        type_filter = self.type_filter.currentText()
        dept_filter = self.dept_filter.currentText()
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            query = "SELECT id, name, type, department, verified FROM spots WHERE 1=1"
            params = []
            
            if type_filter != "All":
                query += " AND type = ?"
                params.append(type_filter)
            
            if dept_filter != "All":
                query += " AND department = ?"
                params.append(dept_filter)
            
            query += " ORDER BY name"
            
            cursor.execute(query, params)
            spots = cursor.fetchall()
            conn.close()
            
            self.spots_table.setRowCount(len(spots))
            
            for row, spot in enumerate(spots):
                for col, value in enumerate(spot):
                    if col == 4:  # Verified column
                        value = "✓" if value else "✗"
                    item = QTableWidgetItem(str(value) if value else "")
                    self.spots_table.setItem(row, col, item)
            
            self.spots_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Filter Error", f"Failed to filter spots: {str(e)}")
    
    def on_spot_selected(self):
        """Handle spot selection."""
        selected_items = self.spots_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            spot_id = int(self.spots_table.item(row, 0).text())
            self.spot_selected.emit(spot_id)
            self.zoom_button.setEnabled(True)
        else:
            self.zoom_button.setEnabled(False)
    
    def zoom_to_spot(self):
        """Zoom to selected spot on the map."""
        selected_items = self.spots_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        spot_id = int(self.spots_table.item(row, 0).text())
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT latitude, longitude 
                FROM spots 
                WHERE id = ?
            """, (spot_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                lat, lon = result
                # Emit signal or call QGIS zoom function
                # This would be connected to the main plugin
                from qgis.utils import iface
                if iface:
                    point = QgsPointXY(lon, lat)
                    iface.mapCanvas().setCenter(point)
                    iface.mapCanvas().zoomScale(5000)  # Zoom to 1:5000 scale
            
        except Exception as e:
            QMessageBox.warning(self, "Zoom Error", f"Failed to zoom to spot: {str(e)}")
    
    def add_spot(self):
        """Open dialog to add new spot."""
        from .add_spot_dialog import AddSpotDialog
        dialog = AddSpotDialog(self, self.db_path)
        if dialog.exec_():
            self.load_spots()  # Refresh the list