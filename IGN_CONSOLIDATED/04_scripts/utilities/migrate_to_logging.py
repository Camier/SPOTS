#!/usr/bin/env python3
"""
Script to help migrate print statements to proper logging
"""
import os
import re
from pathlib import Path

def analyze_print_statements(file_path):
    """Analyze print statements in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all print statements
    print_pattern = r'print\s*\([^)]+\)'
    matches = re.finditer(print_pattern, content)
    
    issues = []
    for match in matches:
        line_num = content[:match.start()].count('\n') + 1
        statement = match.group()
        
        # Categorize the print statement
        if 'error' in statement.lower() or 'exception' in statement.lower():
            level = 'ERROR'
        elif 'warning' in statement.lower() or 'warn' in statement.lower():
            level = 'WARNING'
        elif 'debug' in statement.lower():
            level = 'DEBUG'
        else:
            level = 'INFO'
        
        issues.append({
            'line': line_num,
            'statement': statement,
            'suggested_level': level
        })
    
    return issues

def generate_migration_report():
    """Generate a report of all print statements that need migration"""
    src_dir = Path(__file__).parent.parent / "src"
    tools_dir = Path(__file__).parent.parent / "tools"
    
    report = []
    
    for directory in [src_dir, tools_dir]:
        for py_file in directory.rglob("*.py"):
            issues = analyze_print_statements(py_file)
            if issues:
                report.append({
                    'file': str(py_file.relative_to(Path(__file__).parent.parent)),
                    'count': len(issues),
                    'issues': issues[:5]  # Show first 5 examples
                })
    
    # Sort by number of print statements
    report.sort(key=lambda x: x['count'], reverse=True)
    
    return report

def main():
    """Generate migration report"""
    report = generate_migration_report()
    
    print("# Print Statement Migration Report\n")
    print(f"Total files with print statements: {len(report)}")
    print(f"Total print statements found: {sum(r['count'] for r in report)}\n")
    
    print("## Top 10 Files to Migrate:\n")
    
    for item in report[:10]:
        print(f"### {item['file']} ({item['count']} statements)")
        print("\nExamples:")
        for issue in item['issues']:
            print(f"- Line {issue['line']}: `{issue['statement']}` → logger.{issue['suggested_level'].lower()}()")
        print()
    
    print("\n## Migration Steps:\n")
    print("1. Add to top of file:")
    print("   ```python")
    print("   from src.config.logging_config import get_logger")
    print("   logger = get_logger(__name__)")
    print("   ```\n")
    print("2. Replace print statements according to suggestions above")
    print("3. Test to ensure logging works correctly")

if __name__ == "__main__":
    main()