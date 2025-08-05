#!/usr/bin/env python3
"""
Demo: HuggingFace-Powered Code Analysis for SPOTS
Shows how AI models enhance code quality
"""

import requests
import json
from datetime import datetime

def test_code_analyzer():
    """Demonstrate the code analyzer capabilities"""
    print("🤖 SPOTS Code Analyzer - HuggingFace Integration Demo")
    print("=" * 60)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Example 1: Analyze Python code with security issues
    print("\n📝 Example 1: Python Code with Security Issues")
    print("-" * 50)
    
    vulnerable_code = '''
def get_user_data(user_id):
    """Fetch user data from database"""
    # Build SQL query
    query = "SELECT * FROM users WHERE id = " + user_id
    password = "admin123"  # TODO: Move to env
    
    connection = db.connect(host="localhost", password=password)
    result = connection.execute(query)
    
    return result.fetchall()
'''
    
    response = requests.post(
        "http://localhost:8000/api/code/suggest-improvements",
        json={
            "code": vulnerable_code,
            "language": "python"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Analysis complete!")
        
        if result.get("security_analysis", {}).get("vulnerabilities"):
            print("\n🔐 Security Vulnerabilities Found:")
            for vuln in result["security_analysis"]["vulnerabilities"]:
                print(f"   ⚠️  Line {vuln['line']}: {vuln['description']}")
                print(f"      Type: {vuln['type']}, Severity: {vuln['severity']}")
        
        if result.get("ai_suggestions"):
            print("\n💡 AI Suggestions:")
            for i, suggestion in enumerate(result["ai_suggestions"], 1):
                print(f"   {i}. {suggestion}")
    
    # Example 2: JavaScript code analysis
    print("\n\n📝 Example 2: JavaScript Code Analysis")
    print("-" * 50)
    
    js_code = '''
var calculateSpotScore = function(spotData) {
    console.log("Calculating score for spot");
    
    var score = 0;
    
    // Check features
    if (spotData.hasWater == true) {
        score = score + 10;
    }
    
    if (spotData.difficulty == "easy") {
        score = score + 5;
    }
    
    eval("score = score + " + spotData.bonus);  // Dynamic bonus
    
    return score;
}
'''
    
    response = requests.post(
        "http://localhost:8000/api/code/suggest-improvements",
        json={
            "code": js_code,
            "language": "javascript"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Analysis complete!")
        
        if result.get("ai_suggestions"):
            print("\n💡 AI Suggestions:")
            for suggestion in result["ai_suggestions"]:
                print(f"   • {suggestion}")
        
        if result.get("security_analysis", {}).get("risk_level"):
            print(f"\n🔐 Security Risk Level: {result['security_analysis']['risk_level'].upper()}")
    
    # Example 3: Get project health report
    print("\n\n📊 Example 3: Project Health Report")
    print("-" * 50)
    
    response = requests.get("http://localhost:8000/api/code/code-health-report")
    
    if response.status_code == 200:
        health = response.json()
        print(f"✅ Health Report Generated!")
        print(f"   Overall Health: {health['overall_health'].upper()}")
        print(f"   Files Analyzed: {health['files_analyzed']}")
        print(f"   Total Issues: {health['total_issues']}")
        print(f"   Security Vulnerabilities: {health['security_vulnerabilities']}")
        
        print("\n📁 Module Analysis:")
        for module in health['modules']:
            print(f"   • {module['file']}")
            print(f"     Language: {module['language']}, Lines: {module['lines']}")
            print(f"     Issues: {module['issues_count']}, Security: {module['security_risk']}")
            print(f"     Documentation: {module['documentation_coverage']*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("🎉 Demo Complete! The HuggingFace integration is ready to improve your code!")
    print("\nTest the interactive UI at: http://localhost:8085/code-analyzer.html")

if __name__ == "__main__":
    test_code_analyzer()