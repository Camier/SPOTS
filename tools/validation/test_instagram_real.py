#!/usr/bin/env python3
"""
Test script for REAL Instagram scraper
This fetches actual data from Instagram - no simulations!
"""

import sys
from pathlib import Path
import json
import os

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.scrapers.instagram_real_scraper import RealInstagramScraper


def test_real_instagram_scraper():
    """Test real Instagram scraper with actual data"""
    print("=" * 60)
    print("📸 REAL INSTAGRAM SCRAPER TEST")
    print("=" * 60)
    print()
    
    # Check for credentials
    username = os.environ.get('INSTAGRAM_USERNAME')
    password = os.environ.get('INSTAGRAM_PASSWORD')
    
    if not username or not password:
        print("❌ ERROR: Instagram credentials not found!")
        print("\nPlease set environment variables:")
        print("  export INSTAGRAM_USERNAME='your_username'")
        print("  export INSTAGRAM_PASSWORD='your_password'")
        print("\nOr create a .env file with:")
        print("  INSTAGRAM_USERNAME=your_username")
        print("  INSTAGRAM_PASSWORD=your_password")
        return
        
    print(f"✅ Using Instagram account: @{username}")
    print()
    
    try:
        # Create scraper with real authentication
        print("🔐 Authenticating with Instagram...")
        scraper = RealInstagramScraper(
            username=username,
            password=password,
            session_file="instagram_session.json"
        )
        print("✅ Authentication successful!")
        print()
        
        # Test 1: Search for specific locations
        print("🔍 TEST 1: Searching for Occitanie locations")
        print("-" * 60)
        
        test_locations = ["Lac de Salagou", "Gorges du Tarn", "Pic du Midi"]
        for location in test_locations:
            results = scraper.search_location_by_name(location)
            if results:
                print(f"\n📍 Found {len(results)} results for '{location}':")
                for r in results[:2]:  # Show first 2
                    print(f"   - {r['name']} ({r['lat']:.4f}, {r['lng']:.4f})")
            else:
                print(f"\n❌ No results for '{location}'")
                
        # Test 2: Scrape by location
        print("\n\n🏞️ TEST 2: Scraping posts from locations")
        print("-" * 60)
        
        location_spots = scraper.scrape(limit=10, method="location")
        print(f"\nFound {len(location_spots)} real spots from locations:")
        
        for i, spot in enumerate(location_spots[:5], 1):
            print(f"\n{i}. {spot.get('name', 'Unknown')}")
            print(f"   📍 Location: {spot.get('address_hint', 'Unknown')}")
            print(f"   🏷️ Type: {spot.get('type', 'unknown')}")
            print(f"   🏃 Activities: {', '.join(spot.get('activities', []))}")
            print(f"   👤 Posted by: @{spot.get('metadata', {}).get('user', 'unknown')}")
            print(f"   ❤️ Likes: {spot.get('metadata', {}).get('likes', 0)}")
            print(f"   🔗 Link: {spot.get('source_url', 'N/A')}")
            
        # Test 3: Scrape by hashtag
        print("\n\n#️⃣ TEST 3: Scraping posts from hashtags")
        print("-" * 60)
        
        hashtag_spots = scraper.scrape(limit=10, method="hashtag")
        print(f"\nFound {len(hashtag_spots)} real spots from hashtags:")
        
        for i, spot in enumerate(hashtag_spots[:5], 1):
            print(f"\n{i}. {spot.get('name', 'Unknown')}")
            print(f"   📍 Department: {spot.get('department', 'Unknown')}")
            print(f"   🏷️ Type: {spot.get('type', 'unknown')}")
            print(f"   #️⃣ Hashtag: #{spot.get('metadata', {}).get('hashtag', 'unknown')}")
            print(f"   📈 Relevance: {spot.get('metadata', {}).get('relevance_score', 0):.2f}")
            print(f"   🔗 Link: {spot.get('source_url', 'N/A')}")
            
        # Test 4: Get posts from outdoor accounts
        print("\n\n👥 TEST 4: Getting posts from outdoor accounts")
        print("-" * 60)
        
        outdoor_accounts = ["randonnee_pyrenees", "toulouse_outdoor", "occitanie_tourism"]
        for account in outdoor_accounts:
            try:
                posts = scraper.get_user_posts(account, limit=3)
                if posts:
                    print(f"\n✅ Found {len(posts)} outdoor posts from @{account}")
                else:
                    print(f"\n❌ No outdoor posts found from @{account}")
            except Exception as e:
                print(f"\n⚠️ Could not access @{account}: {e}")
                
        # Summary
        print("\n\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        total_spots = len(location_spots) + len(hashtag_spots)
        print(f"\n✅ Total real spots found: {total_spots}")
        print(f"   - From locations: {len(location_spots)}")
        print(f"   - From hashtags: {len(hashtag_spots)}")
        
        # Show departments distribution
        departments = {}
        for spot in location_spots + hashtag_spots:
            dept = spot.get('department', 'Unknown')
            departments[dept] = departments.get(dept, 0) + 1
            
        print("\n🗺️ Department distribution:")
        for dept, count in sorted(departments.items()):
            if dept in scraper.OCCITANIE_DEPARTMENTS:
                dept_name = scraper.OCCITANIE_DEPARTMENTS[dept]
                print(f"   {dept} - {dept_name}: {count} spots")
            elif dept != 'Unknown':
                print(f"   {dept}: {count} spots")
                
        # Save sample data
        sample_data = {
            "timestamp": datetime.now().isoformat(),
            "total_spots": total_spots,
            "location_spots": location_spots[:3],
            "hashtag_spots": hashtag_spots[:3],
        }
        
        with open("instagram_real_sample.json", "w", encoding="utf-8") as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 Sample data saved to: instagram_real_sample.json")
        
    except ImportError:
        print("❌ ERROR: instagrapi not installed!")
        print("\nInstall it with:")
        print("  pip install instagrapi")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure you have:")
        print("1. Valid Instagram credentials")
        print("2. instagrapi installed (pip install instagrapi)")
        print("3. Internet connection")
        print("4. Instagram account is not blocked/restricted")


if __name__ == "__main__":
    from datetime import datetime
    
    # Try to load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    test_real_instagram_scraper()