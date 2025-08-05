#!/usr/bin/env python3
"""
Validate all scrapers to ensure they only fetch REAL DATA
NO MOCK DATA ALLOWED!
"""

import os
import sys
import ast
import re
from pathlib import Path


def check_file_for_mock_data(file_path):
    """Check if a file contains mock data generation"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Patterns that indicate mock data generation
    mock_patterns = [
        r'generate.*fake',
        r'generate.*mock',
        r'generate.*simulated',
        r'create.*fake.*data',
        r'random\.choice.*\[.*spots.*\]',
        r'fake.*=.*True',
        r'mock.*=.*True',
        r'return.*\{.*"fake".*:.*True',
        r'_generate_.*spot',
        r'_create_fake',
        r'dummy.*data',
    ]
    
    for pattern in mock_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_no = content[:match.start()].count('\n') + 1
            issues.append({
                'file': file_path,
                'line': line_no,
                'pattern': pattern,
                'match': match.group()
            })
    
    # Check for functions that might generate data
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if any(word in node.name.lower() for word in ['generate', 'simulate', 'mock', 'fake', 'dummy']):
                    if 'test' not in str(file_path).lower():
                        issues.append({
                            'file': file_path,
                            'line': node.lineno,
                            'pattern': 'suspicious function name',
                            'match': f'def {node.name}'
                        })
    except:
        pass
    
    return issues


def validate_scrapers():
    """Validate all scraper files"""
    print("=" * 70)
    print("🔍 VALIDATING SCRAPERS - NO MOCK DATA ALLOWED!")
    print("=" * 70)
    print()
    
    scrapers_dir = Path("src/backend/scrapers")
    
    # Find all scraper files
    scraper_files = list(scrapers_dir.glob("*scraper*.py"))
    
    print(f"Found {len(scraper_files)} scraper files to validate:")
    for f in scraper_files:
        print(f"  - {f.name}")
    print()
    
    all_issues = []
    
    for scraper_file in scraper_files:
        issues = check_file_for_mock_data(scraper_file)
        if issues:
            all_issues.extend(issues)
    
    if all_issues:
        print("❌ VALIDATION FAILED! Found potential mock data generation:")
        print()
        for issue in all_issues:
            print(f"📁 {issue['file'].name}")
            print(f"   Line {issue['line']}: {issue['match']}")
            print(f"   Pattern: {issue['pattern']}")
            print()
    else:
        print("✅ VALIDATION PASSED!")
        print("All scrapers appear to fetch REAL DATA only.")
        print()
        
        # Additional checks
        print("📊 Scraper Summary:")
        for scraper_file in scraper_files:
            with open(scraper_file, 'r') as f:
                content = f.read()
            
            # Check for real data indicators
            real_data_indicators = [
                'requests.get',
                'requests.post',
                'api.reddit.com',
                'instagram.com',
                'overpass-api',
                'nominatim',
                'is_real_data": True',
                'fetch.*real',
                'actual.*data'
            ]
            
            indicators_found = []
            for indicator in real_data_indicators:
                if re.search(indicator, content, re.IGNORECASE):
                    indicators_found.append(indicator)
            
            print(f"\n✓ {scraper_file.name}")
            if indicators_found:
                print(f"  Real data sources: {', '.join(indicators_found[:3])}")
            else:
                print(f"  ⚠️  No obvious real data sources found")
    
    return len(all_issues) == 0


if __name__ == "__main__":
    success = validate_scrapers()
    sys.exit(0 if success else 1)