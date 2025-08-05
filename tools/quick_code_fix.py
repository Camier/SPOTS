#!/usr/bin/env python3
"""
Quick Code Fix with Local AI - PERSONAL USE
No fancy UI, just AI fixes!
"""

import requests
import sys

def fix_code(code_snippet, issue_type="general"):
    """Get AI to fix your code - simple and direct"""
    
    prompts = {
        "sql": "Fix SQL injection vulnerability. Use parameterized queries:",
        "auth": "Add JWT authentication to this FastAPI endpoint:",
        "error": "Improve error handling with specific exceptions:",
        "general": "Fix and improve this code:"
    }
    
    prompt = f"{prompts.get(issue_type, prompts['general'])}\n\n{code_snippet}\n\nFixed:"
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "granite3.3:8b",
            "prompt": prompt,
            "temperature": 0.1,
            "stream": False
        },
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json().get('response', 'No fix generated')
    else:
        return f"Error: {response.status_code}"

# Quick examples
if __name__ == "__main__":
    print("🔧 QUICK AI CODE FIXER\n")
    
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            code = f.read()
        issue = sys.argv[2] if len(sys.argv) > 2 else "general"
    else:
        # Example vulnerable code
        code = '''
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
'''
        issue = "sql"
    
    print(f"Fixing {issue} issue...")
    print("Original:", code.strip())
    print("\nAI Fix:")
    print(fix_code(code, issue))
    
    print("\n💡 Usage: python quick_code_fix.py [file] [sql|auth|error|general]")