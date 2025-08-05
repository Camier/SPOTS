# 🚀 StarCoder Commands Implementation Guide

## 📦 Installation

```bash
# 1. Make scripts executable
chmod +x starcoder_commands.sh starcoder_commands.py

# 2. Run setup for aliases
bash setup_starcoder_aliases.sh

# 3. Reload shell
source ~/.bashrc
```

## 🎯 Available Commands

### Main Command Interface

```bash
# Using main command
code <command> [options]

# Or short alias
sc <command> [options]
```

### Core Commands

#### 1. **Fix Code Issues**
```bash
# Fix syntax or bugs
code fix "print('Hello world)"
code fix buggy.py -i "undefined variable"

# Short alias
cfix "for i in range(10) print(i)"
```

#### 2. **Code Review**
```bash
# Review with different focus areas
code review main.py -f security
code review app.js -f performance
code review utils.py -f bugs

# Short alias
creview vulnerable.py
```

#### 3. **Generate SQL**
```bash
# Natural language to SQL
code sql "find customers who ordered in last 30 days"
code sql "top 5 products by revenue" -s "CREATE TABLE products(id, name, price)"

# Short alias  
csql "delete duplicate records"
```

#### 4. **Explain Code**
```bash
# Different explanation levels
code explain "lambda x: x**2" -l eli5
code explain complex.py -l expert
code explain algorithm.js -l beginner

# Short alias
cexplain "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
```

#### 5. **Refactor Code**
```bash
# Different refactoring styles
code refactor messy.py -s clean
code refactor slow.py -s performance
code refactor old.js -s modern
code refactor unsafe.py -s secure

# Short alias
crefactor legacy.py
```

#### 6. **Debug Errors**
```bash
# Debug with context
code debug "NameError: name 'x' is not defined"
code debug "TypeError: unhashable type" -c "my_dict[my_list] = 1"

# Short alias
cdebug "ImportError: No module named requests"
```

#### 7. **Generate Tests**
```bash
# Different test frameworks
code test calculator.py -f pytest
code test utils.js -f jest
code test api.py -f unittest

# Short alias
ctest mymodule.py
```

#### 8. **Convert Code**
```bash
# Language conversion
code convert script.js javascript python
code convert algo.py python rust
code convert function.java java golang
```

## ⚡ Quick Commands

```bash
# Fix SQL injection
code fix-sql "cursor.execute(f'SELECT * FROM users WHERE id={uid}')"

# Security scan
code security main.py

# Optimize Python
code optimize slow_function.py

# Interactive mode
code interactive
# or
code help-me
```

## 🔧 Shell Functions

After setup, these functions are available:

```bash
# Fix error from last command
fix-last

# Explain last command
explain-last

# SQL with auto-detected schema
sql-here "find all active users"

# Review all Python files
review-all-py
review-all-py security  # With specific focus

# Generate tests for all Python files
test-all-py

# Interactive fix mode
ifix
```

## 🔗 Git Integration

### Install Pre-commit Hook
```bash
# Copy hook to your repo
cp git_hooks/pre-commit-starcoder .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Features
- Automatic security review before commit
- Bug detection in staged files
- Commit message suggestions
- Non-blocking by default (can be configured)

## 📋 Integration Examples

### VS Code Tasks

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Fix Current File",
      "type": "shell",
      "command": "code fix ${file}",
      "group": "build"
    },
    {
      "label": "Review for Security",
      "type": "shell",
      "command": "code review ${file} -f security",
      "group": "test"
    },
    {
      "label": "Generate Tests",
      "type": "shell",
      "command": "code test ${file} -f pytest > test_${fileBasename}",
      "group": "test"
    }
  ]
}
```

### Makefile Integration

```makefile
.PHONY: review test-gen optimize security-check

review:
	@for f in *.py; do \
		echo "Reviewing $$f..."; \
		code review $$f; \
	done

test-gen:
	@code test src/*.py -f pytest > tests/test_generated.py

optimize:
	@code refactor src/*.py -s performance

security-check:
	@code review . -f security
```

### CI/CD Pipeline

```yaml
# .github/workflows/code-review.yml
name: StarCoder Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Ollama
        run: |
          curl -fsSL https://ollama.ai/install.sh | sh
          
      - name: Pull StarCoder
        run: |
          ollama pull starcoder2:3b
          ollama pull starcoder2:7b
          
      - name: Security Review
        run: |
          for file in $(find . -name "*.py"); do
            ./starcoder_commands.sh review "$file" -f security
          done
```

## 🎨 Customization

### Configure Models

Edit `starcoder_commands.py` to change default models:

```python
self.models = {
    "rapid": "starcoder2:3b",      # Change to your preferred rapid model
    "balanced": "starcoder2:7b",    # Change to your preferred balanced model
    "sql": "sqlcoder:7b",          # Change to your SQL specialist
    "python": "deepseek-coder:6.7b", # Change to your Python specialist
}
```

### Add Custom Commands

Add new functions to `starcoder_commands.py`:

```python
def custom_analysis(self, code: str) -> Dict:
    """Your custom analysis"""
    prompt = f"Perform custom analysis on:\n{code}"
    return self._run_ollama(self.models["balanced"], prompt)
```

## 💡 Tips & Tricks

1. **Pipe Support**: All commands support piping
   ```bash
   cat complex.py | code explain -
   git diff | code review - -f bugs
   ```

2. **File or Direct Input**: Commands accept both
   ```bash
   code fix "buggy code"
   code fix buggy_file.py
   ```

3. **Model Override**: Use environment variables
   ```bash
   OLLAMA_CODE_MODEL=codellama:13b code review file.py
   ```

4. **Batch Processing**: Use shell loops
   ```bash
   find . -name "*.py" -exec code review {} -f security \;
   ```

5. **Output Redirection**: Save results
   ```bash
   code explain complex.py > documentation.md
   code test module.py > test_module.py
   ```

## 🚀 Quick Start Examples

```bash
# Fix a syntax error
code fix "def hello() print('Hi')"

# Review file for security issues
code review api.py -f security

# Generate SQL from description
code sql "calculate monthly revenue by product category"

# Explain complex code simply
code explain "decorators.py" -l eli5

# Refactor for better performance
code refactor slow_function.py -s performance

# Debug an error
code debug "KeyError: 'user_id'" -c "data = {'id': 1}"

# Generate pytest tests
code test calculator.py -f pytest

# Convert JavaScript to Python
code convert utils.js javascript python
```

## 🔍 Troubleshooting

1. **Command not found**: Run `source ~/.bashrc` or restart terminal
2. **Model not available**: Pull required models with `ollama pull <model>`
3. **Slow responses**: Use rapid models (3b) for quick tasks
4. **Out of memory**: Use smaller models or increase system RAM

---

With these commands, you have powerful AI-assisted coding tools at your fingertips!