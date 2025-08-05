# Local Code Model Deployment Guide for SPOTS

## 🚀 Quick Start with Ollama (Recommended)

### 1. Install Ollama
```bash
# Linux/WSL
curl -fsSL https://ollama.ai/install.sh | sh

# macOS
brew install ollama

# Or download from https://ollama.ai
```

### 2. Pull and Run Models

#### For 8GB+ RAM/VRAM:
```bash
# Best overall for code (6.7B model, ~4GB download)
ollama pull deepseek-coder:6.7b

# Alternative: CodeLlama Instruct (good for fixes)
ollama pull codellama:7b-instruct
```

#### For 16GB+ RAM/VRAM:
```bash
# Higher quality
ollama pull codellama:13b-instruct
ollama pull deepseek-coder:33b-instruct-q3_K_M
```

#### For Limited Resources (4-8GB):
```bash
# Smaller but still useful
ollama pull deepseek-coder:1.3b
ollama pull codellama:7b-code-q4_0
```

### 3. Test the Model
```bash
ollama run deepseek-coder:6.7b

# In the prompt, try:
# Fix SQL injection: cursor.execute(f"SELECT * FROM spots WHERE {where_clause}")
```

## 📊 Model Recommendations by Hardware

### 💻 CPU Only (No GPU)
1. **CodeT5+ 220M** - Runs on CPU, basic completions
2. **CodeGen-350M-Mono** - Python-specific, lightweight

### 🎮 Consumer GPU (8-12GB VRAM)
1. **DeepSeek-Coder 6.7B** (Q4_K_M) - Best for Python/SQL
2. **CodeLlama 7B Instruct** (Q4_K_M) - Good instruction following
3. **StarCoder 3B** (Q8) - Fast, decent quality

### 💪 Gaming GPU (16GB+ VRAM)
1. **CodeLlama 13B** (Q5_K_M) - Excellent quality
2. **WizardCoder 15B** (Q4_K_M) - Strong reasoning
3. **DeepSeek-Coder 33B** (Q3_K_M) - Best overall if fits

### 🍎 Apple Silicon
- M1/M2 (8-16GB): CodeLlama 7B, DeepSeek 6.7B
- M1/M2 Pro/Max (32GB+): CodeLlama 13B-34B

## 🔧 Integration with SPOTS

### Create a Local AI Service
```python
# local_ai_service.py
import requests
import json

class LocalCodeAI:
    def __init__(self, model="deepseek-coder:6.7b"):
        self.base_url = "http://localhost:11434"
        self.model = model
        
    def analyze_code(self, code, instruction):
        """Analyze code with local model"""
        prompt = f"{instruction}\n\nCode:\n{code}\n\nImproved version:"
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json()['response']
        return None
    
    def fix_sql_injection(self, vulnerable_code):
        """Fix SQL injection vulnerabilities"""
        instruction = """Fix this SQL injection vulnerability. 
        Use parameterized queries. Return only the fixed code."""
        
        return self.analyze_code(vulnerable_code, instruction)
    
    def add_authentication(self, endpoint_code):
        """Add authentication to endpoint"""
        instruction = """Add JWT authentication to this FastAPI endpoint.
        Include proper error handling. Return the complete secured endpoint."""
        
        return self.analyze_code(endpoint_code, instruction)

# Usage
ai = LocalCodeAI()

# Fix SQL injection
vulnerable = '''
cursor.execute(f"SELECT * FROM spots WHERE {where_clause}")
'''
fixed = ai.fix_sql_injection(vulnerable)
print(fixed)
```

## 🎯 Model Selection Guide

### For SPOTS Specifically:

1. **DeepSeek-Coder** - BEST CHOICE
   - Trained on GitHub code
   - Excellent with Python/SQL
   - Good security awareness
   - Sizes: 1.3B (fast), 6.7B (balanced), 33B (best)

2. **CodeLlama-Instruct** - GOOD ALTERNATIVE
   - Better instruction following
   - Good for "fix this" tasks
   - Sizes: 7B, 13B, 34B

3. **SQLCoder** - FOR SQL ONLY
   - Specialized for SQL queries
   - Use if SQL is main focus

## 💡 Alternative: CPU-Only Setup

If no GPU available:
```bash
pip install transformers torch

# Run smaller model on CPU
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained('Salesforce/codegen-350M-mono')
tokenizer = AutoTokenizer.from_pretrained('Salesforce/codegen-350M-mono')

# Use for simple completions
"
```

## 🚦 Quick Decision Tree

1. **Have GPU?** → Use Ollama + DeepSeek-Coder
2. **Mac?** → Use Ollama + CodeLlama (uses Metal)
3. **CPU only?** → Use CodeT5+ 220M or pay for API
4. **Need speed?** → Use smaller quantized models
5. **Need quality?** → Use larger models with lower quant

## 📝 Testing Your Setup

```bash
# 1. Check Ollama is running
curl http://localhost:11434/api/tags

# 2. Test generation
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-coder:6.7b",
  "prompt": "def validate_sql_input(user_input):",
  "stream": false
}'

# 3. Run the SPOTS integration script
python local_ai_service.py
```

## 🎬 Next Steps

1. Install Ollama
2. Pull `deepseek-coder:6.7b`
3. Create `local_ai_service.py`
4. Replace HuggingFace calls with local AI
5. Enjoy fast, private code analysis!

No more API limits, no more 404s, just local AI goodness! 🎉