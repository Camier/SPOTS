#!/bin/bash
# Ollama Quick Start - Smart model selection based on your system

echo "🚀 Ollama Quick Start Script"
echo "=========================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Get available RAM
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
echo "💾 System RAM: ${TOTAL_RAM}GB"

# Function to pull model if not exists
pull_if_needed() {
    local model=$1
    if ! ollama list | grep -q "$model"; then
        echo "📥 Pulling $model..."
        ollama pull "$model"
    else
        echo "✓ $model already installed"
    fi
}

# Recommend and install models based on RAM
echo -e "\n📋 Recommended Models for Your System:"

if [ $TOTAL_RAM -lt 8 ]; then
    echo "⚡ Tier 1: Limited RAM (< 8GB)"
    echo "Installing minimal models..."
    
    pull_if_needed "tinyllama"
    pull_if_needed "phi3:mini"
    pull_if_needed "codegemma:2b"
    
    echo -e "\n✅ Installed models for limited RAM:"
    echo "- tinyllama: Ultra-fast general purpose"
    echo "- phi3:mini: Good reasoning, small size"
    echo "- codegemma:2b: Basic code assistance"
    
elif [ $TOTAL_RAM -lt 16 ]; then
    echo "💪 Tier 2: Standard RAM (8-16GB)"
    echo "Installing balanced models..."
    
    pull_if_needed "llama3.2:latest"
    pull_if_needed "mistral:7b"
    pull_if_needed "codellama:7b-q4_K_M"
    pull_if_needed "phi3:mini"
    
    echo -e "\n✅ Installed models for standard RAM:"
    echo "- llama3.2:latest: Best general purpose"
    echo "- mistral:7b: Excellent balance"
    echo "- codellama:7b-q4_K_M: Code analysis (quantized)"
    echo "- phi3:mini: Fast fallback"
    
elif [ $TOTAL_RAM -lt 32 ]; then
    echo "🚀 Tier 3: Power User (16-32GB)"
    echo "Installing performance models..."
    
    pull_if_needed "llama3.2:latest"
    pull_if_needed "mistral:7b-instruct"
    pull_if_needed "codellama:7b"
    pull_if_needed "deepseek-coder:6.7b"
    pull_if_needed "solar:10.7b"
    
    echo -e "\n✅ Installed models for power users:"
    echo "- llama3.2:latest: Latest general model"
    echo "- mistral:7b-instruct: Best for instructions"
    echo "- codellama:7b: Full quality code model"
    echo "- deepseek-coder:6.7b: Advanced code analysis"
    echo "- solar:10.7b: Long context (32K tokens)"
    
else
    echo "💎 Tier 4: High-End (32GB+)"
    echo "Installing premium models..."
    
    pull_if_needed "mixtral:8x7b"
    pull_if_needed "codellama:13b"
    pull_if_needed "deepseek-coder:6.7b"
    pull_if_needed "solar:10.7b"
    pull_if_needed "llama3.2:latest"
    
    echo -e "\n✅ Installed models for high-end systems:"
    echo "- mixtral:8x7b: Most capable model"
    echo "- codellama:13b: Best code understanding"
    echo "- deepseek-coder:6.7b: Specialized coding"
    echo "- solar:10.7b: Long documents"
    echo "- llama3.2:latest: Fast general purpose"
fi

# Create helper scripts
echo -e "\n📝 Creating helper scripts..."

# Quick chat script
cat > ollama-chat.sh << 'EOF'
#!/bin/bash
# Smart chat selector
RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ $RAM -lt 8 ]; then
    MODEL="phi3:mini"
elif [ $RAM -lt 16 ]; then
    MODEL="llama3.2:latest"
else
    MODEL="mistral:7b-instruct"
fi
echo "Starting chat with $MODEL..."
ollama run $MODEL
EOF

# Quick code script
cat > ollama-code.sh << 'EOF'
#!/bin/bash
# Smart code model selector
RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ $RAM -lt 8 ]; then
    MODEL="codegemma:2b"
elif [ $RAM -lt 16 ]; then
    MODEL="codellama:7b-q4_K_M"
elif [ $RAM -lt 32 ]; then
    MODEL="codellama:7b"
else
    MODEL="deepseek-coder:6.7b"
fi
echo "Starting code assistant with $MODEL..."
ollama run $MODEL
EOF

chmod +x ollama-chat.sh ollama-code.sh

# Test the setup
echo -e "\n🧪 Testing your setup..."
echo "What is 2+2?" | ollama run $(ollama list | grep -E 'phi3:mini|tinyllama|llama3.2' | head -1 | awk '{print $1}') 2>/dev/null

echo -e "\n✅ Setup Complete!"
echo -e "\n📚 Quick Usage:"
echo "- Chat: ./ollama-chat.sh"
echo "- Code: ./ollama-code.sh"
echo "- List models: ollama list"
echo "- Manual run: ollama run <model-name>"
echo -e "\n💡 Pro tip: Models are automatically selected based on your RAM!"