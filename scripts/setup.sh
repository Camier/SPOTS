#!/bin/bash
# Setup script for Toulouse Weather Spots project

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🌦️ Toulouse Weather Spots - Setup Script${NC}"
echo "========================================="

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found:${NC} $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found:${NC} $(node --version)"

# Check SQLite
if ! command -v sqlite3 &> /dev/null; then
    echo -e "${RED}❌ SQLite3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SQLite3 found:${NC} $(sqlite3 --version)"

# Create virtual environment
echo -e "\n${YELLOW}Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install Node.js dependencies
echo -e "\n${YELLOW}Installing Node.js dependencies...${NC}"
npm install
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

# Create necessary directories
echo -e "\n${YELLOW}Creating directory structure...${NC}"
mkdir -p data/{exports,cache,backups}
mkdir -p logs
mkdir -p config

# Create .gitkeep files
touch data/exports/.gitkeep
touch data/cache/.gitkeep
touch logs/.gitkeep

echo -e "${GREEN}✓ Directory structure created${NC}"

# Copy environment file
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}Creating environment file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env with your configuration${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Download spaCy model for French NLP
echo -e "\n${YELLOW}Downloading French language model...${NC}"
python -m spacy download fr_core_news_sm || echo -e "${YELLOW}⚠️  Failed to download spaCy model${NC}"

# Initialize database
echo -e "\n${YELLOW}Initializing database...${NC}"
if [ ! -f "data/toulouse_spots.db" ]; then
    python -c "
from src.backend.utils.database import init_database
init_database()
print('Database initialized')
" 2>/dev/null || echo -e "${YELLOW}⚠️  Database will be created on first run${NC}"
else
    echo -e "${GREEN}✓ Database already exists${NC}"
fi

# Set permissions for scripts
echo -e "\n${YELLOW}Setting script permissions...${NC}"
chmod +x scripts/*.sh 2>/dev/null || true
echo -e "${GREEN}✓ Script permissions set${NC}"

# Create user agents file if not exists
if [ ! -f "config/user_agents.txt" ]; then
    echo -e "\n${YELLOW}Creating user agents file...${NC}"
    cat > config/user_agents.txt << 'EOF'
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15
EOF
    echo -e "${GREEN}✓ User agents file created${NC}"
fi

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your configuration"
echo "2. Run migrations: python -m src.backend.utils.database migrate"
echo "3. Start the application: ./scripts/start.sh"
echo ""
echo -e "${GREEN}Happy exploring! 🗺️${NC}"
