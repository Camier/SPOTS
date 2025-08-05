#!/usr/bin/env python3
"""
Script to apply real data validation decorator to all scraper methods
This ensures NO MOCK OR FAKE DATA enters the system
"""

import ast
import os
from pathlib import Path
import re
from typing import List, Tuple
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Scraper files to update
SCRAPER_FILES = [
    'unified_instagram_scraper.py',
    'facebook_real_scraper.py',
    'facebook_playwright_scraper.py',
    'facebook_puppeteer_scraper.py',
    'reddit_scraper.py',
    'reddit_scraper_french.py',
    'reddit_scraper_enhanced.py',
    'unified_reddit_scraper.py',
    'realtime_validated_scraper.py',
    'validated_instagram_scraper.py',
]

# Methods that should have @enforce_real_data decorator
METHODS_TO_DECORATE = [
    'scrape',
    'scrape_location',
    'scrape_posts',
    'scrape_hashtag',
    'scrape_subreddit',
    'fetch_spots',
    'get_spots',
    'extract_spots',
]


def add_import_if_missing(content: str) -> str:
    """Add the real_data_validator import if it's missing"""
    if 'from src.backend.validators.real_data_validator import enforce_real_data' in content:
        return content
    
    # Find the last import statement
    import_lines = []
    lines = content.split('\n')
    last_import_idx = 0
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i
    
    # Insert the import after the last import
    lines.insert(last_import_idx + 1, 'from src.backend.validators.real_data_validator import enforce_real_data')
    return '\n'.join(lines)


def add_decorator_to_method(content: str, method_name: str) -> str:
    """Add @enforce_real_data decorator to a method if it doesn't have it"""
    # Pattern to find method definitions
    method_pattern = rf'(\s*)(async\s+)?def\s+{method_name}\s*\('
    
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        match = re.match(method_pattern, line)
        if match:
            indent = match.group(1)
            # Check if previous line is already the decorator
            if i > 0 and '@enforce_real_data' in lines[i-1]:
                continue
            
            # Add decorator with proper indentation
            lines.insert(i, f'{indent}@enforce_real_data')
            modified = True
    
    return '\n'.join(lines) if modified else content


def update_scraper_file(file_path: Path) -> bool:
    """Update a single scraper file with real data validation"""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Add import if missing
        content = add_import_if_missing(content)
        
        # Add decorators to methods
        for method in METHODS_TO_DECORATE:
            content = add_decorator_to_method(content, method)
        
        # Only write if content changed
        if content != original_content:
            file_path.write_text(content)
            logger.info(f"✅ Updated: {file_path.name}")
            return True
        else:
            logger.debug(f"⏭️  Already compliant: {file_path.name}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating {file_path.name}: {e}", exc_info=True)
        return False


def main():
    """Apply real data validation to all scrapers"""
    logger.info("🚨 Applying Real Data Validation to All Scrapers")
    logger.info("=" * 50)
    
    scrapers_dir = Path(__file__).parent
    updated_count = 0
    
    for scraper_file in SCRAPER_FILES:
        file_path = scrapers_dir / scraper_file
        if file_path.exists():
            if update_scraper_file(file_path):
                updated_count += 1
        else:
            logger.warning(f"⚠️  File not found: {scraper_file}")
    
    logger.info("=" * 50)
    logger.info(f"✅ Updated {updated_count} scraper files")
    logger.info("🔒 All scrapers now enforce real data validation!")
    
    # Also update the test file to use the new approach
    test_file = scrapers_dir.parent.parent.parent / 'tests' / 'backend' / 'test_main_api.py'
    if test_file.exists():
        content = test_file.read_text()
        if 'MOCK' in content or 'mock' in content:
            logger.warning("\n⚠️  WARNING: Test file still contains mock data!")
            logger.warning("Please update tests to use real API calls or clearly marked test data")


if __name__ == "__main__":
    main()