#!/bin/bash
# Demo StarCoder Commands

echo "🚀 StarCoder Commands Demo"
echo "========================="
echo ""

# Make scripts executable
chmod +x starcoder_commands.sh starcoder_commands.py

# Demo 1: Fix SQL Injection
echo "1️⃣ Fixing SQL Injection"
echo "------------------------"
echo "Input: cursor.execute(f'SELECT * FROM users WHERE id={user_id}')"
echo ""
echo "Running: ./starcoder_commands.sh fix \"cursor.execute(f'SELECT * FROM users WHERE id={user_id}')\""
./starcoder_commands.sh fix "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')" 2>/dev/null || echo "Model not available"
echo ""

# Demo 2: Explain Lambda
echo "2️⃣ Explaining Lambda Function"
echo "-----------------------------"
echo "Input: lambda x: x if x <= 1 else x * factorial(x-1)"
echo ""
echo "Running: ./starcoder_commands.sh explain \"lambda x: x if x <= 1 else x * factorial(x-1)\" -l eli5"
./starcoder_commands.sh explain "lambda x: x if x <= 1 else x * factorial(x-1)" -l eli5 2>/dev/null || echo "Model not available"
echo ""

# Demo 3: Generate SQL
echo "3️⃣ Generating SQL Query"
echo "-----------------------"
echo "Request: Find top 5 customers by total order value"
echo ""
echo "Running: ./starcoder_commands.sh sql \"Find top 5 customers by total order value\""
./starcoder_commands.sh sql "Find top 5 customers by total order value" 2>/dev/null || echo "Model not available"
echo ""

# Demo 4: Quick Security Check
echo "4️⃣ Security Quick Check"
echo "-----------------------"
echo "Creating vulnerable test file..."
cat > test_vulnerable.py << 'EOF'
import os
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

def run_command(cmd):
    # Command injection vulnerability
    os.system(f"echo {cmd}")
    
password = "admin123"  # Hardcoded password
EOF

echo "Running: ./starcoder_commands.sh review test_vulnerable.py -f security"
./starcoder_commands.sh review test_vulnerable.py -f security 2>/dev/null || echo "Model not available"
echo ""

# Cleanup
rm -f test_vulnerable.py

echo "✅ Demo Complete!"
echo ""
echo "To use these commands system-wide, run:"
echo "  bash setup_starcoder_aliases.sh"
echo "  source ~/.bashrc"
echo ""
echo "Then you can use short commands like:"
echo "  cfix 'buggy code'"
echo "  creview file.py"
echo "  csql 'query description'"
echo "  code interactive"