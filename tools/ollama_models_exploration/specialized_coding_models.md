# 🚀 Specialized Coding Models for Ollama

## 🌟 Top Coding Models Beyond StarCoder2

### 1. **DeepSeek Coder** (Already installed: deepseek-coder-gpu:6.7b)
- **Variants**: 1.3b, 6.7b, 33b
- **Strengths**: Excellent at code completion, trained on 2T tokens
- **Best for**: Python, Java, C++, JavaScript
- **Special**: Fill-in-the-middle capability

### 2. **CodeGemma**
```bash
ollama pull codegemma:2b    # 1.6GB - Ultra-fast code checks
ollama pull codegemma:7b    # 4.5GB - Full code analysis
```
- **From**: Google's Gemma family
- **Strengths**: Great at code explanation and generation
- **Best for**: Multi-language support, code understanding

### 3. **CodeLlama** (Already installed: codellama-gpu:7b)
- **Variants**: 7b, 13b, 34b, 70b
- **Strengths**: Meta's specialized coding model
- **Best for**: Complex refactoring, architecture design
- **Special**: Python-specific variant available

### 4. **Stable Code**
```bash
ollama pull stable-code:3b    # 1.6GB - Stability AI's code model
```
- **Strengths**: Balanced performance, good at completion
- **Best for**: General programming tasks
- **Special**: Trained on diverse codebases

### 5. **Granite Code** (Already have granite3.3:8b)
```bash
ollama pull granite-code:3b   # 1.9GB - IBM's code-specific model
ollama pull granite-code:8b   # 4.9GB - Larger variant
ollama pull granite-code:20b  # 12GB - Maximum capability
```
- **Strengths**: Enterprise-focused, security-aware
- **Best for**: Production code, security analysis

### 6. **WizardCoder**
```bash
ollama pull wizardcoder:7b-python   # Python-specific
ollama pull wizardcoder:13b         # General purpose
```
- **Strengths**: Instruction-following for code tasks
- **Best for**: Following complex coding instructions

### 7. **SQLCoder**
```bash
ollama pull sqlcoder:7b    # 4.1GB
ollama pull sqlcoder:15b   # 8.9GB
```
- **Strengths**: Specialized for SQL generation
- **Best for**: Database queries, schema design
- **Special**: Outperforms GPT-4 on SQL benchmarks

### 8. **Phind-CodeLlama**
```bash
ollama pull phind-codellama:34b-v2   # 19GB - Requires 32GB RAM
```
- **Strengths**: Fine-tuned on high-quality code
- **Best for**: Complex debugging, code review

### 9. **Magicoder**
```bash
ollama pull magicoder:6.7b    # 4.0GB
```
- **Strengths**: Trained with OSS-Instruct
- **Best for**: Open source code patterns

### 10. **CodeQwen** (Qwen specialized for code)
```bash
ollama pull codeqwen:7b    # 4.5GB
```
- **Strengths**: Alibaba's code model
- **Best for**: Multi-language support, Asian languages

## 📊 Quick Comparison for Our Framework

### Rapid Tier (<3GB, <2s response)
```bash
starcoder2:3b     # 1.7GB - Best overall
codegemma:2b      # 1.6GB - Google quality
stable-code:3b    # 1.6GB - Balanced
granite-code:3b   # 1.9GB - Enterprise focus
```

### Balanced Tier (4-8GB, good performance)
```bash
starcoder2:7b        # 4.0GB - Excellent completion
deepseek-coder:6.7b  # 4.3GB - Strong Python
codellama:7b         # 3.8GB - Meta quality
codegemma:7b         # 4.5GB - Good explanation
sqlcoder:7b          # 4.1GB - SQL specialist
```

### Deep Analysis Tier (>8GB, maximum capability)
```bash
starcoder2:15b       # 9.1GB - Top performance
codellama:13b        # 7.4GB - Complex tasks
sqlcoder:15b         # 8.9GB - Complex SQL
granite-code:20b     # 12GB - Enterprise grade
```

## 🎯 Specialized Use Cases

### For SQL/Database Work
```bash
# Pull these for database tasks
ollama pull sqlcoder:7b
ollama pull duckdb-nsql:7b    # DuckDB specific
```

### For Python-Heavy Projects
```bash
ollama pull wizardcoder:7b-python
ollama pull deepseek-coder:6.7b
```

### For Security Analysis
```bash
ollama pull granite-code:8b    # Security-aware
ollama pull codellama:7b       # Good at finding vulnerabilities
```

### For Documentation
```bash
ollama pull codegemma:7b       # Excellent at explaining code
ollama pull mistral:7b         # Good for technical writing
```

## 🔧 Integration with Our Framework

Update `OLLAMA_MODEL_FRAMEWORK.md` to include these models:

```yaml
Task-Specific Models:
  SQL/Database:
    rapid: starcoder2:3b
    deep: sqlcoder:15b
    specialized: sqlcoder:7b
  
  Python Development:
    rapid: codegemma:2b
    deep: deepseek-coder:6.7b
    specialized: wizardcoder:7b-python
  
  Security Review:
    rapid: granite-code:3b
    deep: granite-code:20b
    balanced: codellama:7b
  
  Code Documentation:
    rapid: phi3:mini
    deep: codegemma:7b
    balanced: mistral:7b
```

## 💡 Recommendations

1. **Start with StarCoder2 family** - Best all-around performance
2. **Add SQLCoder** if working with databases
3. **Include CodeGemma** for explanation tasks
4. **Consider DeepSeek** for Python-heavy work
5. **Use Granite** for enterprise/security focus

## 🚀 Quick Setup Script

```bash
#!/bin/bash
# pull_coding_models.sh

echo "🚀 Setting up coding models for Ollama..."

# Rapid tier (choose 2-3)
ollama pull starcoder2:3b
ollama pull codegemma:2b
ollama pull stable-code:3b

# Balanced tier (choose 2-3)
ollama pull starcoder2:7b
ollama pull deepseek-coder:6.7b
ollama pull sqlcoder:7b

# Optional specialists
read -p "Pull SQL specialist? (y/n) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ollama pull sqlcoder:7b
fi

read -p "Pull Python specialist? (y/n) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ollama pull wizardcoder:7b-python
fi

echo "✅ Coding models ready!"
ollama list
```