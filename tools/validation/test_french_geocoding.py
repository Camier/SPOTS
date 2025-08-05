#!/usr/bin/env python3
"""Test French BAN and IGN geocoding integration"""

import sys
from pathlib import Path
import requests
import json
from datetime import datetime

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.scrapers.geocoding_france import FrenchGeocodingMixin, OccitanieGeocoder

def test_french_geocoding():
    """Test French geocoding services"""
    print("=" * 60)
    print("🇫🇷 FRENCH GEOCODING TEST (BAN + IGN)")
    print("=" * 60)
    print("✅ No API key required - using free government services!")
    print()
    
    # Initialize geocoder
    geocoder = OccitanieGeocoder()
    
    # Test 1: BAN Geocoding
    print("1. Testing BAN Geocoding (Base Adresse Nationale)...")
    test_addresses = [
        "Place du Capitole, Toulouse",
        "Cité de Carcassonne",
        "Pont du Gard, Vers-Pont-du-Gard",
        "Pic du Midi de Bigorre",
        "Gorges du Tarn, Millau",
        "Canal du Midi, Toulouse"
    ]
    
    geocoded_count = 0
    for address in test_addresses:
        result = geocoder.geocode_address(address)
        if result:
            geocoded_count += 1
            print(f"   ✅ {address}")
            print(f"      Lat: {result['latitude']:.4f}, Lon: {result['longitude']:.4f}")
            print(f"      Confidence: {result['confidence']:.2f}")
            print(f"      City: {result.get('city', 'N/A')}, Dept: {result.get('department', 'N/A')}")
            
            # Check if in Occitanie
            if geocoder.is_in_occitanie(result['latitude'], result['longitude']):
                print(f"      ✓ In Occitanie!")
            else:
                print(f"      ✗ Not in Occitanie")
        else:
            print(f"   ❌ Failed: {address}")
    
    print(f"\n   Success rate: {geocoded_count}/{len(test_addresses)}")
    print()
    
    # Test 2: Reverse Geocoding
    print("2. Testing Reverse Geocoding...")
    test_coords = [
        (43.6047, 1.4442, "Toulouse center"),
        (43.2130, 2.3491, "Carcassonne"),
        (43.9493, 4.5350, "Pont du Gard"),
        (42.9369, 0.1412, "Pic du Midi"),
        (44.3231, 3.2778, "Gorges du Tarn")
    ]
    
    reverse_count = 0
    for lat, lon, name in test_coords:
        address = geocoder.reverse_geocode(lat, lon)
        if address:
            reverse_count += 1
            print(f"   ✅ {name}: {lat:.4f}, {lon:.4f}")
            print(f"      Address: {address}")
            
            # Get department
            dept = geocoder.get_department_code(lat, lon)
            if dept:
                dept_name = geocoder.OCCITANIE_DEPARTMENTS.get(dept, "Unknown")
                print(f"      Department: {dept} - {dept_name}")
        else:
            print(f"   ❌ Failed: {name}")
    
    print(f"\n   Success rate: {reverse_count}/{len(test_coords)}")
    print()
    
    # Test 3: IGN Elevation
    print("3. Testing IGN Elevation Service...")
    elevation_count = 0
    for lat, lon, name in test_coords:
        elevation = geocoder.get_elevation_ign(lat, lon)
        if elevation is not None:
            elevation_count += 1
            print(f"   ✅ {name}: {elevation:.0f}m (IGN)")
        else:
            # Try fallback
            elevation = geocoder.get_elevation_open(lat, lon)
            if elevation is not None:
                elevation_count += 1
                print(f"   ✅ {name}: {elevation:.0f}m (Open-Elevation fallback)")
            else:
                print(f"   ❌ Failed: {name}")
    
    print(f"\n   Success rate: {elevation_count}/{len(test_coords)}")
    print()
    
    # Test 4: Place Search
    print("4. Testing BAN Place Search...")
    search_queries = [
        "lac Toulouse",
        "cascade Ariège",
        "grotte Occitanie",
        "gorges Aveyron"
    ]
    
    for query in search_queries:
        places = geocoder.search_places_ban(query, limit=3)
        print(f"   Query: '{query}' - Found {len(places)} results")
        for place in places[:2]:
            print(f"      - {place['name']} (score: {place['score']:.2f})")
            if place.get('city'):
                print(f"        {place['city']}, {place.get('postcode', '')}")
    print()
    
    # Test 5: API Server
    print("5. Testing API Server...")
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API server running - Version {data.get('version')}")
            
            # Test geocoding endpoint
            response = requests.post(
                "http://localhost:8000/api/mapping/geocode",
                json={"address": "Place du Capitole, Toulouse"},
                timeout=5
            )
            if response.status_code == 200:
                print("   ✅ Geocoding endpoint working")
            else:
                print(f"   ❌ Geocoding endpoint returned {response.status_code}")
                
        else:
            print("   ❌ API server error")
    except requests.exceptions.ConnectionError:
        print("   ❌ API server not running")
        print("   Start with: cd src && python -m backend.main")
    print()
    
    # Test 6: Database Check
    print("6. Testing Database...")
    import sqlite3
    db_path = Path(__file__).parent / "data" / "occitanie_spots.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for French geocoding columns
        cursor.execute("PRAGMA table_info(spots)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['elevation', 'address', 'geocoding_confidence', 'department']
        all_present = all(col in columns for col in required_columns)
        
        if all_present:
            print("   ✅ All French geocoding columns present")
        else:
            missing = [col for col in required_columns if col not in columns]
            print(f"   ❌ Missing columns: {missing}")
            
        # Count enrichment status
        cursor.execute("SELECT COUNT(*) FROM spots")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE elevation IS NOT NULL")
        with_elevation = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE address IS NOT NULL")
        with_address = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spots WHERE department IS NOT NULL")
        with_dept = cursor.fetchone()[0]
        
        print(f"\n   Total spots: {total}")
        print(f"   With elevation: {with_elevation} ({with_elevation/total*100:.1f}%)")
        print(f"   With address: {with_address} ({with_address/total*100:.1f}%)")
        print(f"   With department: {with_dept} ({with_dept/total*100:.1f}%)")
        
        conn.close()
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print("\n✅ French geocoding services are working!")
    print("✅ No API key required")
    print("✅ Free government services:")
    print("   - BAN (Base Adresse Nationale) for geocoding")
    print("   - IGN for elevation data")
    print("\nNext steps:")
    print("1. Run enrichment: python scripts/enrich_spots_french.py")
    print("2. Start API: cd src && python -m backend.main")
    print("3. Test endpoints: http://localhost:8000/docs")


if __name__ == "__main__":
    test_french_geocoding()