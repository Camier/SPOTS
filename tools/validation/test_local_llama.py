#!/usr/bin/env python3
"""
Quick test of local Llama model
"""

from local_code_analyzer import LocalCodeAnalyzer

print("🦙 Testing Llama 3.2 for code analysis\n")

analyzer = LocalCodeAnalyzer(model="codellama-gpu:7b")

# Test just SQL injection fix
vulnerable = """
cursor.execute(f"SELECT * FROM spots WHERE {where_clause}")
"""

print("Fixing SQL injection...")
result = analyzer.fix_sql_injection(vulnerable)
print(f"Result: {result}")