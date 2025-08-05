#!/bin/bash
# Ollama Practical Tools - Ready-to-use commands based on community patterns

# ========== CONFIGURATION ==========
RAPID_MODEL="${OLLAMA_RAPID_MODEL:-phi3:mini}"
DEEP_MODEL="${OLLAMA_DEEP_MODEL:-mistral:7b}"
CODE_MODEL="${OLLAMA_CODE_MODEL:-codellama:7b}"

# ========== COMPARE FUNCTION ==========
ollama_compare() {
    local prompt="$1"
    local models="${2:-$RAPID_MODEL $DEEP_MODEL}"
    
    echo "🔄 Comparing models for: $prompt"
    echo "======================================"
    
    for model in $models; do
        echo -e "\n📊 Model: $model"
        start_time=$(date +%s.%N)
        
        response=$(echo "$prompt" | ollama run "$model" 2>/dev/null | head -20)
        
        end_time=$(date +%s.%N)
        elapsed=$(echo "$end_time - $start_time" | bc)
        
        echo "$response"
        echo -e "\n⏱️ Time: ${elapsed}s"
        echo "---"
    done
}

# ========== SMART QUERY FUNCTION ==========
ollama_smart() {
    local query="$1"
    local word_count=$(echo "$query" | wc -w)
    
    # Smart model selection
    if [[ "$query" =~ (code|function|debug|error|fix) ]]; then
        model="$CODE_MODEL"
    elif [[ $word_count -lt 10 ]]; then
        model="$RAPID_MODEL"
    else
        model="$DEEP_MODEL"
    fi
    
    echo "🎯 Using $model" >&2
    echo "$query" | ollama run "$model"
}

# ========== FILE WATCHER FUNCTION ==========
ollama_watch() {
    local file="$1"
    local last_hash=""
    
    echo "👁️ Watching $file for changes..."
    
    while true; do
        if [[ -f "$file" ]]; then
            current_hash=$(md5sum "$file" | awk '{print $1}')
            
            if [[ "$current_hash" != "$last_hash" ]]; then
                echo -e "\n🔄 Change detected at $(date)"
                
                # Quick analysis with rapid model
                change_summary=$(head -50 "$file" | ollama run "$RAPID_MODEL" "Summarize this file change in one line" 2>/dev/null)
                echo "⚡ Quick: $change_summary"
                
                # If significant change, deep analysis
                if [[ $(wc -l < "$file") -gt 50 ]]; then
                    echo "🔍 Running deep analysis..."
                    head -200 "$file" | ollama run "$DEEP_MODEL" "Analyze this code for issues" 2>/dev/null | head -10
                fi
                
                last_hash="$current_hash"
            fi
        fi
        sleep 2
    done
}

# ========== BATCH PROCESS FUNCTION ==========
ollama_batch() {
    local operation="$1"
    shift
    local files=("$@")
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            echo -e "\n📄 Processing: $file"
            
            case "$operation" in
                summarize)
                    head -500 "$file" | ollama run "$RAPID_MODEL" "Summarize this document in 3 sentences"
                    ;;
                review)
                    cat "$file" | ollama run "$CODE_MODEL" "Review this code for issues"
                    ;;
                explain)
                    head -100 "$file" | ollama run "$DEEP_MODEL" "Explain what this code does"
                    ;;
                *)
                    echo "Unknown operation: $operation"
                    ;;
            esac
        fi
    done
}

# ========== GIT HOOK FUNCTION ==========
ollama_git_review() {
    echo "🤖 AI Code Review"
    
    # Get staged files
    files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|go|java)$')
    
    for file in $files; do
        echo -e "\n📝 Reviewing: $file"
        
        # Get the diff
        diff=$(git diff --cached "$file")
        
        # Quick security check
        security_check=$(echo "$diff" | ollama run "$RAPID_MODEL" "Any security issues in this code? Yes/No" 2>/dev/null)
        
        if [[ "$security_check" =~ [Yy]es ]]; then
            echo "⚠️ Security concern detected!"
            echo "$diff" | ollama run "$CODE_MODEL" "Explain the security issue in this code diff"
        else
            echo "✅ No immediate security concerns"
        fi
    done
}

# ========== SHELL HELPER FUNCTION ==========
ollama_shell() {
    local cmd="$1"
    
    # Check complexity
    if [[ "$cmd" =~ (&&|\|\||for|while|if) ]]; then
        echo "🔍 Complex command detected"
        echo "$cmd" | ollama run "$DEEP_MODEL" "Explain this shell command and suggest improvements"
    else
        echo "$cmd" | ollama run "$RAPID_MODEL" "Briefly explain this shell command"
    fi
}

# ========== MAIN COMMAND HANDLER ==========
case "${1:-help}" in
    compare)
        shift
        ollama_compare "$@"
        ;;
    smart)
        shift
        ollama_smart "$@"
        ;;
    watch)
        shift
        ollama_watch "$@"
        ;;
    batch)
        shift
        ollama_batch "$@"
        ;;
    git-review)
        ollama_git_review
        ;;
    shell)
        shift
        ollama_shell "$@"
        ;;
    help|*)
        cat << EOF
🚀 Ollama Practical Tools

Usage: $0 <command> [args]

Commands:
  compare <prompt> [models]     Compare prompt across models
  smart <query>                 Smart model selection
  watch <file>                  Watch file for changes
  batch <op> <files...>         Batch process files (summarize/review/explain)
  git-review                    Review staged git changes
  shell <command>               Explain shell command

Examples:
  $0 compare "What is Docker?"
  $0 smart "Explain quantum computing"
  $0 watch main.py
  $0 batch summarize *.md
  $0 git-review
  $0 shell "find . -name '*.log' -mtime +7 -delete"

Environment Variables:
  OLLAMA_RAPID_MODEL   Model for quick responses (default: phi3:mini)
  OLLAMA_DEEP_MODEL    Model for deep analysis (default: mistral:7b)
  OLLAMA_CODE_MODEL    Model for code tasks (default: codellama:7b)
EOF
        ;;
esac