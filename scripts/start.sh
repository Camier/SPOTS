#!/bin/bash
# Start script for Toulouse Weather Spots

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=8085
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🌦️  Starting Toulouse Weather Spots${NC}"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Running setup...${NC}"
    "$PROJECT_DIR/scripts/setup.sh"
fi

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Check if .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${YELLOW}Please configure .env file and restart${NC}"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    pkill -f "uvicorn src.backend.main:app" 2>/dev/null || true
    pkill -f "http.server $FRONTEND_PORT" 2>/dev/null || true
    echo -e "${GREEN}✓ Shutdown complete${NC}"
}

trap cleanup EXIT INT TERM

# Start backend API
echo -e "\n${GREEN}Starting backend API on port $BACKEND_PORT...${NC}"
cd "$PROJECT_DIR"
uvicorn src.backend.main:app --reload --port $BACKEND_PORT &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend server
echo -e "\n${GREEN}Starting frontend on port $FRONTEND_PORT...${NC}"
cd "$PROJECT_DIR/src/frontend"
python -m http.server $FRONTEND_PORT &
FRONTEND_PID=$!

# Display access information
echo -e "\n${GREEN}✅ Application started successfully!${NC}"
echo -e "\n📍 Access points:"
echo -e "  Frontend: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  API Docs: ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop${NC}\n"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
