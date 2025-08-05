#!/usr/bin/env python3
"""
Direct Ollama test
"""

import requests
import json

# Test with a very simple prompt
url = "http://localhost:11434/api/generate"
data = {
    "model": "granite3.3:8b",
    "prompt": "Write a Python function to add two numbers",
    "stream": False
}

print("Testing Ollama directly...")
response = requests.post(url, json=data, timeout=30)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Response: {result.get('response', 'No response')[:200]}")
else:
    print(f"Error: {response.text}")