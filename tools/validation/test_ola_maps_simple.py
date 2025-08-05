#!/usr/bin/env python3
"""Simple test for Ola Maps integration without scraper dependencies"""

import os
import sys
from pathlib import Path
import requests
import json
from datetime import datetime

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.scrapers.geocoding_mixin import GeocodingMixin

def test_ola_maps():
    """Test basic Ola Maps functionality"""
    print("=" * 60)
    print("🔧 OLA MAPS SIMPLE INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Initialize geocoder
    geocoder = GeocodingMixin()
    
    # Test 1: Check API key
    has_key = bool(geocoder.ola_api_key)
    print(f"1. API Key Configuration: {'✅ CONFIGURED' if has_key else '❌ NOT SET'}")
    if not has_key:
        print("   Set with: export OLA_MAPS_API_KEY='your-key-here'")
        print("\n⚠️  Cannot proceed with API tests without key.")
        return
    
    print(f"   Key length: {len(geocoder.ola_api_key)} characters")
    print()
    
    # Test 2: Geocoding
    print("2. Testing Geocoding...")
    test_address = "Place du Capitole, Toulouse, France"
    result = geocoder.geocode_address(test_address)
    
    if result:
        print(f"   ✅ Success: {test_address}")
        print(f"   Coordinates: {result['latitude']:.4f}, {result['longitude']:.4f}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Formatted: {result['formatted_address']}")
    else:
        print(f"   ❌ Failed to geocode address")
    print()
    
    # Test 3: Reverse Geocoding
    print("3. Testing Reverse Geocoding...")
    test_coords = (43.6047, 1.4442)  # Toulouse center
    address = geocoder.reverse_geocode(*test_coords)
    
    if address:
        print(f"   ✅ Success: {test_coords}")
        print(f"   Address: {address}")
    else:
        print(f"   ❌ Failed to reverse geocode")
    print()
    
    # Test 4: Elevation
    print("4. Testing Elevation Lookup...")
    elevation = geocoder.get_elevation(*test_coords)
    
    if elevation is not None:
        print(f"   ✅ Success: {test_coords}")
        print(f"   Elevation: {elevation}m")
    else:
        print(f"   ❌ Failed to get elevation")
    print()
    
    # Test 5: Nearby Search
    print("5. Testing Nearby Places Search...")
    places = geocoder.find_nearby_places(*test_coords, radius=500)
    
    if places:
        print(f"   ✅ Found {len(places)} places within 500m")
        for place in places[:3]:
            print(f"   - {place.get('name', 'Unknown')}")
    else:
        print(f"   ❌ No places found")
    print()
    
    # Test 6: API Server
    print("6. Testing API Server...")
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            print("   ✅ API server is running")
            data = response.json()
            print(f"   Version: {data.get('version')}")
            print(f"   Mapping endpoints available: {'/api/mapping' in str(data)}")
        else:
            print("   ❌ API server returned error")
    except requests.exceptions.ConnectionError:
        print("   ❌ API server not running")
        print("   Start with: cd src/backend && python main.py")
    print()
    
    # Test 7: Database
    print("7. Testing Database...")
    import sqlite3
    db_path = Path(__file__).parent / "data" / "occitanie_spots.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check elevation column exists
        cursor.execute("PRAGMA table_info(spots)")
        columns = [col[1] for col in cursor.fetchall()]
        
        has_elevation = 'elevation' in columns
        has_geocoding = 'geocoding_confidence' in columns
        has_address = 'address' in columns
        
        print(f"   {'✅' if has_elevation else '❌'} Elevation column exists")
        print(f"   {'✅' if has_geocoding else '❌'} Geocoding confidence column exists")
        print(f"   {'✅' if has_address else '❌'} Address column exists")
        
        # Count spots with elevation
        cursor.execute("SELECT COUNT(*) FROM spots WHERE elevation IS NOT NULL")
        spots_with_elevation = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots")
        total_spots = cursor.fetchone()[0]
        
        print(f"   Spots with elevation: {spots_with_elevation}/{total_spots} ({spots_with_elevation/total_spots*100:.1f}%)")
        
        conn.close()
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print("\nNext steps:")
    if has_key:
        print("1. Run the elevation enrichment script:")
        print("   python scripts/enrich_spots_with_elevation.py")
        print("2. Start the API server:")
        print("   cd src/backend && python main.py")
        print("3. Test the mapping endpoints:")
        print("   http://localhost:8000/docs")
    else:
        print("1. Get an Ola Maps API key")
        print("2. Set: export OLA_MAPS_API_KEY='your-key'")
        print("3. Run this test again")


if __name__ == "__main__":
    test_ola_maps()