#!/usr/bin/env python3
"""Test the code analyzer API"""

import requests
import json

# Test code to analyze
test_code = '''def analyze_spot_environment(self, lat, lon, radius=1000):
    """Analyze environment around a spot"""
    # TODO: Add error handling
    data = self.query_api(lat, lon)
    
    score = 0
    if data['forest_coverage'] > 50:
        score = score + 20
    
    # Check water access
    water = data.get('water_features')
    if water != None:
        score = score + 10
        
    print("Score calculated: " + str(score))
    
    return score'''

# Test the API
url = "http://localhost:8000/api/code/suggest-improvements"
payload = {
    "code": test_code,
    "language": "python"
}

response = requests.post(url, json=payload)
print(f"Response status: {response.status_code}")
print(f"Response: {response.text[:200]}...")

try:
    result = response.json()
except:
    print("Failed to parse JSON response")
    result = {}

print("\n🔍 Code Analysis Results:")
print("=" * 50)

if "ai_suggestions" in result:
    print("\n📋 AI Suggestions:")
    for i, suggestion in enumerate(result["ai_suggestions"], 1):
        print(f"   {i}. {suggestion}")

if "refactoring_opportunities" in result:
    print("\n🔧 Refactoring Opportunities:")
    for refactor in result["refactoring_opportunities"]:
        print(f"   - {refactor['type']}: {refactor['reason']}")
        print(f"     Suggestion: {refactor['suggestion']}")

if "security_analysis" in result:
    security = result["security_analysis"]
    print(f"\n🔐 Security Analysis:")
    print(f"   Risk Level: {security['risk_level'].upper()}")
    if security["vulnerabilities"]:
        print("   Vulnerabilities found:")
        for vuln in security["vulnerabilities"]:
            print(f"     - Line {vuln['line']}: {vuln['description']}")

print("\n✅ Code analyzer is working!")