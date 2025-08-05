#!/bin/bash

# SPOTS Map Validation Script
# Quick way to validate all maps

echo "🗺️  SPOTS Map Validation"
echo "======================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Navigate to validation directory
cd tests/map-validation

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start local server in background
echo "🚀 Starting local server..."
node server.js &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run validation
echo ""
echo "🧪 Running map validation tests..."
echo ""

# Check if specific scenario is provided
if [ "$1" ]; then
    node run-validation.js "$1" "${@:2}"
else
    # Run all scenarios
    node run-tests.js
fi

# Kill server
kill $SERVER_PID 2>/dev/null

echo ""
echo "✅ Validation complete!"