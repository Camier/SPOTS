#!/bin/bash
# Validation script for Toulouse Weather Spots consolidation

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Validating Toulouse Weather Spots Consolidation${NC}"
echo "=================================================="

# Track validation results
ERRORS=0
WARNINGS=0

# Function to check item
check_item() {
    local item="$1"
    local type="$2"
    local critical="$3"
    
    if [ -e "$item" ]; then
        echo -e "${GREEN}✓${NC} $type: $item"
        return 0
    else
        if [ "$critical" = "critical" ]; then
            echo -e "${RED}✗${NC} $type: $item ${RED}(MISSING - CRITICAL)${NC}"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠${NC} $type: $item ${YELLOW}(Missing - Optional)${NC}"
            ((WARNINGS++))
        fi
        return 1
    fi
}

echo -e "\n${YELLOW}1. Checking Project Structure${NC}"
echo "------------------------------"
check_item "." "Project Root" "critical"
check_item "src/backend" "Backend Directory" "critical"
check_item "src/frontend" "Frontend Directory" "critical"
check_item "data" "Data Directory" "critical"
check_item "scripts" "Scripts Directory" "critical"
check_item "tests" "Tests Directory" "critical"
check_item "docs" "Documentation Directory" "critical"

echo -e "\n${YELLOW}2. Checking Configuration Files${NC}"
echo "--------------------------------"
check_item "README.md" "README" "critical"
check_item "package.json" "NPM Config" "critical"
check_item "requirements.txt" "Python Requirements" "critical"
check_item ".env.example" "Environment Template" "critical"
check_item ".gitignore" "Git Ignore" "critical"
check_item ".git" "Git Repository" "critical"

echo -e "\n${YELLOW}3. Checking Scripts${NC}"
echo "-------------------"
check_item "scripts/setup.sh" "Setup Script" "critical"
check_item "scripts/migrate_data.py" "Migration Script" "critical"
check_item "scripts/start.sh" "Start Script" "critical"

# Check if scripts are executable
for script in scripts/*.sh scripts/*.py; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo -e "${GREEN}✓${NC} Executable: $script"
    elif [ -f "$script" ]; then
        echo -e "${RED}✗${NC} Not executable: $script"
        ((ERRORS++))
    fi
done

echo -e "\n${YELLOW}4. Checking Source Projects${NC}"
echo "----------------------------"
check_item "/home/miko/projects/secret-toulouse-spots" "Scraper Project" "critical"
check_item "/home/miko/projects/active/weather-map-app" "Weather App" "critical"

echo -e "\n${YELLOW}5. Checking Source Databases${NC}"
echo "-----------------------------"
DB_COUNT=0
for db in \
    "/home/miko/projects/secret-toulouse-spots/database/toulouse_spots.db" \
    "/home/miko/projects/secret-toulouse-spots/database/hidden_spots.db" \
    "/home/miko/projects/active/weather-map-app/database/hidden_spots.db"
do
    if [ -f "$db" ]; then
        echo -e "${GREEN}✓${NC} Found: $db"
        ((DB_COUNT++))
    fi
done
echo -e "  ${BLUE}Total databases found: $DB_COUNT${NC}"

echo -e "\n${YELLOW}6. Directory Permissions${NC}"
echo "------------------------"
# Check write permissions
for dir in data scripts src tests; do
    if [ -w "$dir" ]; then
        echo -e "${GREEN}✓${NC} Writable: $dir"
    else
        echo -e "${RED}✗${NC} Not writable: $dir"
        ((ERRORS++))
    fi
done

echo -e "\n${YELLOW}7. Python Environment${NC}"
echo "---------------------"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python3: $(python3 --version)"
else
    echo -e "${RED}✗${NC} Python3 not found"
    ((ERRORS++))
fi

if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip3: $(pip3 --version | cut -d' ' -f1-2)"
else
    echo -e "${RED}✗${NC} pip3 not found"
    ((ERRORS++))
fi

echo -e "\n${YELLOW}8. Node.js Environment${NC}"
echo "----------------------"
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓${NC} Node.js: $(node --version)"
else
    echo -e "${RED}✗${NC} Node.js not found"
    ((ERRORS++))
fi

if command -v npm &> /dev/null; then
    echo -e "${GREEN}✓${NC} npm: $(npm --version)"
else
    echo -e "${RED}✗${NC} npm not found"
    ((ERRORS++))
fi

echo -e "\n${YELLOW}9. Available Disk Space${NC}"
echo "-----------------------"
DISK_USAGE=$(df -h . | awk 'NR==2 {print $4}')
echo -e "${BLUE}Free space: $DISK_USAGE${NC}"

# Summary
echo -e "\n${BLUE}===============================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}===============================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ PERFECT! All validations passed!${NC}"
    echo -e "${GREEN}The consolidation is ready to proceed.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  READY with $WARNINGS warnings${NC}"
    echo -e "${YELLOW}The consolidation can proceed, but check warnings.${NC}"
    exit 0
else
    echo -e "${RED}❌ FAILED with $ERRORS errors and $WARNINGS warnings${NC}"
    echo -e "${RED}Please fix critical issues before proceeding.${NC}"
    exit 1
fi
