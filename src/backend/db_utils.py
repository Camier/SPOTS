"""
Database utilities with connection pooling and async support
"""

import sqlite3
from contextlib import contextmanager
from threading import local
import asyncio
import aiosqlite
from pathlib import Path

# Thread-local storage for connections
_thread_local = local()


class DatabasePool:
    """Simple connection pool for SQLite"""

    def __init__(self, db_path, max_connections=5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections = []
        self._lock = asyncio.Lock()

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool (sync)"""
        if not hasattr(_thread_local, "connection"):
            _thread_local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            _thread_local.connection.row_factory = sqlite3.Row
            # Enable optimizations
            _thread_local.connection.execute("PRAGMA journal_mode=WAL")
            _thread_local.connection.execute("PRAGMA synchronous=NORMAL")
            _thread_local.connection.execute("PRAGMA cache_size=-64000")
            _thread_local.connection.execute("PRAGMA temp_store=MEMORY")
            _thread_local.connection.execute("PRAGMA optimize")

        try:
            yield _thread_local.connection
        except Exception:
            _thread_local.connection.rollback()
            raise
        else:
            _thread_local.connection.commit()

    async def get_async_connection(self):
        """Get an async connection"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Enable optimizations
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA cache_size=-64000")
            await db.execute("PRAGMA temp_store=MEMORY")
            yield db


# Global pool instance
db_path = Path(__file__).parent.parent.parent / "data" / "occitanie_spots.db"
db_pool = DatabasePool(db_path)


# Convenience functions
def get_db():
    """Get database connection (sync)"""
    return db_pool.get_connection()

def get_db_connection(db_path: str):
    """Get database connection with path"""
    return DatabasePool(db_path).get_connection()

def init_db_optimizations(db_path: str):
    """Initialize database with performance optimizations"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode = WAL")
        
        # Optimize query planner
        cursor.execute("PRAGMA optimize")
        
        # Set cache size (negative = KB, positive = pages)
        cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
        
        # Enable query statistics
        cursor.execute("PRAGMA count_changes = OFF")
        cursor.execute("PRAGMA synchronous = NORMAL")
        
        # Create indexes if they don't exist
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_spots_type ON spots(type)",
            "CREATE INDEX IF NOT EXISTS idx_spots_department ON spots(department)",
            "CREATE INDEX IF NOT EXISTS idx_spots_location ON spots(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_spots_ratings ON spots(beauty_rating DESC, popularity DESC)",
            "CREATE INDEX IF NOT EXISTS idx_spots_name ON spots(name)",
            "CREATE INDEX IF NOT EXISTS idx_spots_type_dept ON spots(type, department)",
        ]
        
        for idx in indexes:
            cursor.execute(idx)
        
        conn.commit()


async def get_async_db():
    """Get async database connection"""
    async with db_pool.get_async_connection() as db:
        yield db


# Query helpers
async def fetch_one(query: str, params: tuple = ()):
    """Execute query and fetch one result"""
    async with db_pool.get_async_connection() as db:
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def fetch_all(query: str, params: tuple = ()):
    """Execute query and fetch all results"""
    async with db_pool.get_async_connection() as db:
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def execute(query: str, params: tuple = ()):
    """Execute a query without fetching results"""
    async with db_pool.get_async_connection() as db:
        await db.execute(query, params)
        await db.commit()


# Department bounds helper
DEPT_BOUNDS_SQL = {
    "09": "latitude < 43.2 AND longitude < 2.0",
    "12": "latitude > 44.2 AND longitude > 2.2",
    "46": "latitude > 44.3 AND longitude < 2.0",
    "81": "latitude > 43.7 AND longitude > 1.8 AND longitude < 2.5",
    "65": "latitude < 43.5 AND longitude < 0.5",
    "32": "latitude > 43.5 AND longitude < 1.0",
    "82": "latitude > 43.8 AND longitude > 1.0 AND longitude < 1.7",
    "31": "1=1",
}


def get_dept_where_clause(dept_code: str) -> str:
    """Get WHERE clause for department"""
    return DEPT_BOUNDS_SQL.get(dept_code, "1=1")
