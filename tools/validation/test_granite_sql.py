#!/usr/bin/env python3
"""
Test Granite for SQL injection fixing
"""

import requests
import json

url = "http://localhost:11434/api/generate"

# Test SQL injection fix
prompt = """Fix this SQL injection vulnerability in Python. Use parameterized queries:

cursor.execute(f"SELECT * FROM spots WHERE {where_clause}")

Fixed code:"""

data = {
    "model": "granite3.3:8b",
    "prompt": prompt,
    "temperature": 0.1,
    "stream": False
}

print("🗂️ Testing SQL Injection Fix with Granite 3.3")
print("=" * 50)
print("Vulnerable code:")
print('cursor.execute(f"SELECT * FROM spots WHERE {where_clause}")')
print("\nAsking Granite to fix it...")

response = requests.post(url, json=data, timeout=30)

if response.status_code == 200:
    result = response.json()
    print("\n✅ Granite's fix:")
    print(result.get('response', 'No response'))
else:
    print(f"\n❌ Error: {response.status_code}")