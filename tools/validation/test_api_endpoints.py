#!/usr/bin/env python3
"""Test API endpoints without requiring Ola Maps API key"""

import requests
import json

def test_api():
    """Test API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Spots API Endpoints")
    print("=" * 50)
    
    # Test 1: Root endpoint
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Server Running")
            print(f"   Version: {data['version']}")
            print(f"   Features: {', '.join(data['features'])}")
            
            # Check for mapping endpoints
            mapping_endpoints = [ep for ep in data['endpoints'] if 'mapping' in ep]
            print(f"\n   Mapping Endpoints ({len(mapping_endpoints)}):")
            for endpoint in mapping_endpoints:
                print(f"   - {endpoint}: {data['endpoints'][endpoint]}")
        else:
            print(f"❌ API returned status {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Start server with: cd src/backend && python main.py")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Get all spots
    print("\n✅ Testing /api/spots...")
    try:
        response = requests.get(f"{base_url}/api/spots?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total spots: {data['total']}")
            print(f"   Returned: {len(data['spots'])}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Stats endpoint
    print("\n✅ Testing /api/stats...")
    try:
        response = requests.get(f"{base_url}/api/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total spots: {data['total_spots']}")
            print(f"   Weather sensitive: {data['weather_sensitive']}")
            print(f"   Spot types: {len(data['spots_by_type'])}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Elevation stats (works without API key)
    print("\n✅ Testing /api/mapping/stats/elevation...")
    try:
        response = requests.get(f"{base_url}/api/mapping/stats/elevation")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total spots: {data['total_spots']}")
            print(f"   With elevation: {data['spots_with_elevation']}")
            print(f"   Coverage: {data['coverage_percentage']:.1f}%")
            
            if data['elevation_range']['min'] is not None:
                print(f"   Range: {data['elevation_range']['min']}m - {data['elevation_range']['max']}m")
                print(f"   Average: {data['elevation_range']['average']:.0f}m")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Nearest spots (works without API key)
    print("\n✅ Testing /api/mapping/spots/nearest...")
    try:
        response = requests.get(
            f"{base_url}/api/mapping/spots/nearest",
            params={"lat": 43.6047, "lon": 1.4442, "limit": 5}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data['count']} spots near Toulouse")
            for spot in data['spots'][:3]:
                print(f"   - {spot['name']} ({spot['distance_km']:.1f} km)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 6: Geocoding endpoint (requires API key)
    print("\n⚠️  Testing /api/mapping/geocode (requires API key)...")
    try:
        response = requests.post(
            f"{base_url}/api/mapping/geocode",
            json={"address": "Place du Capitole, Toulouse"}
        )
        if response.status_code == 503:
            print("   Service unavailable - API key not configured")
        elif response.status_code == 200:
            print("   ✅ Geocoding service working!")
        else:
            print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("API test complete!")


if __name__ == "__main__":
    test_api()