#!/bin/bash
# Setup StarCoder command aliases

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📦 Setting up StarCoder command aliases..."

# Create a dedicated bin directory if it doesn't exist
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

# Create symbolic links for main command
ln -sf "$SCRIPT_DIR/starcoder_commands.sh" "$BIN_DIR/code"
ln -sf "$SCRIPT_DIR/starcoder_commands.sh" "$BIN_DIR/sc"

# Create individual command shortcuts
cat > "$BIN_DIR/cfix" << 'EOF'
#!/bin/bash
code fix "$@"
EOF

cat > "$BIN_DIR/creview" << 'EOF'
#!/bin/bash
code review "$@"
EOF

cat > "$BIN_DIR/csql" << 'EOF'
#!/bin/bash
code sql "$@"
EOF

cat > "$BIN_DIR/cexplain" << 'EOF'
#!/bin/bash
code explain "$@"
EOF

cat > "$BIN_DIR/crefactor" << 'EOF'
#!/bin/bash
code refactor "$@"
EOF

cat > "$BIN_DIR/cdebug" << 'EOF'
#!/bin/bash
code debug "$@"
EOF

cat > "$BIN_DIR/ctest" << 'EOF'
#!/bin/bash
code test "$@"
EOF

# Make all scripts executable
chmod +x "$BIN_DIR"/{code,sc,cfix,creview,csql,cexplain,crefactor,cdebug,ctest}

# Add to PATH if not already there
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "" >> ~/.bashrc
    echo "# StarCoder commands" >> ~/.bashrc
    echo "export PATH=\"\$PATH:$BIN_DIR\"" >> ~/.bashrc
    echo "✅ Added $BIN_DIR to PATH in ~/.bashrc"
fi

# Create shell functions for even quicker access
cat > "$HOME/.starcoder_functions.sh" << 'EOF'
# StarCoder Quick Functions

# Fix last command's error
fix-last() {
    local last_cmd=$(fc -ln -1)
    local last_error=$(fc -ln -1 2>&1)
    code debug "$last_error" -c "$last_cmd"
}

# Explain last command
explain-last() {
    local last_cmd=$(fc -ln -1)
    code explain "$last_cmd"
}

# Quick SQL for current directory's database
sql-here() {
    local desc="$*"
    # Try to find schema file
    local schema=""
    if [[ -f "schema.sql" ]]; then
        schema=$(cat schema.sql)
    elif [[ -f "database/schema.sql" ]]; then
        schema=$(cat database/schema.sql)
    fi
    
    if [[ -n "$schema" ]]; then
        code sql "$desc" -s "$schema"
    else
        code sql "$desc"
    fi
}

# Review all Python files in current directory
review-all-py() {
    for file in *.py; do
        if [[ -f "$file" ]]; then
            echo "========== Reviewing $file =========="
            code review "$file" -f "${1:-all}"
            echo ""
        fi
    done
}

# Generate tests for all Python files
test-all-py() {
    for file in *.py; do
        if [[ -f "$file" && "$file" != test_* && "$file" != *_test.py ]]; then
            echo "========== Generating tests for $file =========="
            code test "$file" -f pytest > "test_${file}"
            echo "Created test_${file}"
        fi
    done
}

# Interactive fix mode
ifix() {
    code interactive
}

# Clipboard operations (if xclip is available)
if command -v xclip &> /dev/null; then
    # Fix code from clipboard
    fix-clip() {
        xclip -o | code fix -
    }
    
    # Explain code from clipboard
    explain-clip() {
        xclip -o | code explain -
    }
fi
EOF

# Add functions to bashrc
if ! grep -q ".starcoder_functions.sh" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Load StarCoder functions" >> ~/.bashrc
    echo "[ -f ~/.starcoder_functions.sh ] && source ~/.starcoder_functions.sh" >> ~/.bashrc
fi

echo "
✅ Setup complete!

🚀 Quick Start Commands:
  code fix 'buggy code'         # Fix code issues
  code review file.py           # Review a file
  code sql 'query description'  # Generate SQL
  code explain 'complex code'   # Get explanation
  code interactive              # Interactive mode

⚡ Shortcuts:
  cfix, creview, csql, cexplain, crefactor, cdebug, ctest
  
📋 Shell Functions:
  fix-last         # Fix error from last command
  explain-last     # Explain last command
  sql-here         # SQL with auto-detected schema
  review-all-py    # Review all Python files
  ifix             # Interactive helper

To activate: source ~/.bashrc
"