#!/usr/bin/env python3
"""
Organize SPOTS project files into proper directory structure
"""

import os
import shutil
from pathlib import Path

# Define the organization mapping
FILE_ORGANIZATION = {
    # Main documentation - stays in root
    'README.md': None,
    'SPOTS_QUICKREF.md': None,
    
    # Guides
    'docs/guides': [
        'API_ACCESS_GUIDE.md',
        'ARTISTIC_STYLES_INTEGRATION.md',
        'CLAUDE_CODE_QUICKSTART.md',
        'CODE_IMPROVEMENT_GUIDE.md',
        'CONTEXT_FILES_GUIDE.md',
        'DATA_PROCESSING_PIPELINE.md',
        'DATA_SCRAPING_INFRASTRUCTURE.md',
        'DOCUMENTATION_INDEX.md',
        'DOCUMENTATION.md',
        'ENRICHMENT_COMPLETE_GUIDE.md',
        'FRENCH_GEOCODING_INTEGRATION.md',
        'GEOAI_INTEGRATION_GUIDE.md',
        'IGN_WFS_INTEGRATION_GUIDE.md',
        'INSTAGRAM_BEST_PRACTICES_GUIDE.md',
        'LOCAL_CODE_MODEL_SETUP.md',
        'STARCODER_COMMANDS_GUIDE.md',
    ],
    
    # Reports
    'docs/reports': [
        'CLEANUP_REPORT.md',
        'COMPREHENSIVE_CODE_REVIEW.md',
        'DATA_VALIDATION_FINDINGS.md',
        'FILTERING_REPORT.md',
        'FRONTEND_REVIEW.md',
        'LOCAL_AI_ANALYSIS_RESULTS.md',
        'TECHNICAL_DEBT_REPORT.md',
        'VALIDATION_REPORT.md',
        'WFS_INTEGRATION_REPORT.md',
        'WORKSPACE_CLEANUP_REPORT.md',
        'knowledge_sync_report.md',
    ],
    
    # Summaries
    'docs/summaries': [
        'COMPLETE_INSIGHTS_SUMMARY.md',
        'CONSOLIDATION_COMPLETE.md',
        'CONSOLIDATION_SUMMARY.md',
        'DATA_STORAGE_VALIDATION_SUMMARY.md',
        'FACEBOOK_DATA_MINING_SUMMARY.md',
        'IGN-INTEGRATION-SUMMARY.md',
        'IGN_INTEGRATION_SUMMARY.md',
        'MAP-TILE-FIX-SUMMARY.md',
        'OLA_MAPS_INTEGRATION_SUMMARY.md',
        'OPTIMIZATION-SUMMARY.md',
        'REFACTORING_SUMMARY.md',
        'SCRAPING_SUMMARY.md',
        'SOCIAL_MEDIA_MINING_COMPLETE.md',
    ],
    
    # Technical/Implementation
    'docs/technical': [
        'CARTES_GOUV_FR_INTEGRATION.md',
        'CLAUDE_CODE_WFS_INTEGRATION_PROMPT.md',
        'CLAUDE_COMMANDS_VALIDATION.md',
        'ENHANCED_MAP_IGN_FIXES.md',
        'IGN-ADVANCED-FEATURES.md',
        'IGN_ENHANCEMENT_PLAN.md',
        'IGN_SCAN_REGIONAL_INTEGRATION.md',
        'IMPLEMENTATION_ACTION_PLAN.md',
        'LAUNCH_SUCCESS.md',
        'PRACTICAL_IMPROVEMENTS.md',
        'PREMIUM_MAPS_UPGRADE.md',
        'PROJECT_MERGE_PLAN.md',
        'REGIONAL_TRANSFORMATION.md',
        'SECURITY_FIXES_APPLIED.md',
        'STARCODER2_AND_BEYOND.md',
        'STARCODER_COMMANDS_FIXED.md',
        'TOOLS_MIGRATION_COMPLETE.md',
    ],
    
    # Project context files
    'docs/archive': [
        'COMPREHENSIVE_DOCUMENTATION.md',
        'PROJECT_CONTEXT_BRIEF.md',
        'PROJECT_CONTEXT_COPYPASTE.md',
        'PROJECT_CONTEXT.md',
        'PROJECT-SNAPSHOT.md',
        'QUICK_REFERENCE.md',
    ],
    
    # Python tools - Analysis
    'tools/analysis': [
        'ai_code_review.py',
        'alternative_ai_analysis.py',
        'analyze_with_code_models.py',
        'analyze_with_hf_models.py',
        'analyze_with_paid_hf.py',
        'demo_code_analyzer.py',
        'direct_code_analysis.py',
        'local_code_analyzer.py',
        'test_code_analyzer.py',
        'use_code_improvement.py',
        'use_working_code_models.py',
    ],
    
    # Python tools - Scraping
    'tools/scraping': [
        'test_scraping_pipeline.py',
        'validate_instagram_scraper.py',
        'test_instagram_simple.py',
        'test_instagram_puppeteer_mcp.py',
        'test_instagram_playwright.py',
        'test_instagram_playwright_headless.py',
        'collect_instagram_occitanie.py',
        'validate_scrapers.py',
    ],
    
    # Python tools - Validation/Testing
    'tools/validation': [
        'check_available_models.py',
        'find_actual_working_models.py',
        'query_hf_with_headers.py',
        'test_coding_models.py',
        'test_granite_sql.py',
        'test_hf_diagnostic.py',
        'test_ign_wfs_integration.py',
        'test_ign_wfs_no_api_key.py',
        'test_local_llama.py',
        'test_ollama_direct.py',
        'validate_wfs_integration.py',
        'test_puppeteer_mcp_demo.py',
        'test_ola_maps_simple.py',
    ],
    
    # Python tools - Improvements
    'tools': [
        'improve_spots_code.py',
        'quick_code_fix.py',
        'simple_code_fixes.py',
        'consolidate_spots.py',
        'organize_project.py',  # This script itself
    ],
    
    # Shell scripts
    'tools': [
        'cleanup_workspace.sh',
        'run_claude_code_integration.sh',
        'map-interfaces.sh',
    ],
}

def organize_files():
    """Move files to their appropriate directories"""
    root = Path('/home/miko/projects/spots')
    moved_files = []
    errors = []
    
    for dest_dir, files in FILE_ORGANIZATION.items():
        if files is None:
            continue
            
        dest_path = root / dest_dir if dest_dir else root
        
        for filename in files:
            src = root / filename
            dst = dest_path / filename
            
            if src.exists():
                try:
                    # Create destination directory if needed
                    dest_path.mkdir(parents=True, exist_ok=True)
                    
                    # Move the file
                    shutil.move(str(src), str(dst))
                    moved_files.append(f"{filename} → {dest_dir}")
                    print(f"✓ Moved {filename} → {dest_dir}")
                except Exception as e:
                    errors.append(f"Error moving {filename}: {e}")
                    print(f"✗ Error moving {filename}: {e}")
            else:
                # File might have been already moved or doesn't exist
                if not dst.exists():
                    print(f"⚠ File not found: {filename}")
    
    # Handle remaining Python files
    remaining_py = list(root.glob('*.py'))
    if remaining_py:
        print("\n📌 Remaining Python files to handle:")
        for py_file in remaining_py:
            if py_file.name != 'organize_project.py':
                print(f"  - {py_file.name}")
    
    # Handle remaining MD files
    remaining_md = list(root.glob('*.md'))
    if remaining_md:
        print("\n📌 Remaining MD files:")
        for md_file in remaining_md:
            if md_file.name not in ['README.md', 'SPOTS_QUICKREF.md']:
                print(f"  - {md_file.name}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  - Files moved: {len(moved_files)}")
    print(f"  - Errors: {len(errors)}")
    
    return moved_files, errors

if __name__ == "__main__":
    print("🧹 Organizing SPOTS project files...\n")
    moved, errors = organize_files()
    
    if errors:
        print("\n❌ Errors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n✅ Organization complete!")