#!/usr/bin/env python3
"""
Simple test to verify Instagram connectivity without login
Tests public access methods that don't require authentication
"""

import sys
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from instagrapi import Client
    from instagrapi.exceptions import ClientError
except ImportError:
    print("ERROR: instagrapi not installed")
    sys.exit(1)


def test_public_instagram():
    """Test public Instagram access without login"""
    print("=" * 60)
    print("📸 TESTING PUBLIC INSTAGRAM ACCESS")
    print("=" * 60)
    print()
    
    cl = Client()
    
    # Test 1: Search for locations without login
    print("🔍 TEST 1: Searching public locations")
    print("-" * 60)
    
    test_locations = ["Toulouse", "Montpellier", "Carcassonne"]
    
    for location in test_locations:
        try:
            print(f"\nSearching for: {location}")
            # Note: Some methods may require login, let's see what works
            results = cl.fbsearch_places(location, 3)
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for r in results:
                    print(f"   - {r.name} ({r.subtitle})")
            else:
                print(f"❌ No results found")
                
        except ClientError as e:
            if "login_required" in str(e).lower():
                print(f"⚠️  Login required for location search")
            else:
                print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Test 2: Try to get public user info
    print("\n\n👤 TEST 2: Getting public user info")
    print("-" * 60)
    
    test_users = ["natgeo", "toulouse", "occitanie_tourisme"]
    
    for username in test_users:
        try:
            print(f"\nLooking up @{username}")
            # This might work without login
            user_id = cl.user_id_from_username(username)
            print(f"✅ Found user ID: {user_id}")
            
        except ClientError as e:
            if "login_required" in str(e).lower():
                print(f"⚠️  Login required for user lookup")
            else:
                print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Test 3: Alternative approach - direct web access
    print("\n\n🌐 TEST 3: Direct web access approach")
    print("-" * 60)
    
    import requests
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Try to access Instagram web
    try:
        print("\nChecking Instagram web accessibility...")
        response = requests.get('https://www.instagram.com/', headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Instagram web is accessible")
        else:
            print(f"⚠️  Instagram returned status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Cannot access Instagram: {e}")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print("\nMost Instagram API methods require authentication.")
    print("For real data scraping, you need:")
    print("1. Valid Instagram account credentials")
    print("2. Use the authenticated scraper (instagram_real_scraper.py)")
    print("3. Or use web scraping with Selenium/Playwright")


if __name__ == "__main__":
    test_public_instagram()