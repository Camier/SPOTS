#!/usr/bin/env python3
"""
Local Code Analyzer for SPOTS using Ollama
No more HuggingFace API limits!
"""

import requests
import json
import subprocess
import time

class LocalCodeAnalyzer:
    def __init__(self, model="granite3.3:8b"):
        self.base_url = "http://localhost:11434"
        self.model = model
        self.check_ollama()
    
    def check_ollama(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json()
                print("✅ Ollama is running!")
                print(f"Available models: {[m['name'] for m in models['models']]}")
                return True
        except:
            print("❌ Ollama not running. Start with: ollama serve")
            print("   Install: curl -fsSL https://ollama.ai/install.sh | sh")
            return False
    
    def analyze(self, code, instruction, temperature=0.1):
        """Send code to local model for analysis"""
        
        prompt = f"""{instruction}

Code to analyze:
```python
{code}
```

Fixed/Improved code:
```python"""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()['response']
                # Clean up response
                if "```" in result:
                    result = result.split("```")[0]
                return result.strip()
            else:
                return f"Error: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def fix_sql_injection(self, code):
        """Fix SQL injection vulnerabilities"""
        
        instruction = """Fix SQL injection. Use parameterized queries:"""
        
        return self.analyze(code, instruction)
    
    def add_authentication(self, code):
        """Add authentication to API endpoint"""
        
        instruction = """Add JWT authentication to this FastAPI endpoint.
Include proper error handling and dependency injection.
Use FastAPI's security utilities."""
        
        return self.analyze(code, instruction)
    
    def improve_error_handling(self, code):
        """Improve error handling"""
        
        instruction = """Improve the error handling in this code.
Add specific exception types, proper logging, and meaningful error messages.
Don't hide unexpected errors."""
        
        return self.analyze(code, instruction)

def analyze_spots_code():
    """Analyze actual SPOTS vulnerabilities with local AI"""
    
    print("🤖 LOCAL AI CODE ANALYSIS FOR SPOTS\n")
    
    analyzer = LocalCodeAnalyzer()
    
    # 1. SQL Injection from main.py
    print("\n1️⃣ FIXING SQL INJECTION")
    print("-" * 50)
    
    vulnerable_sql = """
def get_spots_by_department(dept_code: str, limit: int = 100):
    where_clause = department_bounds.get(dept_code, "1=1")
    cursor.execute(f"SELECT * FROM spots WHERE {where_clause} LIMIT {limit}")
    return cursor.fetchall()
"""
    
    print("Vulnerable code:")
    print(vulnerable_sql)
    print("\n🔧 AI Fix:")
    fixed = analyzer.fix_sql_injection(vulnerable_sql)
    print(fixed)
    
    # 2. Missing Authentication
    print("\n\n2️⃣ ADDING AUTHENTICATION")
    print("-" * 50)
    
    unprotected_endpoint = """
@app.get("/api/spots")
async def get_spots(limit: int = 100, offset: int = 0):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM spots LIMIT ? OFFSET ?", (limit, offset))
    spots = cursor.fetchall()
    conn.close()
    return {"spots": spots}
"""
    
    print("Unprotected endpoint:")
    print(unprotected_endpoint)
    print("\n🔧 AI Fix:")
    secured = analyzer.add_authentication(unprotected_endpoint)
    print(secured)
    
    # 3. Poor Error Handling
    print("\n\n3️⃣ IMPROVING ERROR HANDLING")
    print("-" * 50)
    
    bad_error_handling = """
def fetch_weather_data(location):
    try:
        response = requests.get(f"https://api.weather.com/{location}")
        return response.json()
    except:
        return None
"""
    
    print("Poor error handling:")
    print(bad_error_handling)
    print("\n🔧 AI Fix:")
    improved = analyzer.improve_error_handling(bad_error_handling)
    print(improved)

def setup_instructions():
    """Print setup instructions if Ollama not found"""
    
    print("\n📋 QUICK SETUP GUIDE:")
    print("1. Install Ollama:")
    print("   curl -fsSL https://ollama.ai/install.sh | sh")
    print("\n2. Pull a model:")
    print("   ollama pull deepseek-coder:6.7b")
    print("\n3. Run this script again!")
    print("\nAlternative models:")
    print("   - ollama pull codellama:7b-instruct (better instructions)")
    print("   - ollama pull deepseek-coder:1.3b (smaller, faster)")

if __name__ == "__main__":
    analyzer = LocalCodeAnalyzer()
    
    if analyzer.check_ollama():
        analyze_spots_code()
        
        print("\n\n✅ SUMMARY:")
        print("- Local AI is working!")
        print("- No API limits")
        print("- Complete privacy")
        print("- Fast responses")
        print("\nTo use different models:")
        print("ollama pull codellama:13b-instruct")
        print("Then update model name in LocalCodeAnalyzer()")
    else:
        setup_instructions()