#!/usr/bin/env python3
"""
Organize JSON files in SPOTS project
Based on sequential analysis of 26 project JSON files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

def organize_json_files():
    """Organize JSON files into proper structure"""
    root = Path('/home/miko/projects/spots')
    
    # Create new directory structure
    directories = [
        'data/main',
        'data/regions',
        'data/exports/archive/2025-08-03'
    ]
    
    for dir_path in directories:
        (root / dir_path).mkdir(parents=True, exist_ok=True)
    
    # File organization mapping
    moves = {
        # Main data files
        'consolidated_spots.json': 'data/main/spots_database.json',
        'spots_map_data.json': 'data/main/spots_map_data.json',
        
        # Regional data
        'haute_garonne_verified_spots.json': 'data/regions/haute_garonne.json',
        
        # Test/demo files to archive
        'instagram_occitanie_spots.json': 'data/exports/archive/2025-08-03/',
        'instagram_scraping_results.json': 'data/exports/archive/2025-08-03/',
        'puppeteer_mcp_demo_results.json': 'data/exports/archive/2025-08-03/',
    }
    
    # Move files
    moved = []
    errors = []
    
    for src_file, dest in moves.items():
        src_path = root / src_file
        if src_path.exists():
            if dest.endswith('/'):
                # Move to directory keeping filename
                dest_path = root / dest / src_file
            else:
                # Rename file
                dest_path = root / dest
            
            try:
                shutil.move(str(src_path), str(dest_path))
                moved.append(f"{src_file} → {dest}")
                print(f"✓ Moved {src_file} → {dest}")
            except Exception as e:
                errors.append(f"Error moving {src_file}: {e}")
                print(f"✗ Error moving {src_file}: {e}")
    
    # Archive old exports (keep structure but move to archive)
    exports_dir = root / 'exports'
    archive_dir = root / 'data/exports/archive/2025-08-03'
    
    # Move timestamped files
    timestamped_patterns = [
        'instagram_spots_*_20250803_*.json',
        'facebook_spots_*_20250803_*.json',
        'validation_report_*_20250803_*.json',
        'realtime_validated_*_20250803_*.json',
        'puppeteer_validated_*_20250803_*.json'
    ]
    
    for pattern in timestamped_patterns:
        for file_path in exports_dir.glob(pattern):
            try:
                dest_path = archive_dir / file_path.name
                shutil.move(str(file_path), str(dest_path))
                moved.append(f"{file_path.name} → archive")
                print(f"✓ Archived {file_path.name}")
            except Exception as e:
                errors.append(f"Error archiving {file_path.name}: {e}")
    
    # Create JSON organization report
    report = {
        "organization_date": datetime.now().isoformat(),
        "files_moved": len(moved),
        "errors": len(errors),
        "new_structure": {
            "data/main": "Primary data files (spots database and map data)",
            "data/regions": "Region-specific data files",
            "data/exports/archive": "Historical exports organized by date",
            "exports": "Current/active exports only"
        },
        "recommendations": [
            "Add exports/*.json to .gitignore to avoid repo bloat",
            "Use data/main/spots_database.json as single source of truth",
            "Clean up archive periodically (keep only significant versions)",
            "Consider using database instead of JSON for production"
        ]
    }
    
    # Save report
    report_path = root / 'JSON_ORGANIZATION_REPORT.md'
    with open(report_path, 'w') as f:
        f.write("# JSON Files Organization Report\n\n")
        f.write(f"**Date**: {report['organization_date']}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Files moved: {report['files_moved']}\n")
        f.write(f"- Errors: {report['errors']}\n\n")
        f.write("## New Structure\n\n")
        for path, desc in report['new_structure'].items():
            f.write(f"- **{path}**: {desc}\n")
        f.write("\n## Recommendations\n\n")
        for rec in report['recommendations']:
            f.write(f"- {rec}\n")
        
        if errors:
            f.write("\n## Errors\n\n")
            for error in errors:
                f.write(f"- {error}\n")
    
    print(f"\n✅ Organization complete! Report saved to {report_path}")
    return moved, errors

if __name__ == "__main__":
    print("🗂️ Organizing JSON files...\n")
    moved, errors = organize_json_files()
    
    print(f"\n📊 Summary:")
    print(f"  - Files organized: {len(moved)}")
    print(f"  - Errors: {len(errors)}")