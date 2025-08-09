#!/bin/bash

# IGN Download Progress Monitor
# Shows real-time status of the 50GB download operation

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

clear

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    🗺️  IGN 50GB COLLECTION DOWNLOAD MONITOR${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

while true; do
    # Get current size
    CURRENT_SIZE=$(du -sh IGN_CONSOLIDATED 2>/dev/null | cut -f1)
    
    # Count MBTiles files
    MBTILES_COUNT=$(find IGN_CONSOLIDATED -name "*.mbtiles" -type f 2>/dev/null | wc -l)
    
    # Count total tiles
    TOTAL_TILES=0
    for db in IGN_CONSOLIDATED/**/*.mbtiles; do
        if [ -f "$db" ]; then
            TILES=$(sqlite3 "$db" "SELECT COUNT(*) FROM tiles" 2>/dev/null || echo 0)
            TOTAL_TILES=$((TOTAL_TILES + TILES))
        fi
    done
    
    # Check if download process is running
    if pgrep -f "download_50gb" > /dev/null; then
        STATUS="${GREEN}🟢 DOWNLOADING${NC}"
    else
        STATUS="${YELLOW}⚠️  STOPPED${NC}"
    fi
    
    # Get last log lines
    if [ -f "IGN_CONSOLIDATED/02_downloads/download.log" ]; then
        LAST_LOG=$(tail -1 IGN_CONSOLIDATED/02_downloads/download.log 2>/dev/null | cut -c1-60)
    else
        LAST_LOG="No log file found"
    fi
    
    # Calculate percentage (50GB = 51200 MB)
    CURRENT_MB=$(du -sm IGN_CONSOLIDATED 2>/dev/null | cut -f1)
    PERCENTAGE=$(echo "scale=3; $CURRENT_MB / 51200 * 100" | bc 2>/dev/null || echo "0")
    
    # Display status
    echo -e "\n${GREEN}📊 Current Status:${NC}"
    echo -e "   Status: $STATUS"
    echo -e "   Total Size: ${YELLOW}$CURRENT_SIZE${NC}"
    echo -e "   MBTiles Files: ${YELLOW}$MBTILES_COUNT${NC}"
    echo -e "   Total Tiles: ${YELLOW}$(printf "%'d" $TOTAL_TILES)${NC}"
    echo -e "   Progress: ${YELLOW}${PERCENTAGE}%${NC} of 50GB"
    
    echo -e "\n${BLUE}📝 Latest Activity:${NC}"
    echo -e "   $LAST_LOG..."
    
    echo -e "\n${BLUE}💡 Commands:${NC}"
    echo -e "   View log: ${YELLOW}tail -f IGN_CONSOLIDATED/02_downloads/download.log${NC}"
    echo -e "   Stop: ${YELLOW}pkill -f download_50gb${NC}"
    echo -e "   Resume: ${YELLOW}cd IGN_CONSOLIDATED && python3 scripts/download_50gb_collection.py &${NC}"
    
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "Press Ctrl+C to exit monitor (download continues in background)"
    
    sleep 10
    clear
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}    🗺️  IGN 50GB COLLECTION DOWNLOAD MONITOR${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
done