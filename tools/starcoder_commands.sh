#!/bin/bash
# StarCoder Commands - Shell wrapper for easy usage

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/starcoder_commands.py"

# Make sure Python script is executable
chmod +x "$PYTHON_SCRIPT"

# ========== INDIVIDUAL COMMAND FUNCTIONS ==========

# Quick fix for code issues
code-fix() {
    python3 "$PYTHON_SCRIPT" fix "$@"
}

# Code review with focus areas
code-review() {
    python3 "$PYTHON_SCRIPT" review "$@"
}

# Generate SQL from description
code-sql() {
    python3 "$PYTHON_SCRIPT" sql "$@"
}

# Explain code at different levels
code-explain() {
    python3 "$PYTHON_SCRIPT" explain "$@"
}

# Refactor code with style
code-refactor() {
    python3 "$PYTHON_SCRIPT" refactor "$@"
}

# Debug errors
code-debug() {
    python3 "$PYTHON_SCRIPT" debug "$@"
}

# Generate tests
code-test() {
    python3 "$PYTHON_SCRIPT" test "$@"
}

# Convert between languages
code-convert() {
    python3 "$PYTHON_SCRIPT" convert "$@"
}

# ========== INTERACTIVE COMMANDS ==========

# Interactive code helper
code-help() {
    echo "🚀 StarCoder Interactive Helper"
    echo "=============================="
    echo "What would you like help with?"
    echo "1) Fix code issue"
    echo "2) Review code file"
    echo "3) Generate SQL query"
    echo "4) Explain code"
    echo "5) Refactor code"
    echo "6) Debug error"
    echo "7) Generate tests"
    echo "8) Convert code language"
    echo ""
    read -p "Select option (1-8): " choice
    
    case $choice in
        1)
            read -p "Enter code or file path: " code
            read -p "Specific issue (optional): " issue
            code-fix "$code" ${issue:+-i "$issue"}
            ;;
        2)
            read -p "File to review: " file
            echo "Focus area:"
            echo "  1) Security"
            echo "  2) Performance"
            echo "  3) Style"
            echo "  4) Bugs"
            echo "  5) All (default)"
            read -p "Select (1-5): " focus_choice
            case $focus_choice in
                1) focus="security" ;;
                2) focus="performance" ;;
                3) focus="style" ;;
                4) focus="bugs" ;;
                *) focus="all" ;;
            esac
            code-review "$file" -f "$focus"
            ;;
        3)
            read -p "Describe what SQL you need: " desc
            read -p "Schema (optional): " schema
            code-sql "$desc" ${schema:+-s "$schema"}
            ;;
        4)
            read -p "Code or file to explain: " code
            echo "Explanation level:"
            echo "  1) ELI5"
            echo "  2) Beginner"
            echo "  3) Normal (default)"
            echo "  4) Expert"
            read -p "Select (1-4): " level_choice
            case $level_choice in
                1) level="eli5" ;;
                2) level="beginner" ;;
                4) level="expert" ;;
                *) level="normal" ;;
            esac
            code-explain "$code" -l "$level"
            ;;
        5)
            read -p "Code or file to refactor: " code
            echo "Refactoring style:"
            echo "  1) Clean (default)"
            echo "  2) Performance"
            echo "  3) Functional"
            echo "  4) Modern"
            echo "  5) Secure"
            read -p "Select (1-5): " style_choice
            case $style_choice in
                2) style="performance" ;;
                3) style="functional" ;;
                4) style="modern" ;;
                5) style="secure" ;;
                *) style="clean" ;;
            esac
            code-refactor "$code" -s "$style"
            ;;
        6)
            read -p "Error message: " error
            read -p "Code context (optional): " context
            code-debug "$error" ${context:+-c "$context"}
            ;;
        7)
            read -p "Code or file to test: " code
            echo "Test framework:"
            echo "  1) pytest (default)"
            echo "  2) unittest"
            echo "  3) jest"
            echo "  4) mocha"
            read -p "Select (1-4): " framework_choice
            case $framework_choice in
                2) framework="unittest" ;;
                3) framework="jest" ;;
                4) framework="mocha" ;;
                *) framework="pytest" ;;
            esac
            code-test "$code" -f "$framework"
            ;;
        8)
            read -p "Code or file to convert: " code
            read -p "From language: " from_lang
            read -p "To language: " to_lang
            code-convert "$code" "$from_lang" "$to_lang"
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
}

# ========== QUICK COMMANDS ==========

# Quick SQL injection fix
fix-sql-injection() {
    local code="${1:-}"
    if [[ -z "$code" ]]; then
        echo "Usage: fix-sql-injection 'code with SQL injection'"
        return 1
    fi
    echo "$code" | ollama run starcoder2:7b "Fix this SQL injection vulnerability and explain the fix"
}

# Quick security scan
security-scan() {
    local file="${1:-}"
    if [[ -z "$file" ]]; then
        echo "Usage: security-scan <file>"
        return 1
    fi
    code-review "$file" -f security
}

# Quick Python optimization
optimize-python() {
    local file="${1:-}"
    if [[ -z "$file" ]]; then
        echo "Usage: optimize-python <file>"
        return 1
    fi
    code-refactor "$file" -s performance
}

# ========== MAIN COMMAND HANDLER ==========

case "${1:-help}" in
    fix)
        shift
        code-fix "$@"
        ;;
    review)
        shift
        code-review "$@"
        ;;
    sql)
        shift
        code-sql "$@"
        ;;
    explain)
        shift
        code-explain "$@"
        ;;
    refactor)
        shift
        code-refactor "$@"
        ;;
    debug)
        shift
        code-debug "$@"
        ;;
    test)
        shift
        code-test "$@"
        ;;
    convert)
        shift
        code-convert "$@"
        ;;
    interactive|help-me)
        code-help
        ;;
    fix-sql)
        shift
        fix-sql-injection "$@"
        ;;
    security)
        shift
        security-scan "$@"
        ;;
    optimize)
        shift
        optimize-python "$@"
        ;;
    help|*)
        cat << EOF
🚀 StarCoder Commands

Usage: $0 <command> [options]

Commands:
  fix <code>           Quick code fix
  review <file>        Code review with focus areas
  sql <description>    Generate SQL from natural language
  explain <code>       Explain code at different levels
  refactor <code>      Refactor with different styles
  debug <error>        Debug errors with context
  test <code>          Generate unit tests
  convert <code> <from> <to>  Convert between languages

Quick Commands:
  fix-sql <code>       Fix SQL injection vulnerability
  security <file>      Security-focused code review
  optimize <file>      Optimize Python code

Interactive:
  interactive          Interactive helper mode
  help-me             Same as interactive

Examples:
  $0 fix "print('Hello world)"
  $0 review main.py -f security
  $0 sql "find top 5 customers by revenue"
  $0 explain "lambda x: x**2" -l eli5
  $0 refactor messy.py -s clean
  $0 debug "NameError: name 'x' is not defined"
  $0 test calculator.py -f pytest
  $0 convert code.js javascript python

Options vary by command. Use -h with any command for details.
EOF
        ;;
esac