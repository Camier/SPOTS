"""
Database Manager for SPOTS QGIS Plugin
Handles connection to SpatiaLite database
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from qgis.core import QgsMessageLog, Qgis

class SpotsDBManager:
    """Manage connection to SPOTS SpatiaLite database"""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager
        
        :param db_path: Path to SpatiaLite database
        """
        self.db_path = Path(db_path)
        self.conn = None
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
            
        self.connect()
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.enable_load_extension(True)
            
            # Try to load SpatiaLite
            try:
                self.conn.load_extension("mod_spatialite")
                QgsMessageLog.logMessage("SpatiaLite extension loaded", 'SPOTS', Qgis.Info)
            except Exception as e:
                QgsMessageLog.logMessage(f"SpatiaLite not available: {e}", 'SPOTS', Qgis.Warning)
                
            # Enable row factory for dict-like access
            self.conn.row_factory = sqlite3.Row
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Database connection failed: {e}", 'SPOTS', Qgis.Critical)
            raise
            
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def get_spots(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get spots from database with optional filters
        
        :param filters: Dictionary of filters (department, type, etc.)
        :returns: List of spot dictionaries
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                id, name, description, latitude, longitude,
                location_type, danger_level, access_difficulty,
                department_id, activities, source, confidence_score,
                created_at, updated_at
            FROM spots
            WHERE 1=1
        """
        
        params = []
        
        if filters:
            if 'department_id' in filters:
                query += " AND department_id = ?"
                params.append(filters['department_id'])
                
            if 'location_type' in filters:
                query += " AND location_type = ?"
                params.append(filters['location_type'])
                
            if 'danger_level' in filters:
                query += " AND danger_level <= ?"
                params.append(filters['danger_level'])
                
            if 'min_confidence' in filters:
                query += " AND confidence_score >= ?"
                params.append(filters['min_confidence'])
                
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        # Convert to list of dicts
        spots = []
        for row in cursor.fetchall():
            spot = dict(row)
            # Parse JSON fields
            if spot.get('activities'):
                try:
                    spot['activities'] = json.loads(spot['activities'])
                except:
                    spot['activities'] = []
            spots.append(spot)
            
        return spots
        
    def get_spot(self, spot_id: int) -> Optional[Dict]:
        """
        Get single spot by ID
        
        :param spot_id: Spot ID
        :returns: Spot dictionary or None
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM spots WHERE id = ?
        """, (spot_id,))
        
        row = cursor.fetchone()
        if row:
            spot = dict(row)
            # Parse JSON fields
            if spot.get('activities'):
                try:
                    spot['activities'] = json.loads(spot['activities'])
                except:
                    pass
            return spot
            
        return None
        
    def add_spot(self, spot_data: Dict) -> Optional[int]:
        """
        Add new spot to database
        
        :param spot_data: Spot data dictionary
        :returns: New spot ID or None
        """
        cursor = self.conn.cursor()
        
        try:
            # Prepare data
            activities_json = json.dumps(spot_data.get('activities', []))
            
            # Insert spot
            cursor.execute("""
                INSERT INTO spots (
                    name, description, latitude, longitude,
                    location_type, danger_level, access_difficulty,
                    department_id, activities, source, confidence_score,
                    geometry
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    MakePoint(?, ?, 4326))
            """, (
                spot_data.get('name'),
                spot_data.get('description'),
                spot_data.get('latitude'),
                spot_data.get('longitude'),
                spot_data.get('location_type'),
                spot_data.get('danger_level', 1),
                spot_data.get('access_difficulty', 1),
                spot_data.get('department_id'),
                activities_json,
                spot_data.get('source', 'manual'),
                spot_data.get('confidence_score', 1.0),
                spot_data.get('longitude'),
                spot_data.get('latitude')
            ))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to add spot: {e}", 'SPOTS', Qgis.Critical)
            self.conn.rollback()
            return None
            
    def update_spot(self, spot_id: int, spot_data: Dict) -> bool:
        """
        Update existing spot
        
        :param spot_id: Spot ID
        :param spot_data: Updated data
        :returns: Success status
        """
        cursor = self.conn.cursor()
        
        try:
            # Build update query dynamically
            updates = []
            params = []
            
            for field in ['name', 'description', 'location_type', 
                         'danger_level', 'access_difficulty']:
                if field in spot_data:
                    updates.append(f"{field} = ?")
                    params.append(spot_data[field])
                    
            if 'activities' in spot_data:
                updates.append("activities = ?")
                params.append(json.dumps(spot_data['activities']))
                
            if 'latitude' in spot_data and 'longitude' in spot_data:
                updates.append("latitude = ?")
                params.append(spot_data['latitude'])
                updates.append("longitude = ?")
                params.append(spot_data['longitude'])
                updates.append("geometry = MakePoint(?, ?, 4326)")
                params.extend([spot_data['longitude'], spot_data['latitude']])
                
            if not updates:
                return False
                
            # Add updated_at
            updates.append("updated_at = datetime('now')")
            
            # Add spot_id to params
            params.append(spot_id)
            
            query = f"UPDATE spots SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            self.conn.commit()
            return True
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to update spot: {e}", 'SPOTS', Qgis.Critical)
            self.conn.rollback()
            return False
            
    def delete_spot(self, spot_id: int) -> bool:
        """
        Delete spot from database
        
        :param spot_id: Spot ID
        :returns: Success status
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("DELETE FROM spots WHERE id = ?", (spot_id,))
            self.conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to delete spot: {e}", 'SPOTS', Qgis.Critical)
            self.conn.rollback()
            return False
            
    def get_departments(self) -> List[Dict]:
        """Get list of departments"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, name, code FROM departments
            ORDER BY code
        """)
        
        return [dict(row) for row in cursor.fetchall()]
        
    def get_spot_types(self) -> List[str]:
        """Get distinct spot types"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT location_type FROM spots
            WHERE location_type IS NOT NULL
            ORDER BY location_type
        """)
        
        return [row[0] for row in cursor.fetchall()]
        
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total spots
        cursor.execute("SELECT COUNT(*) FROM spots")
        stats['total_spots'] = cursor.fetchone()[0]
        
        # Spots with geometry
        cursor.execute("SELECT COUNT(*) FROM spots WHERE geometry IS NOT NULL")
        stats['georeferenced_spots'] = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT location_type, COUNT(*) as count
            FROM spots
            GROUP BY location_type
        """)
        stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By danger level
        cursor.execute("""
            SELECT danger_level, COUNT(*) as count
            FROM spots
            WHERE danger_level IS NOT NULL
            GROUP BY danger_level
        """)
        stats['by_danger'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By department
        cursor.execute("""
            SELECT d.name, COUNT(s.id) as count
            FROM spots s
            JOIN departments d ON s.department_id = d.id
            GROUP BY d.name
        """)
        stats['by_department'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        return stats