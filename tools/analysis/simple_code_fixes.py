#!/usr/bin/env python3
"""
Simple fixes for SPOTS - just the essentials
"""

print("QUICK FIXES FOR SPOTS\n")

print("1. SQL INJECTION FIX:")
print("-" * 30)
print("""
# In main.py, replace this:
cursor.execute(f"SELECT * FROM spots WHERE {where_clause}")

# With this:
DEPT_CONDITIONS = {
    "09": ("latitude < 43.2 AND longitude < 2.0", []),
    "12": ("latitude > 44.2 AND longitude > 2.2", [])
}
condition = DEPT_CONDITIONS.get(dept_code, ("1=1", []))[0]
cursor.execute(f"SELECT * FROM spots WHERE {condition} LIMIT ? OFFSET ?", (limit, offset))
""")

print("\n2. MOVE HARDCODED STUFF:")
print("-" * 30)
print("""
# Create .env file:
IGN_API_KEY=your_actual_key_here
DB_PATH=spots.db

# In code:
import os
api_key = os.getenv("IGN_API_KEY", "essentiels")
db_path = os.getenv("DB_PATH", "spots.db")
""")

print("\n3. BASIC ERROR HANDLING:")
print("-" * 30)
print("""
# Instead of:
try:
    response = requests.get(url)
    return response.json()
except:
    return None

# Do:
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
except Exception as e:
    print(f"Error: {e}")
    return None
""")

print("\nThat's it! The main issues are:")
print("- SQL injection in main.py")
print("- Hardcoded API keys")
print("- Basic error handling")
print("\nFix these and you're good for personal use.")