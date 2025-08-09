"""
Database operations for urbex spots
"""
import sqlite3
import logging
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path

from .data_models import UrbexSpot, UrbexCategory, DangerLevel, AccessDifficulty

logger = logging.getLogger(__name__)

class UrbexDatabase:
    """Handle database operations for urbex spots"""
    
    def __init__(self, db_path: str = "data/urbex_spots.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the urbex database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create urbex_spots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urbex_spots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    department TEXT NOT NULL,
                    region TEXT DEFAULT 'Occitanie',
                    
                    -- Location details
                    address TEXT,
                    city TEXT,
                    postal_code TEXT,
                    
                    -- Urbex-specific
                    danger_level INTEGER DEFAULT 2,
                    access_difficulty INTEGER DEFAULT 2,
                    is_active BOOLEAN DEFAULT 1,
                    year_abandoned INTEGER,
                    historical_use TEXT,
                    current_state TEXT,
                    
                    -- Access info
                    access_notes TEXT,
                    best_time_to_visit TEXT,
                    security_presence BOOLEAN DEFAULT 0,
                    fence_type TEXT,
                    entry_points TEXT,
                    
                    -- Safety
                    hazards TEXT,
                    structural_integrity TEXT,
                    asbestos_risk BOOLEAN DEFAULT 0,
                    
                    -- Photography
                    photography_spots TEXT,
                    best_light_time TEXT,
                    notable_features TEXT,
                    
                    -- Legal
                    legal_status TEXT,
                    owner_info TEXT,
                    permission_required BOOLEAN DEFAULT 1,
                    
                    -- Community
                    popularity_score INTEGER DEFAULT 0,
                    visit_count INTEGER DEFAULT 0,
                    last_confirmed_visit TEXT,
                    local_name TEXT,
                    
                    -- Metadata
                    discovered_date TEXT,
                    last_updated TEXT,
                    source TEXT,
                    verified BOOLEAN DEFAULT 0,
                    notes TEXT,
                    
                    -- Constraints
                    UNIQUE(latitude, longitude),
                    CHECK(danger_level BETWEEN 1 AND 4),
                    CHECK(access_difficulty BETWEEN 1 AND 4),
                    CHECK(popularity_score BETWEEN 0 AND 100)
                )
            ''')
            
            # Create media table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urbex_media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spot_id INTEGER NOT NULL,
                    media_type TEXT NOT NULL,
                    url TEXT NOT NULL,
                    caption TEXT,
                    uploaded_date TEXT,
                    FOREIGN KEY (spot_id) REFERENCES urbex_spots(id) ON DELETE CASCADE
                )
            ''')
            
            # Create visits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urbex_visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spot_id INTEGER NOT NULL,
                    visitor_name TEXT,
                    visit_date TEXT NOT NULL,
                    condition_report TEXT,
                    danger_update INTEGER,
                    photos_taken BOOLEAN DEFAULT 0,
                    FOREIGN KEY (spot_id) REFERENCES urbex_spots(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_urbex_department ON urbex_spots(department)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_urbex_category ON urbex_spots(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_urbex_danger ON urbex_spots(danger_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_urbex_coords ON urbex_spots(latitude, longitude)')
            
            conn.commit()
            logger.info(f"Urbex database initialized at {self.db_path}")
    
    def add_spot(self, spot: UrbexSpot) -> int:
        """Add a new urbex spot to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                spot_dict = spot.to_dict()
                
                # Prepare the insert query
                columns = ', '.join(spot_dict.keys())
                placeholders = ', '.join(['?' for _ in spot_dict])
                query = f'INSERT INTO urbex_spots ({columns}) VALUES ({placeholders})'
                
                cursor.execute(query, list(spot_dict.values()))
                spot_id = cursor.lastrowid
                
                # Add media if present
                if spot.photos:
                    for photo_url in spot.photos:
                        cursor.execute('''
                            INSERT INTO urbex_media (spot_id, media_type, url)
                            VALUES (?, ?, ?)
                        ''', (spot_id, 'photo', photo_url))
                
                if spot.videos:
                    for video_url in spot.videos:
                        cursor.execute('''
                            INSERT INTO urbex_media (spot_id, media_type, url)
                            VALUES (?, ?, ?)
                        ''', (spot_id, 'video', video_url))
                
                conn.commit()
                logger.info(f"Added urbex spot: {spot.name} (ID: {spot_id})")
                return spot_id
                
        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate spot or constraint violation: {e}")
            return -1
        except Exception as e:
            logger.error(f"Error adding urbex spot: {e}")
            return -1
    
    def get_spot_by_id(self, spot_id: int) -> Optional[UrbexSpot]:
        """Get a single urbex spot by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM urbex_spots WHERE id = ?', (spot_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_spot(dict(row))
            return None
    
    def get_spots_by_department(self, department: str) -> List[UrbexSpot]:
        """Get all urbex spots in a department"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM urbex_spots 
                WHERE department = ? AND is_active = 1
                ORDER BY popularity_score DESC
            ''', (department,))
            
            return [self._row_to_spot(dict(row)) for row in cursor.fetchall()]
    
    def get_spots_by_category(self, category: UrbexCategory) -> List[UrbexSpot]:
        """Get all spots of a specific category"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM urbex_spots 
                WHERE category = ? AND is_active = 1
                ORDER BY popularity_score DESC
            ''', (category.value,))
            
            return [self._row_to_spot(dict(row)) for row in cursor.fetchall()]
    
    def get_safe_spots(self, max_danger: int = 2) -> List[UrbexSpot]:
        """Get spots safe for beginners"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM urbex_spots 
                WHERE danger_level <= ? 
                AND access_difficulty <= ?
                AND asbestos_risk = 0
                AND is_active = 1
                ORDER BY popularity_score DESC
            ''', (max_danger, 2))
            
            return [self._row_to_spot(dict(row)) for row in cursor.fetchall()]
    
    def search_spots(self, query: str) -> List[UrbexSpot]:
        """Search for spots by name or notes"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_pattern = f'%{query}%'
            cursor.execute('''
                SELECT * FROM urbex_spots 
                WHERE (name LIKE ? OR notes LIKE ? OR city LIKE ?)
                AND is_active = 1
                ORDER BY popularity_score DESC
            ''', (search_pattern, search_pattern, search_pattern))
            
            return [self._row_to_spot(dict(row)) for row in cursor.fetchall()]
    
    def get_nearby_spots(self, lat: float, lng: float, radius_km: float = 50) -> List[UrbexSpot]:
        """Get spots within radius of coordinates"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Approximate calculation (good enough for nearby search)
            lat_range = radius_km / 111  # 1 degree latitude ≈ 111 km
            lng_range = radius_km / (111 * 0.7)  # Adjust for latitude
            
            cursor.execute('''
                SELECT * FROM urbex_spots 
                WHERE latitude BETWEEN ? AND ?
                AND longitude BETWEEN ? AND ?
                AND is_active = 1
                ORDER BY popularity_score DESC
            ''', (lat - lat_range, lat + lat_range, 
                  lng - lng_range, lng + lng_range))
            
            return [self._row_to_spot(dict(row)) for row in cursor.fetchall()]
    
    def update_spot(self, spot_id: int, updates: Dict) -> bool:
        """Update an existing spot"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query
                set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                query = f'UPDATE urbex_spots SET {set_clause}, last_updated = ? WHERE id = ?'
                
                values = list(updates.values()) + [datetime.now().isoformat(), spot_id]
                cursor.execute(query, values)
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating spot: {e}")
            return False
    
    def record_visit(self, spot_id: int, condition_report: str, 
                     danger_update: Optional[int] = None) -> bool:
        """Record a visit to a spot"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO urbex_visits 
                    (spot_id, visit_date, condition_report, danger_update)
                    VALUES (?, ?, ?, ?)
                ''', (spot_id, datetime.now().isoformat(), condition_report, danger_update))
                
                # Update visit count and last confirmed visit
                cursor.execute('''
                    UPDATE urbex_spots 
                    SET visit_count = visit_count + 1,
                        last_confirmed_visit = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), spot_id))
                
                # Update danger level if provided
                if danger_update:
                    cursor.execute('''
                        UPDATE urbex_spots SET danger_level = ? WHERE id = ?
                    ''', (danger_update, spot_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error recording visit: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total spots
            cursor.execute('SELECT COUNT(*) FROM urbex_spots WHERE is_active = 1')
            stats['total_spots'] = cursor.fetchone()[0]
            
            # By category
            cursor.execute('''
                SELECT category, COUNT(*) 
                FROM urbex_spots 
                WHERE is_active = 1 
                GROUP BY category
            ''')
            stats['by_category'] = dict(cursor.fetchall())
            
            # By department
            cursor.execute('''
                SELECT department, COUNT(*) 
                FROM urbex_spots 
                WHERE is_active = 1 
                GROUP BY department
            ''')
            stats['by_department'] = dict(cursor.fetchall())
            
            # By danger level
            cursor.execute('''
                SELECT danger_level, COUNT(*) 
                FROM urbex_spots 
                WHERE is_active = 1 
                GROUP BY danger_level
            ''')
            stats['by_danger'] = dict(cursor.fetchall())
            
            # Recent visits
            cursor.execute('''
                SELECT COUNT(*) FROM urbex_visits 
                WHERE date(visit_date) >= date('now', '-30 days')
            ''')
            stats['recent_visits'] = cursor.fetchone()[0]
            
            return stats
    
    def _row_to_spot(self, row: Dict) -> UrbexSpot:
        """Convert database row to UrbexSpot object"""
        # Convert string enums back to enum types
        row['category'] = UrbexCategory(row['category'])
        row['danger_level'] = DangerLevel(row['danger_level'])
        row['access_difficulty'] = AccessDifficulty(row['access_difficulty'])
        
        # Convert comma-separated strings to lists
        if row.get('entry_points'):
            row['entry_points'] = row['entry_points'].split(',')
        if row.get('hazards'):
            row['hazards'] = row['hazards'].split(',')
        if row.get('photography_spots'):
            row['photography_spots'] = row['photography_spots'].split(',')
        if row.get('notable_features'):
            row['notable_features'] = row['notable_features'].split(',')
        
        # Convert date strings to datetime
        if row.get('last_confirmed_visit'):
            row['last_confirmed_visit'] = datetime.fromisoformat(row['last_confirmed_visit'])
        if row.get('discovered_date'):
            row['discovered_date'] = datetime.fromisoformat(row['discovered_date'])
        if row.get('last_updated'):
            row['last_updated'] = datetime.fromisoformat(row['last_updated'])
        
        # Remove id field (not in data model)
        row.pop('id', None)
        
        return UrbexSpot(**row)