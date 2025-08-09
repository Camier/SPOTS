#!/usr/bin/env python3
"""
Data Migration Script
Consolidates data from both projects into unified database
"""

import os
import sys
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Paths to source data
SCRAPER_PROJECT = Path("/home/miko/projects/secret-toulouse-spots")
WEATHER_APP = Path("/home/miko/projects/active/weather-map-app")
TARGET_DB = project_root / "data" / "toulouse_spots.db"

# Colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
NC = '\033[0m'

def print_status(message, status="info"):
    """Print colored status messages"""
    if status == "success":
        print(f"{GREEN}✓ {message}{NC}")
    elif status == "warning":
        print(f"{YELLOW}⚠️  {message}{NC}")
    elif status == "error":
        print(f"{RED}❌ {message}{NC}")
    else:
        print(f"  {message}")

def backup_existing_data():
    """Backup existing database if it exists"""
    if TARGET_DB.exists():
        backup_dir = project_root / "data" / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"toulouse_spots_backup_{timestamp}.db"
        
        shutil.copy2(TARGET_DB, backup_path)
        print_status(f"Backed up existing database to {backup_path.name}", "success")
        return backup_path
    return None

def get_spot_hash(spot_data):
    """Generate unique hash for a spot based on key attributes"""
    key_parts = [
        str(spot_data.get('name', '')),
        str(spot_data.get('latitude', '')),
        str(spot_data.get('longitude', ''))
    ]
    return hashlib.md5(''.join(key_parts).encode()).hexdigest()

def migrate_database(source_db, target_conn):
    """Migrate data from source database to target"""
    try:
        source_conn = sqlite3.connect(source_db)
        source_conn.row_factory = sqlite3.Row
        
        # Get all spots from source
        cursor = source_conn.execute("""
            SELECT * FROM spots
            ORDER BY created_at DESC
        """)
        
        spots = cursor.fetchall()
        migrated = 0
        duplicates = 0
        
        for spot in spots:
            spot_dict = dict(spot)
            spot_hash = get_spot_hash(spot_dict)
            
            # Check if spot already exists
            existing = target_conn.execute(
                "SELECT id FROM spots WHERE data_hash = ?",
                (spot_hash,)
            ).fetchone()
            
            if existing:
                duplicates += 1
                continue
            
            # Insert new spot
            columns = list(spot_dict.keys())
            placeholders = ','.join(['?' for _ in columns])
            values = [spot_dict[col] for col in columns]
            
            target_conn.execute(f"""
                INSERT OR IGNORE INTO spots ({','.join(columns)}, data_hash)
                VALUES ({placeholders}, ?)
            """, values + [spot_hash])
            
            migrated += 1
        
        source_conn.close()
        return migrated, duplicates
        
    except Exception as e:
        print_status(f"Error migrating {source_db}: {e}", "error")
        return 0, 0

def migrate_json_files(json_path, target_conn):
    """Migrate spots from JSON exports"""
    if not json_path.exists():
        return 0, 0
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        spots = data if isinstance(data, list) else data.get('spots', [])
        migrated = 0
        duplicates = 0
        
        for spot in spots:
            spot_hash = get_spot_hash(spot)
            
            # Check if spot already exists
            existing = target_conn.execute(
                "SELECT id FROM spots WHERE data_hash = ?",
                (spot_hash,)
            ).fetchone()
            
            if existing:
                duplicates += 1
                continue
            
            # Insert new spot
            target_conn.execute("""
                INSERT OR IGNORE INTO spots 
                (name, latitude, longitude, type, description, source, data_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                spot.get('name', 'Unknown'),
                spot.get('latitude'),
                spot.get('longitude'),
                spot.get('type', 'unknown'),
                spot.get('description', ''),
                spot.get('source', 'json_import'),
                spot_hash
            ))
            
            migrated += 1
        
        return migrated, duplicates
        
    except Exception as e:
        print_status(f"Error migrating {json_path}: {e}", "error")
        return 0, 0

def create_unified_database():
    """Create the unified database schema"""
    conn = sqlite3.connect(TARGET_DB)
    
    # Create main spots table with all fields
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            type TEXT,
            description TEXT,
            access_info TEXT,
            weather_sensitive BOOLEAN DEFAULT 0,
            source TEXT,
            source_url TEXT,
            confidence_score REAL DEFAULT 0.5,
            verified BOOLEAN DEFAULT 0,
            data_hash TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_spots_location ON spots(latitude, longitude)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_spots_type ON spots(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_spots_hash ON spots(data_hash)")
    
    # Create weather cache table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER,
            weather_data TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (spot_id) REFERENCES spots (id)
        )
    """)
    
    # Create user spots table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            type TEXT,
            description TEXT,
            notes TEXT,
            visited BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    return conn

def main():
    """Main migration process"""
    print(f"\n{GREEN}🔄 Toulouse Weather Spots - Data Migration{NC}")
    print("=" * 50)
    
    # Backup existing data
    print("\n📦 Backing up existing data...")
    backup_existing_data()
    
    # Create unified database
    print("\n🗄️  Creating unified database...")
    conn = create_unified_database()
    print_status("Database schema created", "success")
    
    # Migrate from scraper project
    print("\n📥 Migrating from secret-toulouse-spots project...")
    total_migrated = 0
    total_duplicates = 0
    
    # Database sources
    db_sources = [
        SCRAPER_PROJECT / "database" / "toulouse_spots.db",
        SCRAPER_PROJECT / "database" / "hidden_spots.db",
        SCRAPER_PROJECT / "scrapers" / "hidden_spots.db",
        WEATHER_APP / "database" / "hidden_spots.db",
        WEATHER_APP / "scrapers" / "hidden_spots.db"
    ]
    
    for db_path in db_sources:
        if db_path.exists():
            print_status(f"Migrating {db_path.name}...")
            migrated, duplicates = migrate_database(db_path, conn)
            total_migrated += migrated
            total_duplicates += duplicates
            print_status(f"  Migrated: {migrated}, Duplicates: {duplicates}")
    
    # JSON sources
    json_sources = [
        SCRAPER_PROJECT / "data" / "all_spots_export.json",
        SCRAPER_PROJECT / "data" / "hidden_spots_export.json",
        WEATHER_APP / "data" / "integrated_spots.json",
        WEATHER_APP / "data" / "hidden_spots_export.json"
    ]
    
    print("\n📄 Migrating from JSON exports...")
    for json_path in json_sources:
        if json_path.exists():
            print_status(f"Migrating {json_path.name}...")
            migrated, duplicates = migrate_json_files(json_path, conn)
            total_migrated += migrated
            total_duplicates += duplicates
            print_status(f"  Migrated: {migrated}, Duplicates: {duplicates}")
    
    # Copy static files
    print("\n📁 Copying configuration files...")
    
    # Copy weather app frontend files
    if (WEATHER_APP / "src").exists():
        shutil.copytree(
            WEATHER_APP / "src",
            project_root / "src" / "frontend" / "js",
            dirs_exist_ok=True
        )
        print_status("Frontend files copied", "success")
    
    # Commit all changes
    conn.commit()
    
    # Get final statistics
    total_spots = conn.execute("SELECT COUNT(*) FROM spots").fetchone()[0]
    
    print(f"\n{GREEN}✅ Migration Complete!{NC}")
    print(f"\n📊 Statistics:")
    print(f"  - Total spots migrated: {total_migrated}")
    print(f"  - Duplicates skipped: {total_duplicates}")
    print(f"  - Total unique spots: {total_spots}")
    
    conn.close()
    
    print(f"\n{YELLOW}Next steps:{NC}")
    print("1. Review the migrated data")
    print("2. Run the application to verify everything works")
    print("3. Archive the old project directories")

if __name__ == "__main__":
    main()
