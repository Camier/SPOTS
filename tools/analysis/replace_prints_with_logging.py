#!/usr/bin/env python3
"""
Replace print statements with proper logging
Handles common print patterns and converts them to structured logs
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

# Patterns to match different print styles
PRINT_PATTERNS = [
    # Standard print
    (r'^(\s*)print\((.*)\)$', r'\1logger.info(\2)'),
    # Print with f-string
    (r'^(\s*)print\(f["\'](.+?)["\']\)$', r'\1logger.info("\2")'),
    # Print with format
    (r'^(\s*)print\((.+?)\.format\((.*?)\)\)$', r'\1logger.info(\2, \3)'),
    # Print with %
    (r'^(\s*)print\((.+?) % (.+?)\)$', r'\1logger.info(\2, \3)'),
    # Error-like prints
    (r'^(\s*)print\(["\']Error:(.+?)["\']\)$', r'\1logger.error("\1")'),
    (r'^(\s*)print\(["\']Warning:(.+?)["\']\)$', r'\1logger.warning("\1")'),
    # Debug-like prints
    (r'^(\s*)print\(["\']Debug:(.+?)["\']\)$', r'\1logger.debug("\1")'),
]

def needs_import(content: str) -> bool:
    """Check if file already has logging import"""
    return 'from backend.core.logging_config import logger' not in content

def add_import(content: str) -> str:
    """Add logging import after other imports"""
    lines = content.split('\n')
    import_added = False
    last_import_idx = 0
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i
        elif last_import_idx > 0 and not import_added and line.strip() == '':
            # Add import after the last import line
            lines.insert(last_import_idx + 1, 'from backend.core.logging_config import logger')
            import_added = True
            break
    
    if not import_added and last_import_idx > 0:
        lines.insert(last_import_idx + 1, 'from backend.core.logging_config import logger')
    
    return '\n'.join(lines)

def replace_prints_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """Replace print statements in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return 0, [f"Error reading {file_path}: {e}"]
    
    original_content = content
    lines = content.split('\n')
    modified_lines = []
    replacements = 0
    issues = []
    
    for i, line in enumerate(lines):
        modified = False
        new_line = line
        
        # Skip comments and strings
        stripped = line.strip()
        if stripped.startswith('#') or '# print' in line or '#print' in line:
            modified_lines.append(line)
            continue
        
        # Try each pattern
        for pattern, replacement in PRINT_PATTERNS:
            if re.match(pattern, line):
                new_line = re.sub(pattern, replacement, line)
                modified = True
                replacements += 1
                break
        
        # Handle complex prints that don't match patterns
        if not modified and 'print(' in line and not line.strip().startswith('#'):
            # Mark for manual review
            issues.append(f"Line {i+1}: Complex print statement needs manual review: {line.strip()}")
        
        modified_lines.append(new_line)
    
    # Join lines back
    new_content = '\n'.join(modified_lines)
    
    # Add import if needed and replacements were made
    if replacements > 0 and needs_import(new_content):
        new_content = add_import(new_content)
    
    # Write back if changed
    if new_content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return replacements, issues

def process_directory(directory: Path) -> None:
    """Process all Python files in directory"""
    total_replacements = 0
    total_files = 0
    all_issues = []
    
    # Find all Python files
    py_files = list(directory.rglob('*.py'))
    
    print(f"Found {len(py_files)} Python files to process")
    
    for py_file in py_files:
        # Skip venv, node_modules, etc
        if any(part in py_file.parts for part in ['venv', 'node_modules', '__pycache__', '.git']):
            continue
        
        replacements, issues = replace_prints_in_file(py_file)
        
        if replacements > 0:
            total_replacements += replacements
            total_files += 1
            print(f"✓ {py_file}: Replaced {replacements} print statements")
        
        if issues:
            all_issues.extend([(py_file, issue) for issue in issues])
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  - Files modified: {total_files}")
    print(f"  - Print statements replaced: {total_replacements}")
    print(f"  - Issues requiring manual review: {len(all_issues)}")
    
    # Save issues for manual review
    if all_issues:
        with open('print_replacement_issues.txt', 'w') as f:
            f.write("Print statements requiring manual review:\n\n")
            for file_path, issue in all_issues:
                f.write(f"{file_path}:\n  {issue}\n\n")
        print(f"\n⚠️  See print_replacement_issues.txt for complex cases")

if __name__ == "__main__":
    # Process backend directory
    backend_dir = Path('/home/miko/projects/spots/src/backend')
    process_directory(backend_dir)