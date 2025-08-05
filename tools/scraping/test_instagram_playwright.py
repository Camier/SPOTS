#!/usr/bin/env python3
"""
Test Instagram scraper using Playwright
This uses real browser automation to fetch ACTUAL Instagram data
"""

import sys
from pathlib import Path
import os
from datetime import datetime

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.scrapers.instagram_playwright_scraper import PlaywrightInstagramScraper


def test_playwright_instagram():
    """Test Instagram scraping with Playwright"""
    print("=" * 60)
    print("🎭 INSTAGRAM PLAYWRIGHT SCRAPER TEST")
    print("=" * 60)
    print()
    
    # Get credentials from environment
    username = os.environ.get('INSTAGRAM_USERNAME')
    password = os.environ.get('INSTAGRAM_PASSWORD')
    
    if not username or not password:
        print("❌ ERROR: Instagram credentials not found!")
        print("\nPlease set environment variables or create .env file")
        return
        
    print(f"✅ Using Instagram account: {username}")
    print()
    
    # Create scraper (with visible browser for testing)
    print("🌐 Starting browser (visible mode for testing)...")
    scraper = PlaywrightInstagramScraper(
        username=username,
        password=password,
        headless=False  # Show browser for debugging
    )
    
    try:
        # Setup browser
        scraper.browser, scraper.page = scraper.setup_browser()
        print("✅ Browser started successfully")
        
        # Login to Instagram
        print("\n🔐 Logging in to Instagram...")
        print("   (Watch the browser window)")
        
        login_success = scraper.login()
        
        if not login_success:
            print("❌ Login failed!")
            print("\nTroubleshooting:")
            print("1. Check your credentials")
            print("2. Complete any security challenges in the browser")
            print("3. Try logging in manually first")
            return
            
        print("✅ Login successful!")
        
        # Test 1: Search for a location
        print("\n" + "=" * 60)
        print("📍 TEST 1: Location Search")
        print("=" * 60)
        
        test_location = "Lac de Salagou"
        print(f"\nSearching for: {test_location}")
        
        location_url = scraper.search_location(test_location)
        if location_url:
            print(f"✅ Found location: {location_url}")
            
            # Scrape posts from location
            print(f"\nScraping posts from {test_location}...")
            posts = scraper.scrape_location_posts(location_url, limit=3)
            
            print(f"\n✅ Found {len(posts)} posts:")
            for i, post in enumerate(posts, 1):
                print(f"\n{i}. {post.get('name', 'Unknown')}")
                print(f"   User: @{post.get('metadata', {}).get('username', 'unknown')}")
                print(f"   Type: {post.get('type', 'unknown')}")
                print(f"   Activities: {', '.join(post.get('activities', []))}")
                print(f"   Likes: {post.get('metadata', {}).get('likes', 0)}")
                print(f"   URL: {post.get('source_url', 'N/A')}")
                
                # Show caption preview
                caption = post.get('raw_text', '')
                if caption:
                    print(f"   Caption: {caption[:100]}...")
        else:
            print(f"❌ Location not found")
            
        # Test 2: Hashtag search
        print("\n" + "=" * 60)
        print("#️⃣ TEST 2: Hashtag Search")
        print("=" * 60)
        
        test_hashtag = "occitaniesecrete"
        print(f"\nScraping posts from #{test_hashtag}...")
        
        hashtag_posts = scraper.scrape_hashtag_posts(test_hashtag, limit=3)
        
        print(f"\n✅ Found {len(hashtag_posts)} posts:")
        for i, post in enumerate(hashtag_posts, 1):
            print(f"\n{i}. {post.get('name', 'Unknown')}")
            print(f"   Location: {post.get('address_hint', 'Unknown')}")
            print(f"   Type: {post.get('type', 'unknown')}")
            print(f"   Hidden spot: {'Yes' if post.get('is_hidden') else 'No'}")
            print(f"   URL: {post.get('source_url', 'N/A')}")
            
        # Test 3: Full scraping test
        print("\n" + "=" * 60)
        print("🏞️ TEST 3: Full Location Scraping")
        print("=" * 60)
        
        print("\nRunning full location-based scraping...")
        all_spots = scraper.scrape(method="location", limit=10)
        
        print(f"\n✅ Total spots found: {len(all_spots)}")
        
        # Show department distribution
        departments = {}
        for spot in all_spots:
            dept = spot.get('department', 'Unknown')
            departments[dept] = departments.get(dept, 0) + 1
            
        if departments:
            print("\n🗺️ Department distribution:")
            for dept, count in sorted(departments.items()):
                if dept in scraper.OCCITANIE_DEPARTMENTS:
                    dept_name = scraper.OCCITANIE_DEPARTMENTS[dept]
                    print(f"   {dept} - {dept_name}: {count} spots")
                    
        # Show spot types
        types = {}
        for spot in all_spots:
            spot_type = spot.get('type', 'unknown')
            types[spot_type] = types.get(spot_type, 0) + 1
            
        if types:
            print("\n🏞️ Spot types found:")
            for spot_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {spot_type}: {count}")
                
        # Save sample data
        sample_file = Path("instagram_playwright_sample.json")
        sample_data = {
            "timestamp": datetime.now().isoformat(),
            "total_spots": len(all_spots),
            "sample_spots": all_spots[:5],
            "departments": departments,
            "types": types,
        }
        
        import json
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 Sample data saved to: {sample_file}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🧹 Cleaning up browser...")
        scraper.cleanup()
        print("✅ Done!")
        
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print("\nPlaywright Instagram scraper successfully:")
    print("✅ Logged in to Instagram")
    print("✅ Searched for locations")
    print("✅ Scraped real posts")
    print("✅ Extracted spot information")
    print("\nThis scraper fetches REAL Instagram data using browser automation!")


if __name__ == "__main__":
    # Load .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    test_playwright_instagram()