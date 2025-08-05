#!/usr/bin/env python3
"""Test script for ADRESSE-PREMIUM geocoding"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backend.scrapers.geocoding_france import OccitanieGeocoder
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def test_premium_geocoding():
    """Test premium geocoding features"""
    geocoder = OccitanieGeocoder()
    
    print("🔍 Testing ADRESSE-PREMIUM Geocoding")
    print(f"Premium enabled: {geocoder.premium_service.enabled}")
    print("-" * 50)
    
    # Test addresses with increasing complexity
    test_addresses = [
        # Simple addresses
        "1 Place du Capitole, Toulouse",
        "Tour Eiffel, Paris",
        
        # Rural/remote addresses
        "Refuge du Néouvielle, Hautes-Pyrénées",
        "Cascade d'Ars, Ariège",
        
        # Historical/lieu-dit
        "Château de Peyrepertuse, Aude",
        "Gorges du Tarn, Lozère",
        
        # Ambiguous addresses
        "Lac Bleu, Pyrénées",
        "Grotte, Ariège"
    ]
    
    results = []
    
    for address in test_addresses:
        print(f"\n📍 Testing: {address}")
        result = geocoder.geocode_address(address)
        
        if result:
            print(f"  ✅ Found: {result['formatted_address']}")
            print(f"  📊 Confidence: {result['confidence']:.2f}")
            print(f"  🎯 Precision: {result.get('precision', 'unknown')}")
            print(f"  📐 Coordinates: {result['latitude']:.6f}, {result['longitude']:.6f}")
            
            # Premium-specific fields
            if result.get('precision') == 'premium':
                print(f"  🏠 House number: {result.get('housenumber', 'N/A')}")
                print(f"  🛣️ Street: {result.get('street', 'N/A')}")
                print(f"  📍 Entrance: {result.get('entrance', 'N/A')}")
                print(f"  📜 Old name: {result.get('oldcity', 'N/A')}")
                print(f"  ⭐ Quality: {result.get('quality', 'N/A')}")
            
            results.append({
                'query': address,
                'success': True,
                'result': result
            })
        else:
            print(f"  ❌ Not found")
            results.append({
                'query': address,
                'success': False
            })
    
    # Test reverse geocoding
    print("\n" + "="*50)
    print("🔄 Testing Reverse Geocoding")
    print("-" * 50)
    
    test_coords = [
        (43.604652, 1.444209),  # Toulouse center
        (42.871937, 0.158039),  # Mountain refuge area
        (43.116669, 2.985000)   # Rural area
    ]
    
    for lat, lon in test_coords:
        print(f"\n📍 Reverse geocoding: {lat:.6f}, {lon:.6f}")
        address = geocoder.reverse_geocode(lat, lon)
        
        if address:
            print(f"  ✅ Address: {address}")
            
            # Get detailed info if premium
            if geocoder.premium_service.enabled:
                detailed = geocoder.premium_service.reverse_geocode_premium(lat, lon)
                if detailed:
                    print(f"  🏠 Details:")
                    print(f"     - Type: {detailed.get('type', 'N/A')}")
                    print(f"     - Distance: {detailed.get('distance', 0):.1f}m")
                    print(f"     - Precision: {detailed.get('precision', 'N/A')}")
        else:
            print(f"  ❌ No address found")
    
    # Test POI search (premium only)
    if geocoder.premium_service.enabled:
        print("\n" + "="*50)
        print("🎯 Testing POI Search (Premium Feature)")
        print("-" * 50)
        
        poi_searches = [
            ("refuge", 42.871937, 0.158039),  # Mountain refuges
            ("cascade", 42.7, 1.4),            # Waterfalls
            ("grotte", 43.0, 1.5)              # Caves
        ]
        
        for query, lat, lon in poi_searches:
            print(f"\n🔍 Searching for '{query}' near {lat:.2f}, {lon:.2f}")
            pois = geocoder.premium_service.search_poi_premium(query, lat, lon, radius=5000)
            
            if pois:
                print(f"  ✅ Found {len(pois)} results:")
                for poi in pois[:3]:  # Show first 3
                    print(f"     📍 {poi['name']} ({poi['type']}) - {poi['distance']:.0f}m away")
            else:
                print(f"  ❌ No POIs found")
    
    # Summary
    print("\n" + "="*50)
    print("📊 Summary")
    print("-" * 50)
    
    success_count = sum(1 for r in results if r['success'])
    premium_count = sum(1 for r in results if r.get('result', {}).get('precision') == 'premium')
    
    print(f"Total tests: {len(results)}")
    print(f"Successful: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)")
    if geocoder.premium_service.enabled:
        print(f"Premium results: {premium_count}/{success_count}")
    else:
        print("⚠️  Premium service not enabled - using standard BAN")
    
    # Save results
    output_file = "premium_geocoding_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Results saved to {output_file}")

if __name__ == "__main__":
    test_premium_geocoding()