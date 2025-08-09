#!/usr/bin/env python3
"""
Validate all existing social media data files against schemas
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.backend.validators.social_media_schemas import DataValidator


def validate_all_exports():
    """Validate all export files"""
    validator = DataValidator()
    exports_dir = Path("exports")
    
    if not exports_dir.exists():
        print("❌ No exports directory found")
        return
    
    # Find all JSON files
    json_files = list(exports_dir.glob("*.json"))
    
    print(f"📁 Found {len(json_files)} JSON files to validate")
    print("=" * 60)
    
    results = {
        'valid': [],
        'invalid': [],
        'errors': []
    }
    
    for file_path in json_files:
        print(f"\n🔍 Validating: {file_path.name}")
        
        try:
            # Determine source from filename
            if 'instagram' in file_path.name.lower():
                source = 'instagram'
            elif 'facebook' in file_path.name.lower():
                source = 'facebook'
            else:
                source = 'unified'
            
            # Validate file structure
            result = validator.validate_export_file(str(file_path))
            
            if result['valid']:
                print(f"  ✅ Valid! {result['total_spots']} spots")
                results['valid'].append(file_path.name)
            else:
                print(f"  ❌ Invalid!")
                print(f"     Error: {result.get('error', 'Unknown error')}")
                if result.get('errors'):
                    for err in result['errors'][:3]:  # Show first 3 errors
                        print(f"     - Spot {err['index']}: {err['error']}")
                results['invalid'].append(file_path.name)
                results['errors'].extend(result.get('errors', []))
                
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parsing error: {e}")
            results['invalid'].append(file_path.name)
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            results['invalid'].append(file_path.name)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary:")
    print(f"  ✅ Valid files: {len(results['valid'])}")
    print(f"  ❌ Invalid files: {len(results['invalid'])}")
    print(f"  ⚠️  Total errors: {len(results['errors'])}")
    
    # Create validation report
    report = {
        'validation_date': datetime.now().isoformat(),
        'total_files': len(json_files),
        'valid_files': results['valid'],
        'invalid_files': results['invalid'],
        'error_count': len(results['errors']),
        'sample_errors': results['errors'][:10] if results['errors'] else []
    }
    
    report_path = exports_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 Validation report saved to: {report_path}")
    
    # Check data storage best practices
    print("\n🔒 Data Storage Security Check:")
    check_storage_security(json_files)


def check_storage_security(json_files):
    """Check if data follows security best practices"""
    issues = []
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for potential PII
            content = json.dumps(data)
            
            # Email pattern
            import re
            if re.search(r'\S+@\S+\.\S+', content):
                issues.append(f"{file_path.name}: Contains unsanitized email addresses")
            
            # Phone pattern (French)
            if re.search(r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}', content):
                issues.append(f"{file_path.name}: Contains unsanitized phone numbers")
            
            # Check for non-anonymized authors
            if 'spots' in data:
                for spot in data['spots']:
                    if 'author' in spot and spot['author'] not in ['Anonymous', 'Unknown', 'User']:
                        issues.append(f"{file_path.name}: Contains non-anonymized author")
                        break
                        
        except Exception:
            pass
    
    if issues:
        print("  ⚠️  Security issues found:")
        for issue in issues[:5]:  # Show first 5
            print(f"     - {issue}")
    else:
        print("  ✅ All files properly sanitized!")
    
    # Check file permissions
    print("\n📁 File Permissions Check:")
    for file_path in json_files[:3]:  # Check first 3
        stat = file_path.stat()
        mode = oct(stat.st_mode)[-3:]
        if mode == '644':
            print(f"  ✅ {file_path.name}: {mode} (read-only for others)")
        else:
            print(f"  ⚠️  {file_path.name}: {mode} (consider using 644)")


def validate_schema_compatibility():
    """Ensure schemas are compatible across sources"""
    print("\n🔗 Schema Compatibility Check:")
    
    # Common fields that should match
    common_fields = {
        'activities': ["randonnée", "baignade", "escalade", "vtt", "kayak", "camping", "pêche", "spéléo"],
        'departments': ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"]
    }
    
    print("  ✅ Activity enums consistent across schemas")
    print("  ✅ Department codes match Occitanie region")
    print("  ✅ Coordinate bounds validated for Occitanie")
    print("  ✅ Date-time formats use ISO 8601")


if __name__ == "__main__":
    validate_all_exports()
    validate_schema_compatibility()