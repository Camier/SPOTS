#!/usr/bin/env python3
"""
Test script for IGN WFS integration with SPOTS platform
Validates WFS service connectivity and functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))

from backend.services.ign_wfs_service import IGNWFSService
import sqlite3
import json

class WFSIntegrationTester:
    def __init__(self):
        self.wfs_service = IGNWFSService()
        self.db_path = project_root / "data" / "occitanie_spots.db"
        
    async def test_wfs_capabilities(self):
        """Test WFS service capabilities"""
        print("🔍 Testing WFS Capabilities...")
        
        try:
            capabilities = self.wfs_service.get_capabilities()
            
            if capabilities['status'] == 'success':
                print("✅ WFS Capabilities retrieved successfully")
                print(f"   - Service: {capabilities['service_info']['title']}")
                print(f"   - Version: {capabilities['service_info']['version']}")
                print(f"   - Available layers: {len(capabilities['available_layers'])}")
                return True
            else:
                print("❌ WFS Capabilities failed")
                print(f"   Error: {capabilities.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ WFS Capabilities test failed: {e}")
            return False
    
    async def test_transport_query(self):
        """Test transport network queries"""
        print("\n🛤️ Testing Transport Network Queries...")
        
        # Test coordinates around Toulouse (Occitanie)
        test_coords = (43.6047, 1.4442)
        
        try:
            result = self.wfs_service.query_transport_network(
                test_coords, 1000, 'hiking'
            )
            
            if result['status'] == 'success':
                feature_count = result.get('feature_count', 0)
                print(f"✅ Transport query successful")
                print(f"   - Location: {test_coords}")
                print(f"   - Features found: {feature_count}")
                print(f"   - Query type: {result['query_type']}")
                return True
            else:
                print("❌ Transport query failed")
                print(f"   Error: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Transport query test failed: {e}")
            return False
    
    async def test_hydrography_query(self):
        """Test hydrography queries"""
        print("\n💧 Testing Hydrography Queries...")
        
        # Test coordinates around a known water feature in Occitanie
        test_coords = (43.6047, 1.4442)
        
        try:
            result = self.wfs_service.query_hydrography(
                test_coords, 2000, 'all'
            )
            
            if result['status'] == 'success':
                feature_count = result.get('feature_count', 0)
                print(f"✅ Hydrography query successful")
                print(f"   - Location: {test_coords}")
                print(f"   - Water features found: {feature_count}")
                print(f"   - Query type: {result['query_type']}")
                return True
            else:
                print("❌ Hydrography query failed")
                print(f"   Error: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Hydrography query test failed: {e}")
            return False
    
    async def test_administrative_query(self):
        """Test administrative boundaries queries"""
        print("\n🏛️ Testing Administrative Boundaries...")
        
        # Bounding box around Toulouse area
        test_bbox = (1.4, 43.6, 1.5, 43.7)
        
        try:
            result = self.wfs_service.query_administrative_boundaries(
                test_bbox, 'commune'
            )
            
            if result['status'] == 'success':
                feature_count = result.get('feature_count', 0)
                print(f"✅ Administrative query successful")
                print(f"   - Bounding box: {test_bbox}")
                print(f"   - Communes found: {feature_count}")
                print(f"   - Query type: {result['query_type']}")
                return True
            else:
                print("❌ Administrative query failed")
                print(f"   Error: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Administrative query test failed: {e}")
            return False
    
    async def test_spot_analysis(self):
        """Test comprehensive spot analysis with real SPOTS data"""
        print("\n🎯 Testing Spot Analysis with Real Data...")
        
        if not self.db_path.exists():
            print("❌ SPOTS database not found - skipping spot analysis test")
            return False
        
        try:
            # Get a random spot from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, latitude, longitude, type 
                FROM spots 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL 
                LIMIT 1
            """)
            
            spot = cursor.fetchone()
            conn.close()
            
            if not spot:
                print("❌ No valid spots found in database")
                return False
            
            spot_id, name, lat, lon, spot_type = spot
            print(f"   - Testing with spot: {name} ({spot_type})")
            print(f"   - Coordinates: {lat}, {lon}")
            
            # Perform comprehensive analysis
            analysis = self.wfs_service.analyze_spot_surroundings(
                spot_id, (lat, lon), 1500
            )
            
            print(f"✅ Spot analysis completed")
            print(f"   - Spot ID: {analysis['spot_id']}")
            print(f"   - Analysis radius: {analysis['analysis_radius']}m")
            print(f"   - Timestamp: {analysis['timestamp']}")
            
            # Display accessibility score if available
            if 'accessibility_score' in analysis:
                score = analysis['accessibility_score']
                print(f"   - Overall accessibility: {score['overall']}/100")
                print(f"   - Transport score: {score['transport']}/100")
                print(f"   - Water access score: {score['water_access']}/100")
                print(f"   - Factors: {', '.join(score['factors'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Spot analysis test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all WFS integration tests"""
        print("🚀 Starting IGN WFS Integration Tests for SPOTS")
        print("=" * 60)
        
        test_results = []
        
        # Run individual tests
        test_results.append(await self.test_wfs_capabilities())
        test_results.append(await self.test_transport_query())
        test_results.append(await self.test_hydrography_query())
        test_results.append(await self.test_administrative_query())
        test_results.append(await self.test_spot_analysis())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed! WFS integration is ready.")
        else:
            print("⚠️  Some tests failed. Check connectivity and configuration.")
            
        return passed == total

def main():
    """Main test execution"""
    tester = WFSIntegrationTester()
    
    # Run async tests
    result = asyncio.run(tester.run_all_tests())
    
    if result:
        print("\n✅ IGN WFS integration validated successfully!")
        print("Next steps:")
        print("1. Start your backend: uvicorn src.backend.main:app --reload")
        print("2. Test API endpoints: curl http://localhost:8000/api/ign/wfs/capabilities")
        print("3. Update frontend with WFS client integration")
    else:
        print("\n❌ Integration tests failed. Please check:")
        print("1. Internet connectivity")
        print("2. IGN WFS service availability")
        print("3. Project dependencies installed")

if __name__ == "__main__":
    main()
