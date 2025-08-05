import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from datetime import datetime
from typing import Dict

from src.backend.services.basic_geoai import BasicGeoAI


class TestBasicGeoAI:
    """Test suite for BasicGeoAI service"""
    
    @pytest.fixture
    def geoai(self):
        """Create BasicGeoAI instance"""
        return BasicGeoAI()
    
    @pytest.fixture
    def sample_spot(self):
        """Sample spot data for testing"""
        return {
            "id": 1,
            "name": "Test Waterfall",
            "latitude": 43.5,
            "longitude": 1.5,
            "type": "waterfall",
            "description": "Beautiful waterfall with easy access via marked trail",
            "elevation": 1200,
            "weather_sensitive": True
        }
    
    def test_haversine_distance(self, geoai):
        """Test haversine distance calculation"""
        # Test known distance: Toulouse to Paris (~590 km)
        toulouse = (43.6047, 1.4442)
        paris = (48.8566, 2.3522)
        
        distance = geoai._haversine_distance(toulouse[0], toulouse[1], paris[0], paris[1])
        
        # Should be approximately 590 km
        assert 580 < distance < 600
        
        # Test same point
        distance = geoai._haversine_distance(43.5, 1.5, 43.5, 1.5)
        assert distance == 0
    
    def test_estimate_accessibility_score(self, geoai):
        """Test accessibility score estimation"""
        # High accessibility spot
        easy_spot = {
            "type": "viewpoint",
            "elevation": 300,
            "description": "Easy access with parking nearby"
        }
        score = geoai.estimate_accessibility_score(easy_spot)
        assert 0.7 < score <= 1.0
        
        # Low accessibility spot
        hard_spot = {
            "type": "cave",
            "elevation": 2000,
            "description": "Difficult climb required, steep terrain"
        }
        score = geoai.estimate_accessibility_score(hard_spot)
        assert 0 <= score < 0.5
        
        # Medium accessibility
        medium_spot = {
            "type": "waterfall",
            "elevation": 800,
            "description": "Moderate hike on marked trail"
        }
        score = geoai.estimate_accessibility_score(medium_spot)
        assert 0.4 < score < 0.8
    
    def test_predict_crowd_level(self, geoai):
        """Test crowd level prediction"""
        spot = {"latitude": 43.6, "longitude": 1.4}
        
        # Test weekend high season
        with patch('src.backend.services.basic_geoai.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 7, 20, 14, 0)  # Saturday, July, 2 PM
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            crowd_level = geoai.predict_crowd_level(spot, user_location=(43.6047, 1.4442))
            assert crowd_level == "high"
        
        # Test weekday off-season
        with patch('src.backend.services.basic_geoai.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 2, 13, 10, 0)  # Tuesday, February, 10 AM
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            crowd_level = geoai.predict_crowd_level(spot, user_location=(43.6047, 1.4442))
            assert crowd_level == "low"
    
    def test_assess_difficulty(self, geoai, sample_spot):
        """Test difficulty assessment"""
        # Easy spot
        easy_spot = {**sample_spot, "elevation": 200, "type": "viewpoint"}
        difficulty = geoai.assess_difficulty(easy_spot, user_fitness="average")
        assert difficulty == "easy"
        
        # Hard spot
        hard_spot = {**sample_spot, "elevation": 2500, "type": "cave"}
        difficulty = geoai.assess_difficulty(hard_spot, user_fitness="average")
        assert difficulty == "hard"
        
        # Test with different fitness levels
        medium_spot = {**sample_spot, "elevation": 1000}
        assert geoai.assess_difficulty(medium_spot, user_fitness="low") == "hard"
        assert geoai.assess_difficulty(medium_spot, user_fitness="high") == "easy"
    
    def test_get_recommendations(self, geoai):
        """Test spot recommendations"""
        spots = [
            {"id": 1, "name": "Easy Trail", "type": "viewpoint", "elevation": 300,
             "latitude": 43.5, "longitude": 1.5, "description": "Easy access"},
            {"id": 2, "name": "Hard Cave", "type": "cave", "elevation": 1800,
             "latitude": 43.7, "longitude": 1.7, "description": "Difficult climb"},
            {"id": 3, "name": "Medium Falls", "type": "waterfall", "elevation": 800,
             "latitude": 43.6, "longitude": 1.6, "description": "Moderate hike"},
        ]
        
        preferences = {
            "difficulty": "easy",
            "max_distance": 50,
            "preferred_types": ["viewpoint", "waterfall"]
        }
        
        recommendations = geoai.get_recommendations(
            spots, 
            user_location=(43.5, 1.5),
            preferences=preferences
        )
        
        # Should recommend the easy trail first
        assert len(recommendations) > 0
        assert recommendations[0]["name"] == "Easy Trail"
        assert recommendations[0]["score"] > 0.5
        
        # Should include recommendation reasons
        assert "recommendation_reason" in recommendations[0]
    
    def test_analyze_spot_complete(self, geoai, sample_spot):
        """Test complete spot analysis"""
        analysis = geoai.analyze_spot(sample_spot, user_location=(43.6047, 1.4442))
        
        # Check all expected fields
        assert "accessibility_score" in analysis
        assert "predicted_crowd_level" in analysis
        assert "difficulty_assessment" in analysis
        assert "distance_from_user" in analysis
        assert "best_visit_time" in analysis
        assert "weather_considerations" in analysis
        
        # Check value ranges
        assert 0 <= analysis["accessibility_score"] <= 1
        assert analysis["predicted_crowd_level"] in ["low", "medium", "high"]
        assert analysis["difficulty_assessment"]["overall"] in ["easy", "moderate", "hard"]
        assert analysis["distance_from_user"] > 0
    
    def test_edge_cases(self, geoai):
        """Test edge cases and error handling"""
        # Empty spot
        empty_spot = {}
        score = geoai.estimate_accessibility_score(empty_spot)
        assert 0 <= score <= 1
        
        # Missing description
        no_desc_spot = {"type": "cave", "elevation": 1000}
        score = geoai.estimate_accessibility_score(no_desc_spot)
        assert 0 <= score <= 1
        
        # Invalid coordinates
        analysis = geoai.analyze_spot(
            {"latitude": None, "longitude": None},
            user_location=(43.6, 1.4)
        )
        assert analysis["distance_from_user"] == 0
        
        # No user location
        crowd = geoai.predict_crowd_level({"latitude": 43.5, "longitude": 1.5})
        assert crowd in ["low", "medium", "high"]


class TestWeatherIntegration:
    """Test weather-related functionality"""
    
    def test_weather_sensitive_handling(self):
        """Test handling of weather-sensitive spots"""
        spot = {
            "weather_sensitive": True,
            "type": "waterfall"
        }
        
        # In real implementation, this would check weather conditions
        # For now, just verify the flag exists
        assert spot["weather_sensitive"] is True
        
        # Test weather considerations
        weather_message = "Check weather conditions before visiting"
        if spot["weather_sensitive"]:
            assert len(weather_message) > 0


class TestDatabaseIntegration:
    """Test database-related operations"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection"""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        return conn, cursor
    
    def test_spot_retrieval_with_geoai(self, mock_db_connection):
        """Test spot retrieval with GeoAI analysis"""
        conn, cursor = mock_db_connection
        
        # Mock database response
        cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "Test Spot",
                "latitude": 43.5,
                "longitude": 1.5,
                "type": "waterfall",
                "elevation": 500
            }
        ]
        
        # Simulate retrieval and analysis
        spots = [dict(row) for row in cursor.fetchall.return_value]
        geoai = BasicGeoAI()
        
        for spot in spots:
            analysis = geoai.analyze_spot(spot, user_location=(43.6, 1.4))
            spot["geoai_analysis"] = analysis
        
        assert len(spots) == 1
        assert "geoai_analysis" in spots[0]
        assert spots[0]["geoai_analysis"]["distance_from_user"] > 0


class TestPerformance:
    """Test performance characteristics"""
    
    def test_batch_analysis_performance(self):
        """Test performance of batch spot analysis"""
        geoai = BasicGeoAI()
        
        # Create 100 test spots
        spots = []
        for i in range(100):
            spots.append({
                "id": i,
                "name": f"Spot {i}",
                "latitude": 43.5 + (i * 0.01),
                "longitude": 1.5 + (i * 0.01),
                "type": "waterfall" if i % 2 == 0 else "cave",
                "elevation": 500 + (i * 10),
                "description": "Test spot with moderate difficulty"
            })
        
        # Time the analysis
        import time
        start = time.time()
        
        for spot in spots:
            geoai.analyze_spot(spot, user_location=(43.6, 1.4))
        
        end = time.time()
        
        # Should complete 100 spots in under 1 second
        assert (end - start) < 1.0
    
    def test_recommendation_performance(self):
        """Test recommendation algorithm performance"""
        geoai = BasicGeoAI()
        
        # Create 500 spots
        spots = []
        for i in range(500):
            spots.append({
                "id": i,
                "name": f"Spot {i}",
                "latitude": 43.0 + (i * 0.002),
                "longitude": 1.0 + (i * 0.002),
                "type": ["waterfall", "cave", "viewpoint", "spring"][i % 4],
                "elevation": 200 + (i * 5),
                "description": "Test description"
            })
        
        import time
        start = time.time()
        
        recommendations = geoai.get_recommendations(
            spots,
            user_location=(43.5, 1.5),
            preferences={"difficulty": "easy", "max_distance": 100}
        )
        
        end = time.time()
        
        # Should complete in under 2 seconds even with 500 spots
        assert (end - start) < 2.0
        assert len(recommendations) <= 10  # Should limit results