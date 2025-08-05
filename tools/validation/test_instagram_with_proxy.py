#!/usr/bin/env python3
"""
Test Instagram scraper with proxy and session handling
Handles Instagram security challenges
"""

import sys
from pathlib import Path
import json
import time
import os

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from instagrapi import Client
    from instagrapi.exceptions import (
        LoginRequired, 
        ChallengeRequired,
        TwoFactorRequired,
        BadPassword,
        UnknownError
    )
except ImportError:
    print("ERROR: instagrapi not installed")
    sys.exit(1)


def handle_challenge(client, challenge_code=None):
    """Handle Instagram challenges (captcha, SMS, etc)"""
    print("\n⚠️  Instagram Challenge Required!")
    
    if challenge_code:
        # If we have a code, try to submit it
        try:
            client.challenge_code(challenge_code)
            print("✅ Challenge completed!")
            return True
        except Exception as e:
            print(f"❌ Challenge failed: {e}")
            return False
    else:
        print("Instagram is asking for verification.")
        print("Options:")
        print("1. Check your email for a verification code")
        print("2. Use Instagram app to verify this login")
        print("3. Try again from a different network")
        return False


def test_instagram_with_session():
    """Test Instagram with better session and error handling"""
    print("=" * 60)
    print("📸 INSTAGRAM SCRAPER WITH SESSION HANDLING")
    print("=" * 60)
    print()
    
    # Get credentials
    username = os.environ.get('INSTAGRAM_USERNAME')
    password = os.environ.get('INSTAGRAM_PASSWORD')
    
    if not username or not password:
        print("❌ No credentials found in environment")
        return
        
    print(f"✅ Using account: {username}")
    
    # Create client with specific settings
    cl = Client()
    
    # Set delay between requests
    cl.delay_range = [1, 3]
    
    # Try to use a different device/user agent
    cl.set_device({
        "app_version": "269.0.0.18.75",
        "android_version": 29,
        "android_release": "10",
        "dpi": "480dpi",
        "resolution": "1080x2340",
        "manufacturer": "Samsung",
        "device": "SM-G973F",
        "model": "Galaxy S10",
        "cpu": "Exynos 9820",
        "version_code": 314665256
    })
    
    # Set user agent
    cl.set_user_agent("Instagram 269.0.0.18.75 Android (29/10; 480dpi; 1080x2340; Samsung; SM-G973F; Galaxy S10; Exynos 9820)")
    
    session_file = Path("instagram_session_samsung.json")
    login_success = False
    
    # Try to load existing session
    if session_file.exists():
        try:
            print("\n📁 Loading existing session...")
            cl.load_settings(session_file)
            cl.login(username, password)
            print("✅ Logged in with existing session!")
            login_success = True
        except Exception as e:
            print(f"⚠️  Session invalid: {e}")
            session_file.unlink()  # Delete invalid session
    
    # Fresh login if needed
    if not login_success:
        try:
            print("\n🔐 Attempting fresh login...")
            print("   (This may trigger security checks)")
            
            # Add a delay before login
            time.sleep(2)
            
            # Try login
            cl.login(username, password)
            
            # Save session
            cl.dump_settings(session_file)
            print("✅ Login successful! Session saved.")
            login_success = True
            
        except ChallengeRequired as e:
            print(f"\n⚠️  Challenge Required: {e}")
            handle_challenge(cl)
            
        except BadPassword:
            print("\n❌ Invalid password")
            
        except Exception as e:
            print(f"\n❌ Login failed: {e}")
            
            # Provide troubleshooting steps
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Login to Instagram via web/app first")
            print("2. Verify your account isn't restricted")
            print("3. Try enabling 'Login from other devices' in Instagram settings")
            print("4. Wait a few hours if you've had multiple failed attempts")
            print("5. Consider using app-specific password if 2FA is enabled")
    
    # If login successful, try to get some data
    if login_success:
        print("\n" + "=" * 60)
        print("✅ TESTING DATA ACCESS")
        print("=" * 60)
        
        try:
            # Test 1: Get your own profile info
            print("\n👤 Getting your profile info...")
            me = cl.account_info()
            print(f"   Username: @{me.username}")
            print(f"   Full name: {me.full_name}")
            print(f"   Followers: {me.follower_count}")
            
            # Test 2: Search for a location
            print("\n📍 Searching for Toulouse locations...")
            locations = cl.fbsearch_places("Toulouse France", 5)
            if locations:
                print(f"   Found {len(locations)} locations:")
                for loc in locations[:3]:
                    print(f"   - {loc.name}")
            
            # Test 3: Get location posts
            if locations:
                print(f"\n🏞️ Getting posts from {locations[0].name}...")
                try:
                    # Get location ID first
                    location_info = cl.location_info(locations[0].pk)
                    medias = cl.location_medias_recent(locations[0].pk, amount=5)
                    print(f"   Found {len(medias)} recent posts")
                    
                    for media in medias[:2]:
                        print(f"\n   Post by @{media.user.username}")
                        print(f"   Likes: {media.like_count}")
                        print(f"   Caption: {media.caption_text[:100]}...")
                        
                except Exception as e:
                    print(f"   ⚠️  Could not get posts: {e}")
                    
        except Exception as e:
            print(f"\n❌ Error accessing data: {e}")
    
    print("\n" + "=" * 60)
    print("📊 SESSION STATUS")
    print("=" * 60)
    
    if session_file.exists():
        print(f"✅ Session file saved: {session_file}")
        print("   You can now use instagram_real_scraper.py with this session")
    else:
        print("❌ No valid session established")
        
    # Save login status
    status = {
        "login_success": login_success,
        "session_file": str(session_file) if session_file.exists() else None,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("instagram_login_status.json", "w") as f:
        json.dump(status, f, indent=2)


if __name__ == "__main__":
    test_instagram_with_session()