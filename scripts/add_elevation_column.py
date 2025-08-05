#!/usr/bin/env python3
"""Add elevation column to spots table"""

import sqlite3
from pathlib import Path

def add_elevation_column():
    """Add elevation column to existing spots table"""
    db_path = Path(__file__).parent.parent / "data" / "occitanie_spots.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(spots)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'elevation' not in columns:
            print("Adding elevation column to spots table...")
            cursor.execute("ALTER TABLE spots ADD COLUMN elevation REAL")
            conn.commit()
            print("✅ Elevation column added successfully")
        else:
            print("ℹ️ Elevation column already exists")
            
        # Also add geocoding confidence column
        if 'geocoding_confidence' not in columns:
            print("Adding geocoding_confidence column to spots table...")
            cursor.execute("ALTER TABLE spots ADD COLUMN geocoding_confidence REAL DEFAULT 0.0")
            conn.commit()
            print("✅ Geocoding confidence column added successfully")
        else:
            print("ℹ️ Geocoding confidence column already exists")
            
        # Add reverse geocoded address
        if 'address' not in columns:
            print("Adding address column to spots table...")
            cursor.execute("ALTER TABLE spots ADD COLUMN address TEXT")
            conn.commit()
            print("✅ Address column added successfully")
        else:
            print("ℹ️ Address column already exists")
            
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_elevation_column()