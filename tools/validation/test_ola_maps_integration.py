#!/usr/bin/env python3
"""Test script for Ola Maps integration"""

import os
import sys
from pathlib import Path
import asyncio
import requests
import json
from datetime import datetime

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.scrapers.geocoding_mixin import GeocodingMixin
from backend.scrapers.reddit_scraper_enhanced import EnhancedRedditScraper
from backend.api.mapping import router, geocoder as api_geocoder

class OlaMapsIntegrationTest:
    """Test all Ola Maps integration points"""
    
    def __init__(self):
        self.geocoder = GeocodingMixin()
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   → {details}")
        print()
        
    def test_api_key_configured(self):
        """Test if API key is configured"""
        has_key = bool(self.geocoder.ola_api_key)
        self.log_result(
            "API Key Configuration",
            has_key,
            f"Key present: {has_key}, Key length: {len(self.geocoder.ola_api_key) if has_key else 0}"
        )
        return has_key
        
    def test_geocoding(self):
        """Test geocoding functionality"""
        test_addresses = [
            "Place du Capitole, Toulouse",
            "Cité de Carcassonne",
            "Pont du Gard, Nîmes",
            "Pic du Midi, Hautes-Pyrénées"
        ]
        
        success_count = 0
        for address in test_addresses:
            result = self.geocoder.geocode_address(address)
            if result:
                success_count += 1
                self.log_result(
                    f"Geocode: {address}",
                    True,
                    f"Lat: {result['latitude']:.4f}, Lon: {result['longitude']:.4f}, "
                    f"Confidence: {result['confidence']}"
                )
            else:
                self.log_result(f"Geocode: {address}", False, "No result returned")
                
        return success_count > 0
        
    def test_reverse_geocoding(self):
        """Test reverse geocoding"""
        test_coords = [
            (43.6047, 1.4442),  # Toulouse center
            (43.2130, 2.3491),  # Carcassonne
            (43.9493, 4.5350),  # Pont du Gard
            (42.9369, 0.1412)   # Pic du Midi
        ]
        
        success_count = 0
        for lat, lon in test_coords:
            address = self.geocoder.reverse_geocode(lat, lon)
            if address:
                success_count += 1
                self.log_result(
                    f"Reverse Geocode: {lat:.4f}, {lon:.4f}",
                    True,
                    f"Address: {address[:50]}..."
                )
            else:
                self.log_result(
                    f"Reverse Geocode: {lat:.4f}, {lon:.4f}",
                    False,
                    "No address returned"
                )
                
        return success_count > 0
        
    def test_elevation(self):
        """Test elevation lookup"""
        test_locations = [
            ("Toulouse", 43.6047, 1.4442, 150),  # Expected ~150m
            ("Pic du Midi", 42.9369, 0.1412, 2877),  # Expected ~2877m
            ("Carcassonne", 43.2130, 2.3491, 110),  # Expected ~110m
            ("Montpellier", 43.6119, 3.8772, 50)  # Expected ~50m
        ]
        
        success_count = 0
        for name, lat, lon, expected in test_locations:
            elevation = self.geocoder.get_elevation(lat, lon)
            if elevation is not None:
                success_count += 1
                diff = abs(elevation - expected)
                accuracy = "accurate" if diff < 50 else "approximate"
                self.log_result(
                    f"Elevation: {name}",
                    True,
                    f"Elevation: {elevation}m (expected ~{expected}m) - {accuracy}"
                )
            else:
                self.log_result(f"Elevation: {name}", False, "No elevation returned")
                
        return success_count > 0
        
    def test_nearby_search(self):
        """Test nearby places search"""
        # Search near Toulouse center
        places = self.geocoder.find_nearby_places(43.6047, 1.4442, 500)
        
        if places:
            self.log_result(
                "Nearby Search",
                True,
                f"Found {len(places)} places within 500m of Toulouse center"
            )
            # Show first 3 places
            for place in places[:3]:
                print(f"   - {place.get('name', 'Unknown')}: {place.get('types', [])}")
        else:
            self.log_result("Nearby Search", False, "No places found")
            
        return len(places) > 0
        
    def test_api_endpoints(self):
        """Test FastAPI endpoints"""
        print("Testing API endpoints (requires running server)...")
        base_url = "http://localhost:8000/api/mapping"
        
        endpoints = [
            {
                "name": "Geocode Endpoint",
                "url": f"{base_url}/geocode",
                "method": "POST",
                "json": {"address": "Place du Capitole, Toulouse"}
            },
            {
                "name": "Elevation Endpoint",
                "url": f"{base_url}/elevation",
                "method": "POST",
                "json": {"latitude": 43.6047, "longitude": 1.4442}
            },
            {
                "name": "Nearest Spots",
                "url": f"{base_url}/spots/nearest",
                "method": "GET",
                "params": {"lat": 43.6047, "lon": 1.4442, "limit": 5}
            },
            {
                "name": "Elevation Stats",
                "url": f"{base_url}/stats/elevation",
                "method": "GET"
            }
        ]
        
        api_available = False
        for endpoint in endpoints:
            try:
                if endpoint["method"] == "POST":
                    response = requests.post(
                        endpoint["url"],
                        json=endpoint.get("json"),
                        timeout=5
                    )
                else:
                    response = requests.get(
                        endpoint["url"],
                        params=endpoint.get("params"),
                        timeout=5
                    )
                    
                if response.status_code == 200:
                    self.log_result(endpoint["name"], True, "Endpoint accessible")
                    api_available = True
                elif response.status_code == 503:
                    self.log_result(
                        endpoint["name"],
                        False,
                        "Service unavailable (API key not configured)"
                    )
                else:
                    self.log_result(
                        endpoint["name"],
                        False,
                        f"Status code: {response.status_code}"
                    )
                    
            except requests.exceptions.ConnectionError:
                self.log_result(
                    endpoint["name"],
                    False,
                    "Cannot connect - is the server running?"
                )
            except Exception as e:
                self.log_result(endpoint["name"], False, str(e))
                
        return api_available
        
    def test_enhanced_scraper(self):
        """Test enhanced Reddit scraper with geocoding"""
        scraper = EnhancedRedditScraper()
        
        # Test location extraction
        test_text = "Found a great swimming spot near Carcassonne, amazing cascade!"
        location_info = scraper.extract_location_info(test_text)
        
        has_locations = len(location_info['location_names']) > 0
        self.log_result(
            "Scraper Location Extraction",
            has_locations,
            f"Found locations: {location_info['location_names']}"
        )
        
        # Test geocoding enhancement
        test_spot = {
            "name": "Cascade près de Carcassonne",
            "description": "Beautiful waterfall near the medieval city"
        }
        
        enhanced = scraper.enhance_spot_with_geocoding(test_spot)
        has_coords = 'latitude' in enhanced and 'longitude' in enhanced
        
        self.log_result(
            "Scraper Geocoding Enhancement",
            has_coords,
            f"Enhanced: coords={has_coords}, elevation={'elevation' in enhanced}, "
            f"address={'address' in enhanced}"
        )
        
        return has_locations and has_coords
        
    def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("🔧 OLA MAPS INTEGRATION TEST SUITE")
        print("=" * 60)
        print()
        
        # Check API key first
        if not self.test_api_key_configured():
            print("⚠️  WARNING: OLA_MAPS_API_KEY not configured!")
            print("Set it with: export OLA_MAPS_API_KEY='your-key-here'")
            print()
            print("Running tests that don't require API key...")
            print()
        
        # Run tests
        if self.geocoder.ola_api_key:
            self.test_geocoding()
            self.test_reverse_geocoding()
            self.test_elevation()
            self.test_nearby_search()
            
        self.test_api_endpoints()
        self.test_enhanced_scraper()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        # Save results
        results_file = Path(__file__).parent / "test_results_ola_maps.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_run": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                    "api_key_present": bool(self.geocoder.ola_api_key)
                },
                "results": self.test_results
            }, f, indent=2)
            
        print(f"\nDetailed results saved to: {results_file}")
        
        return passed == total


if __name__ == "__main__":
    tester = OlaMapsIntegrationTest()
    success = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ Some tests failed. Check the results above.")
        
    print("\n📝 Next steps:")
    if not os.getenv('OLA_MAPS_API_KEY'):
        print("1. Get an Ola Maps API key from: https://maps.olacabs.com/")
        print("2. Set the API key: export OLA_MAPS_API_KEY='your-key-here'")
        print("3. Run this test again to verify full functionality")
    else:
        print("1. Start the API server: cd src/backend && python main.py")
        print("2. Run the elevation enrichment script")
        print("3. Test the new mapping endpoints in the browser")
    print("=" * 60)