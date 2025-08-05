#!/usr/bin/env python3
"""
Practical Code Improvement: Enhance SPOTS Functions
"""

import requests
import json
from textwrap import dedent

def improve_spots_function():
    """Demonstrate improving actual SPOTS code"""
    
    print("🔧 SPOTS Code Improvement - Real Example")
    print("=" * 60)
    
    # Original function from SPOTS that could be improved
    original_code = '''
def calculate_quality_score(spot):
    """Calculate a quality score for a spot"""
    score = spot['confidence_score'] * 100  # Start with confidence
    
    # Bonus for having description
    if spot.get('description'):
        score += min(20, len(spot['description']) / 10)
    
    # Bonus for verified type
    if spot.get('type') and spot['type'] != 'unknown':
        score += 10
    
    # Bonus for having elevation
    if spot.get('elevation'):
        score += 5
        
    # Bonus for having address
    if spot.get('address'):
        score += 5
        
    return min(100, score)  # Cap at 100
'''

    print("📝 Original SPOTS Function:")
    print(original_code)
    
    # Analyze it
    response = requests.post(
        "http://localhost:8000/api/code/suggest-improvements",
        json={
            "code": original_code,
            "language": "python"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n🤖 AI Analysis Results:")
        
        if result.get("ai_suggestions"):
            print("\n💡 Suggestions:")
            for suggestion in result["ai_suggestions"]:
                print(f"   • {suggestion}")
        
        print("\n✨ Improved Version Based on AI Suggestions:")
        
        improved_code = '''
from typing import Dict, Any, Union

# Configuration for quality scoring
QUALITY_WEIGHTS = {
    'description_base': 20,
    'description_per_char': 10,
    'verified_type': 10,
    'has_elevation': 5,
    'has_address': 5,
    'has_weather_info': 3,
    'has_accessibility': 7
}

def calculate_quality_score(spot: Dict[str, Any]) -> float:
    """
    Calculate a quality score for a spot based on multiple factors.
    
    Args:
        spot: Dictionary containing spot data with fields like:
            - confidence_score: Base confidence (0-1)
            - description: Text description
            - type: Spot type (e.g., 'waterfall', 'viewpoint')
            - elevation: Elevation in meters
            - address: Physical address
            - weather_sensitive: Boolean for weather dependency
            - accessibility: Accessibility information
    
    Returns:
        float: Quality score between 0 and 100
        
    Example:
        >>> spot = {'confidence_score': 0.8, 'description': 'Beautiful waterfall'}
        >>> score = calculate_quality_score(spot)
        >>> assert 0 <= score <= 100
    """
    # Validate input
    if not isinstance(spot, dict):
        raise ValueError("Spot must be a dictionary")
    
    # Start with confidence score (0-100 scale)
    base_score = spot.get('confidence_score', 0) * 100
    
    # Calculate bonuses
    bonus_score = 0
    
    # Description bonus with better calculation
    description = spot.get('description', '')
    if description:
        desc_length = len(description)
        # More sophisticated scoring based on description quality
        if desc_length > 0:
            bonus_score += min(
                QUALITY_WEIGHTS['description_base'],
                desc_length / QUALITY_WEIGHTS['description_per_char']
            )
    
    # Type verification bonus
    spot_type = spot.get('type', '').lower()
    if spot_type and spot_type != 'unknown':
        bonus_score += QUALITY_WEIGHTS['verified_type']
    
    # Location data bonuses
    if spot.get('elevation') is not None:
        bonus_score += QUALITY_WEIGHTS['has_elevation']
    
    if spot.get('address'):
        bonus_score += QUALITY_WEIGHTS['has_address']
    
    # Additional quality indicators
    if spot.get('weather_sensitive') is not None:
        bonus_score += QUALITY_WEIGHTS['has_weather_info']
    
    if spot.get('accessibility'):
        bonus_score += QUALITY_WEIGHTS['has_accessibility']
    
    # Calculate final score
    total_score = base_score + bonus_score
    
    # Apply cap and ensure valid range
    return max(0, min(100, total_score))


def get_quality_category(score: float) -> str:
    """
    Get quality category based on score.
    
    Args:
        score: Quality score (0-100)
        
    Returns:
        str: Quality category
    """
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 50:
        return "Fair"
    else:
        return "Needs Improvement"


# Example usage with error handling
if __name__ == "__main__":
    test_spots = [
        {
            'confidence_score': 0.9,
            'description': 'Hidden waterfall with crystal clear pools',
            'type': 'waterfall',
            'elevation': 450,
            'address': 'Near Toulouse, France'
        },
        {
            'confidence_score': 0.6,
            'type': 'unknown'
        }
    ]
    
    for i, spot in enumerate(test_spots, 1):
        try:
            score = calculate_quality_score(spot)
            category = get_quality_category(score)
            print(f"Spot {i}: Score = {score:.1f}, Category = {category}")
        except Exception as e:
            print(f"Error processing spot {i}: {e}")
'''
        
        print(improved_code)
        
        print("\n📊 Improvements Applied:")
        print("   ✅ Added comprehensive type hints")
        print("   ✅ Created configuration constants for maintainability")
        print("   ✅ Added detailed docstring with examples")
        print("   ✅ Implemented input validation")
        print("   ✅ Enhanced scoring algorithm with more factors")
        print("   ✅ Added helper function for categorization")
        print("   ✅ Included error handling")
        print("   ✅ Made the function more testable")
        print("   ✅ Improved code organization and readability")
        
        # Test the improvements
        print("\n🧪 Testing Improvement Benefits:")
        
        # Security comparison
        orig_response = requests.post(
            "http://localhost:8000/api/code/suggest-improvements",
            json={"code": original_code, "language": "python"}
        )
        
        improved_response = requests.post(
            "http://localhost:8000/api/code/suggest-improvements",
            json={"code": improved_code[:2000], "language": "python"}
        )
        
        if orig_response.status_code == 200 and improved_response.status_code == 200:
            orig_security = orig_response.json().get("security_analysis", {})
            improved_security = improved_response.json().get("security_analysis", {})
            
            print(f"\n   Original Security Risk: {orig_security.get('risk_level', 'unknown').upper()}")
            print(f"   Improved Security Risk: {improved_security.get('risk_level', 'unknown').upper()}")
            
            print("\n   Benefits of AI-Enhanced Code:")
            print("   • Better error handling reduces runtime failures")
            print("   • Type hints enable better IDE support")
            print("   • Documentation helps team collaboration")
            print("   • Configurable weights make it easier to adjust")
            print("   • Testable design improves reliability")

if __name__ == "__main__":
    improve_spots_function()