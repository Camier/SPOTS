#!/usr/bin/env python3
"""
Fix broad exception handlers in Python files
Replaces bare except: with specific exceptions
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

# Common exceptions to use as replacements
EXCEPTION_REPLACEMENTS = {
    'file': 'except (IOError, OSError) as e:',
    'json': 'except (json.JSONDecodeError, ValueError) as e:',
    'request': 'except (requests.RequestException, ConnectionError) as e:',
    'database': 'except (sqlite3.Error, DatabaseError) as e:',
    'scraping': 'except (AttributeError, KeyError, IndexError) as e:',
    'general': 'except Exception as e:',
}

def detect_context(lines: List[str], line_idx: int) -> str:
    """Detect the context of the exception to suggest appropriate replacement"""
    # Look at previous 10 lines for context
    context_start = max(0, line_idx - 10)
    context_lines = lines[context_start:line_idx]
    context_text = '\n'.join(context_lines).lower()
    
    # Detect context
    if 'open(' in context_text or 'file' in context_text or 'path' in context_text:
        return 'file'
    elif 'json.' in context_text or 'loads' in context_text or 'dumps' in context_text:
        return 'json'
    elif 'requests.' in context_text or 'http' in context_text or 'url' in context_text:
        return 'request'
    elif 'sqlite' in context_text or 'execute' in context_text or 'commit' in context_text:
        return 'database'
    elif 'find' in context_text or 'scrape' in context_text or 'extract' in context_text:
        return 'scraping'
    else:
        return 'general'

def fix_broad_exceptions_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """Fix broad exceptions in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return 0, [f"Error reading {file_path}: {e}"]
    
    modifications = 0
    issues = []
    modified_lines = []
    
    for i, line in enumerate(lines):
        # Match bare except:
        if re.match(r'^(\s*)except:\s*$', line):
            indent = re.match(r'^(\s*)', line).group(1)
            context = detect_context(lines, i)
            replacement = EXCEPTION_REPLACEMENTS[context]
            
            # Replace the line
            new_line = f"{indent}{replacement}\n"
            modified_lines.append(new_line)
            modifications += 1
            
            # Log the change
            print(f"✓ {file_path}:{i+1} - Replaced 'except:' with '{replacement.strip()}'")
        else:
            modified_lines.append(line)
    
    # Write back if changed
    if modifications > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
    
    return modifications, issues

def process_files(file_list: List[str]) -> None:
    """Process specific files to fix exceptions"""
    total_fixes = 0
    
    for file_path in file_list:
        path = Path(file_path)
        if path.exists():
            fixes, issues = fix_broad_exceptions_in_file(path)
            total_fixes += fixes
            
            if issues:
                for issue in issues:
                    print(f"⚠️  {issue}")
    
    print(f"\n📊 Summary:")
    print(f"  - Total exceptions fixed: {total_fixes}")

if __name__ == "__main__":
    # Files identified with broad exceptions
    files_to_fix = [
        '/home/miko/projects/spots/src/backend/services/code_improvement_service.py',
        '/home/miko/projects/spots/src/backend/scrapers/tourism_sites_scraper.py',
        '/home/miko/projects/spots/src/backend/scrapers/facebook_puppeteer_scraper.py',
        '/home/miko/projects/spots/src/backend/scrapers/spot_data_validator.py',
        '/home/miko/projects/spots/src/backend/scrapers/archived_scrapers/instagram_playwright_scraper.py',
        '/home/miko/projects/spots/src/backend/scrapers/archived_scrapers/instagram_alternative_approach.py',
        '/home/miko/projects/spots/src/backend/scrapers/tourism_scraper.py',
    ]
    
    process_files(files_to_fix)