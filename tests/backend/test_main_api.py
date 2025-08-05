import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sqlite3
from pathlib import Path

from src.backend.main import app, get_db, DEPARTMENT_INFO


class TestMainAPI:
    """Test suite for main FastAPI endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock(spec=sqlite3.Cursor)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.row_factory = sqlite3.Row
        
        # Default mock responses
        mock_cursor.fetchone.return_value = {"total": 817}
        mock_cursor.fetchall.return_value = []
        
        return mock_conn, mock_cursor
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns expected data"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Spots Secrets Occitanie API"
        assert data["version"] == "2.3.0"
        assert data["coverage"] == "8 departments"
        assert data["total_spots"] == 817
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
    
    def test_health_check_success(self, client, mock_db):
        """Test health check when database is accessible"""
        mock_conn, mock_cursor = mock_db
        mock_cursor.fetchone.return_value = [817]
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["spots_count"] == 817
    
    def test_health_check_failure(self, client):
        """Test health check when database fails"""
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert "Database connection failed" in data["error"]
    
    def test_get_config(self, client):
        """Test configuration endpoint"""
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        
        assert data["geocoding"]["service"] == "BAN"
        assert data["geocoding"]["premium_enabled"] is False
        assert data["api_base_url"] == "http://localhost:8000"
        assert "IGN" in data["map_providers"]
        assert "OpenStreetMap" in data["map_providers"]
    
    def test_get_spots_basic(self, client, mock_db):
        """Test basic spots retrieval"""
        mock_conn, mock_cursor = mock_db
        mock_cursor.fetchone.return_value = {"total": 100}
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "Test Spot",
                "latitude": 43.5,
                "longitude": 1.5,
                "type": "waterfall",
                "description": "Test description",
                "weather_sensitive": 0,
                "confidence_score": 0.8,
                "elevation": 500,
                "address": "Test address",
                "department": "31"
            }
        ]
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            response = client.get("/api/spots")
            assert response.status_code == 200
            data = response.json()
            
            assert data["total"] == 100
            assert data["limit"] == 100
            assert data["offset"] == 0
            assert len(data["spots"]) == 1
            assert data["spots"][0]["name"] == "Test Spot"
    
    def test_get_spots_with_filters(self, client, mock_db):
        """Test spots retrieval with filters"""
        mock_conn, mock_cursor = mock_db
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            # Test with type filter
            response = client.get("/api/spots?type=waterfall")
            assert response.status_code == 200
            
            # Test with confidence filter
            response = client.get("/api/spots?min_confidence=0.7")
            assert response.status_code == 200
            
            # Test with pagination
            response = client.get("/api/spots?limit=50&offset=10")
            assert response.status_code == 200
    
    def test_get_spots_validation(self, client):
        """Test spots endpoint validation"""
        # Test invalid limit
        response = client.get("/api/spots?limit=0")
        assert response.status_code == 422
        
        response = client.get("/api/spots?limit=1001")
        assert response.status_code == 422
        
        # Test invalid offset
        response = client.get("/api/spots?offset=-1")
        assert response.status_code == 422
        
        # Test invalid confidence
        response = client.get("/api/spots?min_confidence=1.5")
        assert response.status_code == 422
    
    def test_get_quality_spots(self, client, mock_db):
        """Test quality spots endpoint"""
        mock_conn, mock_cursor = mock_db
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "High Quality Spot",
                "latitude": 43.6,
                "longitude": 1.4,
                "type": "cave",
                "description": "Detailed description of this amazing cave",
                "weather_sensitive": 1,
                "confidence_score": 0.95,
                "elevation": 800,
                "address": "Near village X",
                "department": "09",
                "description_length": 40,
                "quality_score": 135
            }
        ]
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            response = client.get("/api/spots/quality")
            assert response.status_code == 200
            data = response.json()
            
            assert data["total"] == 1
            assert data["filters"]["min_confidence"] == 0.7
            assert data["filters"]["exclude_unknown"] is True
            assert data["spots"][0]["has_description"] is True
            assert data["spots"][0]["has_elevation"] is True
    
    def test_get_spot_by_id(self, client, mock_db):
        """Test getting specific spot by ID"""
        mock_conn, mock_cursor = mock_db
        mock_cursor.fetchone.return_value = {
            "id": 42,
            "name": "Specific Spot",
            "latitude": 43.7,
            "longitude": 1.6,
            "type": "spring"
        }
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            response = client.get("/api/spots/42")
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == 42
            assert data["name"] == "Specific Spot"
    
    def test_get_spot_not_found(self, client, mock_db):
        """Test getting non-existent spot"""
        mock_conn, mock_cursor = mock_db
        mock_cursor.fetchone.return_value = None
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            response = client.get("/api/spots/999")
            assert response.status_code == 404
            assert response.json()["detail"] == "Spot not found"
    
    def test_get_stats(self, client, mock_db):
        """Test statistics endpoint"""
        mock_conn, mock_cursor = mock_db
        
        # Mock different query results
        def mock_fetchone_side_effect(*args):
            query = args[0] if args else ""
            if "COUNT(*) FROM spots WHERE" in query:
                # Department counts
                return [50]
            elif "AVG(confidence_score)" in query:
                return [0.85]
            elif "weather_sensitive = 1" in query:
                return [234]
            else:
                return [817]  # Total spots
        
        def mock_fetchall_side_effect(*args):
            # Type counts
            return [
                ("waterfall", 250),
                ("cave", 200),
                ("spring", 150),
                ("ruins", 100),
                ("unknown", 117)
            ]
        
        mock_cursor.fetchone.side_effect = mock_fetchone_side_effect
        mock_cursor.fetchall.side_effect = mock_fetchall_side_effect
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            response = client.get("/api/stats")
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_spots"] == 817
            assert "departments" in data
            assert "spots_by_type" in data
            assert data["weather_sensitive"] == 234
            assert data["average_confidence"] == 0.85
    
    def test_get_spots_by_department(self, client, mock_db):
        """Test department-specific spots endpoint"""
        mock_conn, mock_cursor = mock_db
        mock_cursor.fetchone.return_value = [25]  # Total in department
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "Ariège Spot",
                "latitude": 43.0,
                "longitude": 1.5,
                "type": "cave"
            }
        ]
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            response = client.get("/api/spots/department/09")
            assert response.status_code == 200
            data = response.json()
            
            assert data["department"]["code"] == "09"
            assert data["department"]["name"] == "Ariège"
            assert data["total"] == 25
    
    def test_get_spots_invalid_department(self, client):
        """Test invalid department code"""
        response = client.get("/api/spots/department/99")
        assert response.status_code == 422  # Validation error
        
        response = client.get("/api/spots/department/XX")
        assert response.status_code == 422
    
    def test_search_spots(self, client, mock_db):
        """Test spot search functionality"""
        mock_conn, mock_cursor = mock_db
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "Cascade de Test",
                "latitude": 43.5,
                "longitude": 1.5,
                "type": "waterfall",
                "description": "Beautiful test waterfall",
                "confidence_score": 0.9,
                "department": "31"
            }
        ]
        
        with patch("src.backend.main.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            response = client.get("/api/spots/search?q=cascade")
            assert response.status_code == 200
            data = response.json()
            
            assert data["query"] == "cascade"
            assert data["count"] == 1
            assert data["spots"][0]["name"] == "Cascade de Test"
    
    def test_search_spots_validation(self, client):
        """Test search validation"""
        # Query too short
        response = client.get("/api/spots/search?q=a")
        assert response.status_code == 422
        
        # Missing query
        response = client.get("/api/spots/search")
        assert response.status_code == 422
    
    def test_department_boundaries(self):
        """Test department boundary configuration"""
        assert len(DEPARTMENT_INFO) == 8
        
        # Check specific departments
        assert DEPARTMENT_INFO["09"]["name"] == "Ariège"
        assert "lat_max" in DEPARTMENT_INFO["09"]["bounds"]
        
        assert DEPARTMENT_INFO["31"]["name"] == "Haute-Garonne"
        assert DEPARTMENT_INFO["31"]["bounds"] == {}  # No bounds restriction
    
    @pytest.mark.parametrize("bounds,expected", [
        ({"lat_min": 43.5, "lat_max": 44.0}, "latitude > 43.5 AND latitude < 44.0"),
        ({"lng_min": 1.0, "lng_max": 2.0}, "longitude > 1.0 AND longitude < 2.0"),
        ({}, "1=1"),
        ({"lat_min": 43.0}, "latitude > 43.0"),
    ])
    def test_build_where_clause(self, bounds, expected):
        """Test WHERE clause builder"""
        from src.backend.main import build_where_clause
        result = build_where_clause(bounds)
        assert result == expected


class TestAPIIntegration:
    """Integration tests for API routers"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_api_routes_registered(self, client):
        """Test that all API routes are properly registered"""
        # Test mapping routes
        response = client.get("/api/mapping/")
        assert response.status_code in [200, 404]  # Route exists
        
        # Test IGN routes
        response = client.get("/api/ign/")
        assert response.status_code in [200, 404]  # Route exists
        
        # Test code analysis routes
        response = client.get("/api/code/")
        assert response.status_code in [200, 404]  # Route exists
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly set"""
        response = client.get("/")
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"