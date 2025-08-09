#!/usr/bin/env python3
"""
Upgrade SQLite database to SpatiaLite for QGIS integration
Adds spatial capabilities and indexes for optimal GIS performance
"""

import sqlite3
import sys
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpatiaLiteUpgrader:
    """Upgrade SQLite database to SpatiaLite with spatial capabilities"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self):
        """Connect to database and enable SpatiaLite"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.enable_load_extension(True)
            
            # Try to load SpatiaLite extension
            try:
                # Try different possible library names
                for lib in ['mod_spatialite', 'mod_spatialite.so', 'libspatialite.so']:
                    try:
                        self.conn.load_extension(lib)
                        logger.info(f"Successfully loaded SpatiaLite extension: {lib}")
                        break
                    except Exception:
                        continue
                else:
                    logger.warning("Could not load SpatiaLite extension - spatial features limited")
                    
            except Exception as e:
                logger.warning(f"SpatiaLite extension not available: {e}")
                logger.info("Continuing with basic spatial support")
                
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def initialize_spatial_metadata(self):
        """Initialize spatial metadata tables"""
        cursor = self.conn.cursor()
        
        try:
            # Check if spatial metadata exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='geometry_columns'")
            if not cursor.fetchone():
                # Initialize spatial metadata
                cursor.execute("SELECT InitSpatialMetaData(1)")
                logger.info("Initialized spatial metadata tables")
            else:
                logger.info("Spatial metadata already exists")
                
        except Exception as e:
            logger.warning(f"Could not initialize full SpatiaLite metadata: {e}")
            # Create minimal spatial support
            self._create_minimal_spatial_support(cursor)
            
    def _create_minimal_spatial_support(self, cursor):
        """Create minimal spatial support without full SpatiaLite"""
        logger.info("Creating minimal spatial support")
        
        # Create geometry_columns table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geometry_columns (
                f_table_name TEXT NOT NULL,
                f_geometry_column TEXT NOT NULL,
                geometry_type INTEGER NOT NULL,
                coord_dimension INTEGER NOT NULL,
                srid INTEGER NOT NULL,
                spatial_index_enabled INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (f_table_name, f_geometry_column)
            )
        """)
        
    def add_geometry_column(self):
        """Add geometry column to spots table"""
        cursor = self.conn.cursor()
        
        try:
            # Check if geometry column already exists
            cursor.execute("PRAGMA table_info(spots)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'geometry' not in columns:
                # Add geometry column
                cursor.execute("""
                    ALTER TABLE spots 
                    ADD COLUMN geometry BLOB
                """)
                logger.info("Added geometry column to spots table")
                
                # Register geometry column
                cursor.execute("""
                    INSERT OR REPLACE INTO geometry_columns 
                    (f_table_name, f_geometry_column, geometry_type, coord_dimension, srid, spatial_index_enabled)
                    VALUES ('spots', 'geometry', 1, 2, 4326, 1)
                """)
                logger.info("Registered geometry column in metadata")
            else:
                logger.info("Geometry column already exists")
                
        except Exception as e:
            logger.error(f"Failed to add geometry column: {e}")
            raise
            
    def populate_geometry(self):
        """Populate geometry column from latitude/longitude"""
        cursor = self.conn.cursor()
        
        try:
            # Check if we have SpatiaLite functions available
            cursor.execute("SELECT sqlite_version()")
            
            try:
                # Try SpatiaLite MakePoint function
                cursor.execute("""
                    UPDATE spots 
                    SET geometry = MakePoint(longitude, latitude, 4326)
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """)
                logger.info("Populated geometry using SpatiaLite MakePoint")
                
            except Exception:
                # Fallback to WKB format
                cursor.execute("""
                    SELECT id, latitude, longitude FROM spots
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """)
                
                spots = cursor.fetchall()
                for spot_id, lat, lon in spots:
                    # Create simple WKB point (this is a simplified version)
                    wkb = self._create_wkb_point(lon, lat)
                    cursor.execute("UPDATE spots SET geometry = ? WHERE id = ?", (wkb, spot_id))
                    
                logger.info(f"Populated geometry for {len(spots)} spots using WKB")
                
        except Exception as e:
            logger.error(f"Failed to populate geometry: {e}")
            raise
            
    def _create_wkb_point(self, x: float, y: float) -> bytes:
        """Create WKB (Well-Known Binary) for a point"""
        import struct
        
        # WKB format for 2D point
        # Byte order (1 = little-endian)
        wkb = struct.pack('<B', 1)
        # Geometry type (1 = Point)
        wkb += struct.pack('<I', 1)
        # X coordinate
        wkb += struct.pack('<d', x)
        # Y coordinate  
        wkb += struct.pack('<d', y)
        
        return wkb
        
    def create_spatial_index(self):
        """Create spatial index for geometry column"""
        cursor = self.conn.cursor()
        
        try:
            # Check if we have SpatiaLite
            try:
                cursor.execute("SELECT CreateSpatialIndex('spots', 'geometry')")
                logger.info("Created SpatiaLite spatial index")
                
            except Exception:
                # Create regular index as fallback
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_spots_geometry 
                    ON spots(geometry)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_spots_coords
                    ON spots(latitude, longitude)
                """)
                logger.info("Created standard indexes on geometry and coordinates")
                
        except Exception as e:
            logger.error(f"Failed to create spatial index: {e}")
            
    def add_spatial_views(self):
        """Create useful spatial views for QGIS"""
        cursor = self.conn.cursor()
        
        try:
            # View for spots by department
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_spots_by_department AS
                SELECT 
                    s.*,
                    d.name as department_name,
                    d.code as department_code
                FROM spots s
                LEFT JOIN departments d ON s.department_id = d.id
                WHERE s.geometry IS NOT NULL
            """)
            
            # View for urbex spots with safety info
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_urbex_spots AS
                SELECT * FROM spots
                WHERE location_type IN ('urbex', 'abandoned', 'ruins')
                AND geometry IS NOT NULL
            """)
            
            # View for verified spots only
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_verified_spots AS
                SELECT s.* FROM spots s
                JOIN verified_spots v ON s.id = v.spot_id
                WHERE s.geometry IS NOT NULL
            """)
            
            logger.info("Created spatial views for QGIS")
            
        except Exception as e:
            logger.warning(f"Could not create views: {e}")
            
    def add_triggers(self):
        """Add triggers to maintain geometry column"""
        cursor = self.conn.cursor()
        
        try:
            # Trigger to update geometry when coordinates change
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_geometry_on_coords_change
                AFTER UPDATE OF latitude, longitude ON spots
                FOR EACH ROW
                WHEN NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL
                BEGIN
                    UPDATE spots 
                    SET geometry = (
                        SELECT CASE 
                            WHEN (SELECT COUNT(*) FROM sqlite_master WHERE name='MakePoint') > 0
                            THEN MakePoint(NEW.longitude, NEW.latitude, 4326)
                            ELSE NULL
                        END
                    )
                    WHERE id = NEW.id;
                END;
            """)
            
            logger.info("Created geometry update triggers")
            
        except Exception as e:
            logger.warning(f"Could not create triggers: {e}")
            
    def upgrade(self):
        """Perform complete upgrade to SpatiaLite"""
        try:
            logger.info(f"Starting SpatiaLite upgrade for {self.db_path}")
            
            self.connect()
            self.initialize_spatial_metadata()
            self.add_geometry_column()
            self.populate_geometry()
            self.create_spatial_index()
            self.add_spatial_views()
            self.add_triggers()
            
            # Commit changes
            self.conn.commit()
            
            # Vacuum to optimize
            self.conn.execute("VACUUM")
            
            logger.info("✅ Successfully upgraded database to SpatiaLite")
            
            # Print summary
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM spots WHERE geometry IS NOT NULL")
            geo_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM spots")
            total_count = cursor.fetchone()[0]
            
            logger.info(f"Summary: {geo_count}/{total_count} spots have geometry")
            
        except Exception as e:
            logger.error(f"Upgrade failed: {e}")
            if self.conn:
                self.conn.rollback()
            raise
            
        finally:
            if self.conn:
                self.conn.close()
                
    def verify_upgrade(self):
        """Verify the upgrade was successful"""
        try:
            self.connect()
            cursor = self.conn.cursor()
            
            # Check geometry column exists
            cursor.execute("PRAGMA table_info(spots)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'geometry' in columns:
                logger.info("✓ Geometry column exists")
            else:
                logger.error("✗ Geometry column missing")
                return False
                
            # Check spatial metadata
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='geometry_columns'")
            if cursor.fetchone():
                logger.info("✓ Spatial metadata tables exist")
            else:
                logger.warning("⚠ Spatial metadata tables missing (limited functionality)")
                
            # Check indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%geometry%'")
            indexes = cursor.fetchall()
            if indexes:
                logger.info(f"✓ Spatial indexes exist: {[idx[0] for idx in indexes]}")
            else:
                logger.warning("⚠ No spatial indexes found")
                
            return True
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
            
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main upgrade function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upgrade SPOTS database to SpatiaLite")
    parser.add_argument(
        "--db-path",
        default="/home/miko/Development/projects/spots/data/occitanie_spots.db",
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify if upgrade is successful"
    )
    
    args = parser.parse_args()
    
    upgrader = SpatiaLiteUpgrader(args.db_path)
    
    if args.verify_only:
        success = upgrader.verify_upgrade()
        sys.exit(0 if success else 1)
    else:
        try:
            upgrader.upgrade()
            upgrader.verify_upgrade()
        except Exception as e:
            logger.error(f"Upgrade failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()