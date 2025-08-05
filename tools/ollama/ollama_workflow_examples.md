# 🚀 Ollama Workflow Examples - Community Patterns

Based on real usage from GitHub, Reddit, and automation platforms.

## 📋 Popular Community Patterns

### 1. **Multi-Model Comparison** (ollama-multirun pattern)
```bash
#!/bin/bash
# compare_models.sh - Run same prompt on multiple models

PROMPT="$1"
MODELS=("phi3:mini" "llama3.2:latest" "mistral:7b")

for model in "${MODELS[@]}"; do
    echo "=== $model ==="
    echo "$PROMPT" | ollama run $model --verbose 2>&1 | grep -E "(response|eval rate)"
    echo
done
```

### 2. **File Watcher + Auto Analysis** (Automation pattern)
```python
#!/usr/bin/env python3
# watch_and_analyze.py - Monitor files and analyze changes

import time
from pathlib import Path
import subprocess

def analyze_file(filepath):
    """Analyze file with appropriate model"""
    ext = Path(filepath).suffix
    
    if ext in ['.py', '.js', '.java']:
        model = "codellama:7b"
        prompt = f"Review this code change in {filepath}"
    elif ext in ['.md', '.txt']:
        model = "llama3.2:latest"
        prompt = f"Summarize changes in {filepath}"
    else:
        return
    
    # Analyze with Ollama
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True
    )
    
    print(f"\n🔍 Analysis of {filepath}:")
    print(result.stdout)

# Watch for changes
watched_files = {}
while True:
    for file in Path(".").glob("**/*.py"):
        mtime = file.stat().st_mtime
        if file not in watched_files or watched_files[file] != mtime:
            analyze_file(file)
            watched_files[file] = mtime
    time.sleep(5)
```

### 3. **Shell Command Helper** (aichat pattern)
```bash
#!/bin/bash
# ai_shell.sh - Get AI help for shell commands

ai_explain() {
    local cmd="$1"
    echo "Explaining: $cmd" | ollama run phi3:mini "Explain this shell command: $cmd"
}

ai_improve() {
    local cmd="$1"
    echo "Improving: $cmd" | ollama run mistral:7b "Suggest improvements for: $cmd"
}

# Usage: ai_explain "find . -name '*.log' -mtime +7 -delete"
```

### 4. **Batch Document Processing** (n8n workflow pattern)
```python
#!/usr/bin/env python3
# batch_summarize.py - Process multiple documents

import os
from pathlib import Path
import json

def process_documents(directory, operation="summarize"):
    """Process all documents in directory"""
    
    results = {}
    
    for file in Path(directory).glob("*.txt"):
        print(f"Processing {file.name}...")
        
        # Read content
        content = file.read_text()[:2000]  # First 2000 chars
        
        # Determine model based on length
        if len(content) < 500:
            model = "tinyllama"  # Fast for short docs
        else:
            model = "mistral:7b"  # Better for longer docs
        
        # Process
        prompt = f"{operation}: {content}"
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True
        )
        
        # Save result
        output_file = file.stem + f"_{operation}.txt"
        Path(output_file).write_text(result.stdout)
        
        results[file.name] = {
            "model": model,
            "output": output_file,
            "status": "success" if result.returncode == 0 else "failed"
        }
    
    # Save summary
    Path("batch_summary.json").write_text(json.dumps(results, indent=2))
    print(f"\n✅ Processed {len(results)} documents")
```

### 5. **Git Hook Integration** (Automation pattern)
```bash
#!/bin/bash
# .git/hooks/pre-commit - AI code review before commit

echo "🤖 Running AI code review..."

# Get staged files
files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|go)$')

for file in $files; do
    echo "Reviewing $file..."
    
    # Quick review with fast model
    review=$(git diff --cached "$file" | ollama run codegemma:2b "Review this code diff for issues")
    
    # If issues found, do deep review
    if echo "$review" | grep -qiE "(bug|issue|problem|vulnerable)"; then
        echo "⚠️ Potential issues detected, running deep analysis..."
        deep_review=$(git diff --cached "$file" | ollama run codellama:7b "Analyze this code diff for security and bugs")
        echo "$deep_review"
        
        # Ask for confirmation
        read -p "Continue with commit? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
done
```

### 6. **API Integration** (Power Automate pattern)
```python
#!/usr/bin/env python3
# ollama_api_server.py - Simple API wrapper for Ollama

from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Endpoint for external tools to use Ollama"""
    
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'llama3.2:latest')
    task = data.get('task', 'general')
    
    # Select model based on task
    model_map = {
        'code': 'codellama:7b',
        'sql': 'granite3.3:8b',
        'summarize': 'mistral:7b',
        'quick': 'phi3:mini'
    }
    
    selected_model = model_map.get(task, model)
    
    # Run Ollama
    result = subprocess.run(
        ["ollama", "run", selected_model, prompt],
        capture_output=True,
        text=True
    )
    
    return jsonify({
        'model': selected_model,
        'response': result.stdout,
        'task': task
    })

# Run: flask run
# Use: curl -X POST http://localhost:5000/analyze -H "Content-Type: application/json" -d '{"prompt":"explain recursion","task":"quick"}'
```

### 7. **Intelligent Model Router** (Hybrid approach)
```python
#!/usr/bin/env python3
# smart_ollama.py - Route to best model based on query

import re
import subprocess

def route_query(query):
    """Route query to appropriate model"""
    
    query_lower = query.lower()
    
    # Simple routing rules
    if len(query.split()) < 10:
        model = "phi3:mini"  # Quick questions
    elif any(word in query_lower for word in ['code', 'function', 'bug', 'error']):
        model = "codellama:7b"  # Code questions
    elif any(word in query_lower for word in ['sql', 'database', 'query']):
        model = "granite3.3:8b"  # SQL questions
    elif any(word in query_lower for word in ['explain', 'how', 'why']):
        model = "mistral:7b"  # Explanations
    else:
        model = "llama3.2:latest"  # General
    
    return model

def smart_query(query):
    """Smart query with model routing"""
    
    model = route_query(query)
    print(f"🎯 Using {model} for this query")
    
    # Run query
    result = subprocess.run(
        ["ollama", "run", model, query],
        capture_output=True,
        text=True
    )
    
    return result.stdout

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
        response = smart_query(query)
        print(response)
```

## 🛠️ Integration Patterns

### VS Code Extension Pattern
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "AI Explain",
      "type": "shell",
      "command": "ollama run codellama:7b 'Explain this code: ${selectedText}'",
      "problemMatcher": []
    },
    {
      "label": "AI Refactor",
      "type": "shell",
      "command": "ollama run codellama:7b 'Refactor for clarity: ${selectedText}'",
      "problemMatcher": []
    }
  ]
}
```

### Makefile Integration
```makefile
# AI-powered make commands

.PHONY: ai-review ai-test ai-docs

ai-review:
	@echo "🤖 AI Code Review"
	@find . -name "*.py" -newer .last-review -exec sh -c 'echo "Reviewing $$1"; ollama run codellama:7b "Review this Python file" < "$$1"' _ {} \;
	@touch .last-review

ai-test:
	@echo "🧪 Generating tests"
	@ollama run codellama:7b "Generate pytest tests for: $$(cat $(FILE))"

ai-docs:
	@echo "📚 Generating documentation"
	@ollama run mistral:7b "Generate documentation for: $$(cat $(FILE))"
```

### Docker Compose Pattern
```yaml
# docker-compose.yml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama
    command: serve
    
  ollama-ui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

volumes:
  ollama:
```

## 📱 Quick Implementation Guide

### 1. **Start Simple**
```bash
# Basic comparison
for model in tinyllama phi3:mini mistral:7b; do
    echo "=== $model ==="
    echo "What is Docker?" | ollama run $model | head -n 5
done
```

### 2. **Add Intelligence**
```bash
# Smart model selection
query="$1"
words=$(echo "$query" | wc -w)

if [ $words -lt 10 ]; then
    model="phi3:mini"
else
    model="mistral:7b"
fi

ollama run $model "$query"
```

### 3. **Integrate Everywhere**
- Git hooks for code review
- VS Code tasks for refactoring
- Makefiles for documentation
- CI/CD for automated analysis
- APIs for external tools

## 🎯 Best Practices from Community

1. **Model Selection**
   - Use small models (phi3, tinyllama) for rapid responses
   - Use specialized models (codellama, sqlcoder) for domain tasks
   - Keep 2-3 models loaded for different use cases

2. **Performance**
   - Pre-load frequently used models
   - Use streaming for long responses
   - Implement caching for repeated queries

3. **Integration**
   - Start with shell scripts
   - Move to Python for complex logic
   - Use APIs for external integration
   - Leverage existing tools (n8n, Make, Zapier)

4. **Workflow Automation**
   - File watchers for auto-analysis
   - Git hooks for code review
   - Cron jobs for reports
   - Event triggers for real-time processing