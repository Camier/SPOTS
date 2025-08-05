# 🛠️ SPOTS Development Tools

This directory contains development tools for the SPOTS project, including AI-powered code analysis and improvement utilities.

## 📁 Directory Structure

```
tools/
├── geoai/                    # Geospatial AI tools
├── ollama_models_exploration/# Ollama model documentation
├── ollama_*.py              # Ollama framework components
├── ollama_*.sh              # Ollama shell utilities
├── starcoder_*.py           # StarCoder command implementations
└── starcoder_*.sh           # StarCoder shell wrappers
```

## 🚀 AI Code Analysis Tools

### Ollama Framework
Advanced hybrid AI analysis system with intelligent model routing:

- **ollama_model_manager.py** - Smart model selection and management
- **ollama_hybrid_analyzer.py** - Rapid + deep analysis framework
- **ollama_community_commands.py** - Community-inspired commands
- **ollama_practical_tools.sh** - Ready-to-use shell commands
- **ollama_quick_start.sh** - Quick setup script

### StarCoder Commands
AI-powered code operations using StarCoder2 models:

- **starcoder_commands.py** - Python implementation of 8 commands
- **starcoder_commands.sh** - Shell wrapper for easy usage
- **setup_starcoder_aliases.sh** - Setup script for aliases

## 🎯 Quick Start

### Using Ollama Tools
```bash
# Quick start with Ollama
./tools/ollama_quick_start.sh

# Use practical tools
./tools/ollama_practical_tools.sh compare "What is recursion?"
./tools/ollama_practical_tools.sh smart "Explain quantum computing"
./tools/ollama_practical_tools.sh git-review
```

### Using StarCoder Commands
```bash
# Setup aliases
source ./tools/setup_starcoder_aliases.sh

# Use commands
starfix "TypeError: undefined"
starreview main.py
starsql "Get top customers by revenue"
```

## 🔧 Available Commands

### Ollama Commands
- `compare` - Compare responses across models
- `smart` - Smart model selection based on query
- `batch` - Process multiple files
- `watch` - Monitor files for changes
- `shell` - Get shell command help
- `git-review` - Review staged changes

### StarCoder Commands
- `fix` - Fix code issues
- `review` - Comprehensive code review
- `explain` - Explain code functionality
- `sql` - Generate SQL queries
- `refactor` - Refactor for clarity/performance
- `debug` - Debug errors
- `test` - Generate test suites
- `convert` - Convert between languages

## 📚 Documentation

- See `ollama_workflow_examples.md` for usage patterns
- Check `ollama_models_exploration/` for model details
- Review individual Python files for API documentation

## 🔌 Integration

These tools integrate with:
- Git hooks for automated code review
- VS Code tasks for IDE integration
- CI/CD pipelines for quality checks
- Claude slash commands for chat interface

## 🚀 Model Requirements

Ensure these models are available:
```bash
ollama pull phi3:mini      # Rapid responses
ollama pull mistral:7b     # Deep analysis
ollama pull codellama:7b   # Code tasks
ollama pull starcoder2:3b  # Quick fixes
ollama pull starcoder2:7b  # Complex code
```

---

For more details, see the main project documentation or individual tool READMEs.