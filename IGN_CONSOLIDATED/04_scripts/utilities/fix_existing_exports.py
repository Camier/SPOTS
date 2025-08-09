#!/usr/bin/env python3
"""
Fix existing export files to include required 'source' field
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import shutil

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.backend.validators.social_media_schemas import DataValidator


def fix_export_files():
    """Add missing 'source' field to existing export files"""
    exports_dir = Path("exports")
    
    if not exports_dir.exists():
        print("❌ No exports directory found")
        return
    
    # Find all JSON files that need fixing
    json_files = list(exports_dir.glob("*.json"))
    
    # Skip validation reports
    files_to_fix = []
    for file_path in json_files:
        if 'validation_report' in file_path.name:
            continue
            
        # Check if file needs source field
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'export_date' in data and 'source' not in data:
                files_to_fix.append(file_path)
        except:
            pass
    
    print(f"📁 Found {len(files_to_fix)} files to fix")
    print("=" * 60)
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        print(f"\n🔧 Fixing: {file_path.name}")
        
        try:
            # Create backup
            backup_path = file_path.with_suffix('.json.backup')
            shutil.copy2(file_path, backup_path)
            print(f"  📦 Created backup: {backup_path.name}")
            
            # Load data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine source from filename
            if 'instagram' in file_path.name.lower():
                source = 'Instagram'
            elif 'facebook' in file_path.name.lower():
                source = 'Facebook'
            else:
                source = 'Combined'
            
            # Add source field
            data['source'] = source
            print(f"  ✅ Added source: {source}")
            
            # Save fixed file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Validate the fixed file
            validator = DataValidator()
            result = validator.validate_export_file(str(file_path))
            
            if result['valid']:
                print(f"  ✅ File now passes validation!")
                fixed_count += 1
            else:
                print(f"  ⚠️  Still has issues: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"  ❌ Error fixing file: {e}")
    
    print(f"\n\n📊 Fix Summary:")
    print(f"  ✅ Fixed: {fixed_count}/{len(files_to_fix)} files")
    print(f"  📦 Backups created for all modified files")
    
    # Run validation again
    print(f"\n\n🔍 Running validation on all files...")
    import subprocess
    subprocess.run([sys.executable, "scripts/validate_existing_data.py"])


def cleanup_backups():
    """Remove backup files after confirmation"""
    exports_dir = Path("exports")
    backup_files = list(exports_dir.glob("*.backup"))
    
    if backup_files:
        print(f"\n\n🗑️  Found {len(backup_files)} backup files")
        response = input("Remove backup files? (y/n): ")
        
        if response.lower() == 'y':
            for backup in backup_files:
                backup.unlink()
            print(f"✅ Removed {len(backup_files)} backup files")


if __name__ == "__main__":
    fix_export_files()
    # Uncomment to cleanup backups
    # cleanup_backups()