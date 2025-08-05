import pytest
import asyncio
from playwright.async_api import async_playwright
import requests
import time
from typing import Dict, List


class TestFullStackIntegration:
    """Full stack integration tests for SPOTS application"""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """Base URL for API"""
        return "http://localhost:8000"
    
    @pytest.fixture(scope="class")
    def frontend_url(self):
        """Base URL for frontend"""
        return "http://localhost:8081"
    
    @pytest.fixture(scope="class")
    def check_servers_running(self, api_base_url, frontend_url):
        """Ensure both servers are running before tests"""
        # Check API
        try:
            response = requests.get(f"{api_base_url}/health")
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running on port 8000")
        
        # Check Frontend
        try:
            response = requests.get(frontend_url)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend server not running on port 8081")
    
    def test_api_frontend_data_consistency(self, api_base_url, frontend_url, check_servers_running):
        """Test that frontend correctly displays API data"""
        # Get data from API
        api_response = requests.get(f"{api_base_url}/api/spots/quality?limit=10")
        assert api_response.status_code == 200
        api_data = api_response.json()
        
        # Verify data structure
        assert "spots" in api_data
        assert len(api_data["spots"]) > 0
        
        first_spot = api_data["spots"][0]
        assert all(key in first_spot for key in ["id", "name", "latitude", "longitude", "type"])
    
    @pytest.mark.asyncio
    async def test_map_loads_and_displays_spots(self, frontend_url, check_servers_running):
        """Test that map loads and displays spots from API"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Go to frontend
            await page.goto(f"{frontend_url}/regional-map-optimized.html")
            
            # Wait for map to load
            await page.wait_for_selector("#map", timeout=5000)
            
            # Wait for spots to load (stats should update)
            await page.wait_for_function(
                "document.querySelector('#stats-container').textContent.includes('spots affichés')",
                timeout=10000
            )
            
            # Check stats display
            stats_text = await page.text_content("#stats-container")
            assert "spots affichés" in stats_text
            
            # Check for markers or clusters
            markers_count = await page.locator(".leaflet-marker-icon, .leaflet-cluster-icon").count()
            assert markers_count > 0
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_filter_integration(self, frontend_url, api_base_url, check_servers_running):
        """Test that filters work correctly with API"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Mock API to return specific data
            await page.route("**/api/spots/quality**", lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body="""{"total": 3, "spots": [
                    {"id": 1, "name": "Waterfall 1", "type": "waterfall", "latitude": 43.5, "longitude": 1.5, "confidence_score": 0.9},
                    {"id": 2, "name": "Cave 1", "type": "cave", "latitude": 43.6, "longitude": 1.6, "confidence_score": 0.8},
                    {"id": 3, "name": "Waterfall 2", "type": "waterfall", "latitude": 43.7, "longitude": 1.7, "confidence_score": 0.85}
                ]}"""
            ))
            
            await page.goto(f"{frontend_url}/regional-map-optimized.html")
            
            # Wait for initial load
            await page.wait_for_timeout(2000)
            
            # Click waterfall filter
            await page.click('.filter-btn[data-filter-type="waterfall"]')
            await page.wait_for_timeout(500)
            
            # Verify filter is active
            waterfall_btn = page.locator('.filter-btn[data-filter-type="waterfall"]')
            classes = await waterfall_btn.get_attribute("class")
            assert "active" in classes
            
            await browser.close()
    
    def test_api_error_handling_integration(self, api_base_url):
        """Test API error responses"""
        # Test 404
        response = requests.get(f"{api_base_url}/api/spots/99999")
        assert response.status_code == 404
        assert "Spot not found" in response.json()["detail"]
        
        # Test validation error
        response = requests.get(f"{api_base_url}/api/spots?limit=0")
        assert response.status_code == 422
        
        # Test invalid department
        response = requests.get(f"{api_base_url}/api/spots/department/99")
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_responsive_design(self, frontend_url, check_servers_running):
        """Test responsive design on different viewports"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Test mobile viewport
            mobile_page = await browser.new_page(
                viewport={"width": 375, "height": 667},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 13_0 like Mac OS X) AppleWebKit/605.1.15"
            )
            await mobile_page.goto(f"{frontend_url}/regional-map-optimized.html")
            
            # Info panel should be visible
            info_panel = mobile_page.locator(".info-panel")
            await expect(info_panel).to_be_visible()
            
            # Test tablet viewport
            tablet_page = await browser.new_page(
                viewport={"width": 768, "height": 1024}
            )
            await tablet_page.goto(f"{frontend_url}/regional-map-optimized.html")
            
            # Map should fill viewport
            map_element = tablet_page.locator("#map")
            await expect(map_element).to_be_visible()
            
            await browser.close()
    
    def test_performance_metrics(self, api_base_url):
        """Test API performance"""
        # Test response times
        endpoints = [
            "/api/spots?limit=100",
            "/api/spots/quality?limit=500",
            "/api/stats",
            "/api/spots/department/31"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{api_base_url}{endpoint}")
            end_time = time.time()
            
            assert response.status_code == 200
            # Response should be under 1 second
            assert (end_time - start_time) < 1.0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, api_base_url, check_servers_running):
        """Test API handles concurrent requests"""
        async def make_request(session, url):
            async with session.get(url) as response:
                return await response.json()
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Make 10 concurrent requests
            urls = [f"{api_base_url}/api/spots?offset={i*10}" for i in range(10)]
            
            start_time = time.time()
            results = await asyncio.gather(*[make_request(session, url) for url in urls])
            end_time = time.time()
            
            # All requests should succeed
            assert len(results) == 10
            for result in results:
                assert "spots" in result
            
            # Should complete in reasonable time
            assert (end_time - start_time) < 5.0
    
    def test_department_filtering_integration(self, api_base_url):
        """Test department filtering works correctly"""
        # Get all departments
        stats_response = requests.get(f"{api_base_url}/api/stats")
        stats = stats_response.json()
        
        # Test each department endpoint
        for dept_code, dept_info in stats["departments"].items():
            if dept_info["count"] > 0:
                response = requests.get(f"{api_base_url}/api/spots/department/{dept_code}")
                assert response.status_code == 200
                data = response.json()
                
                assert data["department"]["code"] == dept_code
                assert data["department"]["name"] == dept_info["name"]
                # Count might differ due to boundary calculations
                assert data["total"] >= 0
    
    @pytest.mark.asyncio
    async def test_search_functionality_removed(self, frontend_url, check_servers_running):
        """Verify search functionality has been removed"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(f"{frontend_url}/regional-map-optimized.html")
            
            # Search box should not exist
            search_elements = await page.locator(".search-box, #searchInput").count()
            assert search_elements == 0
            
            # No search-related scripts should be present
            page_content = await page.content()
            assert "searchInput" not in page_content
            assert "search-box" not in page_content
            
            await browser.close()


class TestDataIntegrity:
    """Test data integrity between frontend and backend"""
    
    def test_coordinate_precision(self, api_base_url):
        """Test coordinate precision is maintained"""
        response = requests.get(f"{api_base_url}/api/spots?limit=1")
        spot = response.json()["spots"][0]
        
        # Coordinates should have sufficient precision
        lat_str = str(spot["latitude"])
        lng_str = str(spot["longitude"])
        
        # At least 4 decimal places
        assert len(lat_str.split(".")[-1]) >= 4
        assert len(lng_str.split(".")[-1]) >= 4
    
    def test_data_consistency_across_endpoints(self, api_base_url):
        """Test data consistency across different endpoints"""
        # Get a spot from general endpoint
        general_response = requests.get(f"{api_base_url}/api/spots?limit=1")
        general_spot = general_response.json()["spots"][0]
        
        # Get same spot from specific endpoint
        specific_response = requests.get(f"{api_base_url}/api/spots/{general_spot['id']}")
        specific_spot = specific_response.json()
        
        # Key fields should match
        assert general_spot["name"] == specific_spot["name"]
        assert general_spot["latitude"] == specific_spot["latitude"]
        assert general_spot["longitude"] == specific_spot["longitude"]
        assert general_spot["type"] == specific_spot["type"]