#!/usr/bin/env python3
"""Add department column to spots table"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "occitanie_spots.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(spots)")
columns = [col[1] for col in cursor.fetchall()]

if 'department' not in columns:
    print("Adding department column...")
    cursor.execute("ALTER TABLE spots ADD COLUMN department TEXT")
    conn.commit()
    print("✅ Department column added")
else:
    print("Department column already exists")

conn.close()