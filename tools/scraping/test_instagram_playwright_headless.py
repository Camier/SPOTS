#!/usr/bin/env python3
"""
Test Instagram scraper using Playwright in headless mode
This uses real browser automation to fetch ACTUAL Instagram data
"""

import sys
from pathlib import Path
import os
from datetime import datetime
import json

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend.scrapers.instagram_playwright_scraper import PlaywrightInstagramScraper


def test_playwright_headless():
    """Test Instagram scraping with Playwright in headless mode"""
    print("=" * 60)
    print("🎭 INSTAGRAM PLAYWRIGHT SCRAPER TEST (HEADLESS)")
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
    
    # Create scraper in headless mode
    print("🌐 Starting browser in headless mode...")
    scraper = PlaywrightInstagramScraper(
        username=username,
        password=password,
        headless=True  # Run in background
    )
    
    try:
        # Setup browser
        scraper.browser, scraper.page = scraper.setup_browser()
        print("✅ Browser started successfully")
        
        # Quick test - just try to access Instagram
        print("\n🔐 Attempting to access Instagram...")
        scraper.page.goto('https://www.instagram.com/', wait_until='domcontentloaded')
        
        print("✅ Instagram page loaded")
        
        # Check if we need to handle cookies
        try:
            cookie_button = scraper.page.locator('button:has-text("Allow essential cookies")').or_(
                scraper.page.locator('button:has-text("Autoriser les cookies essentiels")')
            )
            if cookie_button.is_visible(timeout=3000):
                cookie_button.click()
                print("✅ Handled cookie banner")
        except:
            print("ℹ️  No cookie banner found")
        
        # Try login
        print("\n🔐 Attempting login...")
        login_success = scraper.login()
        
        if login_success:
            print("✅ Login successful!")
            
            # Quick test - search for one location
            print("\n📍 Testing location search...")
            test_location = "Toulouse"
            print(f"Searching for: {test_location}")
            
            location_url = scraper.search_location(test_location)
            if location_url:
                print(f"✅ Found location URL: {location_url}")
                
                # Try to get one post
                print("\nGetting 1 post from location...")
                posts = scraper.scrape_location_posts(location_url, limit=1)
                
                if posts:
                    print(f"✅ Successfully scraped {len(posts)} post")
                    post = posts[0]
                    print(f"\n📸 Post details:")
                    print(f"   Name: {post.get('name', 'Unknown')}")
                    print(f"   User: @{post.get('metadata', {}).get('username', 'unknown')}")
                    print(f"   URL: {post.get('source_url', 'N/A')}")
                else:
                    print("❌ No posts found")
            else:
                print("❌ Location not found")
                
        else:
            print("❌ Login failed!")
            print("\nPossible reasons:")
            print("1. Instagram may be blocking automated logins")
            print("2. Credentials might be incorrect")
            print("3. Account might need verification")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🧹 Cleaning up browser...")
        scraper.cleanup()
        print("✅ Done!")
        
    print("\n" + "=" * 60)
    print("📊 TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    # Load .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    # First install browser if needed
    print("🔧 Checking Playwright browser installation...")
    import subprocess
    try:
        result = subprocess.run(
            ["python", "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        if result.returncode == 0:
            print("✅ Browser installed/verified")
        else:
            print(f"⚠️  Browser installation issue: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⚠️  Browser installation is taking too long, proceeding anyway...")
    except Exception as e:
        print(f"⚠️  Could not verify browser: {e}")
    
    print()
    test_playwright_headless()