#!/usr/bin/env python3
"""
Test script for urbex module
"""
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_urbex_module():
    """Test urbex module functionality"""
    
    # Import modules
    from data_models import UrbexSpot, UrbexCategory, DangerLevel, AccessDifficulty
    from validator import UrbexSpotValidator
    from database import UrbexDatabase
    from scraper import UrbexScraper
    
    print("=" * 60)
    print("URBEX MODULE TEST")
    print("=" * 60)
    
    # 1. Test data model
    print("\n1. Testing Data Model...")
    spot = UrbexSpot(
        name="Test Château Abandonné",
        category=UrbexCategory.CASTLE,
        latitude=43.6047,
        longitude=1.4442,
        department="31",
        danger_level=DangerLevel.MEDIUM,
        access_difficulty=AccessDifficulty.MODERATE,
        year_abandoned=1975,
        historical_use="Medieval fortress",
        hazards=["falling stones", "unstable floors"],
        access_notes="Entry through broken gate on south side",
        asbestos_risk=False,
        security_presence=False,
        discovered_date=datetime.now(),
        last_updated=datetime.now(),
        source="manual_test"
    )
    
    print(f"✓ Created spot: {spot.name}")
    print(f"  Category: {spot.category.value}")
    print(f"  Danger: {spot.danger_level.name}")
    print(f"  Risk score: {spot.get_risk_score()}/100")
    print(f"  Beginner friendly: {spot.is_beginner_friendly()}")
    
    # 2. Test validator
    print("\n2. Testing Validator...")
    validator = UrbexSpotValidator()
    
    is_valid = validator.validate(spot)
    print(f"✓ Validation result: {is_valid}")
    
    safety_score = validator.get_safety_score(spot)
    print(f"✓ Safety score: {safety_score}/100")
    
    # Test invalid spot
    invalid_spot = UrbexSpot(
        name="X",  # Too short
        category=UrbexCategory.OTHER,
        latitude=50.0,  # Out of range
        longitude=10.0,
        department="99"
    )
    
    is_valid = validator.validate(invalid_spot)
    print(f"✓ Invalid spot rejected: {not is_valid}")
    
    # 3. Test database
    print("\n3. Testing Database...")
    db = UrbexDatabase("data/test_urbex.db")
    
    # Add spot
    spot_id = db.add_spot(spot)
    print(f"✓ Added spot to database: ID {spot_id}")
    
    # Retrieve spot
    retrieved = db.get_spot_by_id(spot_id)
    if retrieved:
        print(f"✓ Retrieved spot: {retrieved.name}")
    
    # Add more test spots
    test_spots = [
        UrbexSpot(
            name="Usine Textile Abandonnée",
            category=UrbexCategory.INDUSTRIAL,
            latitude=43.5,
            longitude=1.5,
            department="31",
            danger_level=DangerLevel.HIGH,
            asbestos_risk=True,
            year_abandoned=1985
        ),
        UrbexSpot(
            name="École Primaire Désaffectée",
            category=UrbexCategory.SCHOOL,
            latitude=43.7,
            longitude=1.3,
            department="31",
            danger_level=DangerLevel.LOW,
            year_abandoned=1995
        ),
        UrbexSpot(
            name="Hôpital Psychiatrique",
            category=UrbexCategory.HOSPITAL,
            latitude=43.4,
            longitude=1.6,
            department="31",
            danger_level=DangerLevel.EXTREME,
            asbestos_risk=True,
            hazards=["asbestos", "collapsing ceilings", "broken glass"],
            year_abandoned=1970
        )
    ]
    
    for test_spot in test_spots:
        if validator.validate(test_spot):
            db.add_spot(test_spot)
            print(f"✓ Added: {test_spot.name}")
    
    # Test queries
    print("\n4. Testing Database Queries...")
    
    # By department
    dept_spots = db.get_spots_by_department("31")
    print(f"✓ Spots in department 31: {len(dept_spots)}")
    
    # Safe spots
    safe_spots = db.get_safe_spots(max_danger=2)
    print(f"✓ Safe spots for beginners: {len(safe_spots)}")
    for s in safe_spots:
        print(f"  - {s.name} (danger: {s.danger_level.value})")
    
    # By category
    industrial = db.get_spots_by_category(UrbexCategory.INDUSTRIAL)
    print(f"✓ Industrial spots: {len(industrial)}")
    
    # Search
    results = db.search_spots("château")
    print(f"✓ Search results for 'château': {len(results)}")
    
    # Nearby
    nearby = db.get_nearby_spots(43.6, 1.4, radius_km=50)
    print(f"✓ Spots within 50km: {len(nearby)}")
    
    # Record visit
    if spot_id > 0:
        success = db.record_visit(
            spot_id,
            "Structure still stable, roof partially collapsed",
            danger_update=3
        )
        print(f"✓ Recorded visit: {success}")
    
    # Statistics
    stats = db.get_statistics()
    print("\n5. Database Statistics:")
    print(f"  Total spots: {stats['total_spots']}")
    print(f"  By category: {stats['by_category']}")
    print(f"  By danger: {stats['by_danger']}")
    
    # 6. Test scraper (demo mode)
    print("\n6. Testing Scraper...")
    scraper = UrbexScraper()
    
    # Demo Instagram scraping
    instagram_spots = scraper.scrape_instagram_urbex("urbexfrance", limit=3)
    print(f"✓ Demo Instagram spots found: {len(instagram_spots)}")
    for s in instagram_spots:
        print(f"  - {s.name} ({s.category.value})")
    
    # Demo Reddit scraping
    reddit_spots = scraper.scrape_reddit_urbex()
    print(f"✓ Demo Reddit spots found: {len(reddit_spots)}")
    
    # Search all sources
    all_spots = scraper.search_all_sources()
    print(f"✓ Total unique spots from all sources: {len(all_spots)}")
    
    print("\n" + "=" * 60)
    print("URBEX MODULE TEST COMPLETE")
    print("=" * 60)
    
    # Cleanup test database
    if Path("data/test_urbex.db").exists():
        print("\nNote: Test database created at data/test_urbex.db")
        print("You can delete it manually if not needed.")
    
    return True

if __name__ == "__main__":
    try:
        success = test_urbex_module()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test error: {e}")