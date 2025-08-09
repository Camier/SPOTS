#!/bin/bash

# IGN 50GB Download Monitor
# Shows real-time progress and statistics

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

LOG_FILE="02_downloads/systematic_fixed.log"

while true; do
    clear
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}         🗺️  IGN 50GB COLLECTION DOWNLOAD MONITOR${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    
    # Check if process is running
    PID=$(pgrep -f "download_50gb_systematic.py" | head -1)
    
    if [ -n "$PID" ]; then
        echo -e "\n${GREEN}● DOWNLOAD ACTIVE${NC} (PID: $PID)"
        
        # Get CPU and memory usage
        STATS=$(ps -p $PID -o %cpu,%mem,etime --no-headers 2>/dev/null)
        if [ -n "$STATS" ]; then
            CPU=$(echo $STATS | awk '{print $1}')
            MEM=$(echo $STATS | awk '{print $2}')
            TIME=$(echo $STATS | awk '{print $3}')
            echo -e "   CPU: ${YELLOW}${CPU}%${NC}  Memory: ${YELLOW}${MEM}%${NC}  Runtime: ${YELLOW}${TIME}${NC}"
        fi
    else
        echo -e "\n${RED}○ DOWNLOAD STOPPED${NC}"
        echo -e "   To restart: ${YELLOW}cd scripts && python3 download_50gb_systematic.py &${NC}"
    fi
    
    # Current activity from log
    if [ -f "$LOG_FILE" ]; then
        echo -e "\n${CYAN}📍 Current Activity:${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Get current region/layer being downloaded
        CURRENT=$(tail -50 "$LOG_FILE" | grep -E "📍|🗺️|Zoom" | tail -3)
        echo "$CURRENT" | head -20
        
        # Get latest progress
        echo -e "\n${CYAN}📊 Latest Progress:${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        tail -100 "$LOG_FILE" | grep -E "✅|% -" | tail -5
        
        # Overall stats
        echo -e "\n${CYAN}📈 Overall Statistics:${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        OVERALL=$(tail -500 "$LOG_FILE" | grep -E "Overall Progress:|Total size:|Progress:|Rate:|ETA:" | tail -6)
        if [ -n "$OVERALL" ]; then
            echo "$OVERALL"
        else
            # Count tiles downloaded
            TILES=$(grep -c "✅" "$LOG_FILE" 2>/dev/null || echo "0")
            echo -e "   Regions completed: ${YELLOW}$TILES${NC}"
        fi
    fi
    
    # Storage stats
    echo -e "\n${CYAN}💾 Storage Status:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Total IGN_CONSOLIDATED size
    TOTAL_SIZE=$(du -sh ../IGN_CONSOLIDATED 2>/dev/null | cut -f1)
    echo -e "Total collection size: ${YELLOW}$TOTAL_SIZE${NC}"
    
    # Calculate percentage to 50GB
    TOTAL_MB=$(du -sm ../IGN_CONSOLIDATED 2>/dev/null | cut -f1)
    PERCENTAGE=$(echo "scale=2; $TOTAL_MB / 51200 * 100" | bc 2>/dev/null || echo "0")
    echo -e "Progress to 50GB:      ${YELLOW}${PERCENTAGE}%${NC}"
    
    # MBTiles files
    echo -e "\nActive MBTiles:"
    ls -lh 01_active_maps/*.mbtiles 2>/dev/null | tail -5 | awk '{print "  • " $9 ": " $5}'
    
    # Quick actions
    echo -e "\n${BLUE}⚡ Quick Actions:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "View log:    ${YELLOW}tail -f $LOG_FILE${NC}"
    echo -e "Stop:        ${YELLOW}pkill -f download_50gb_systematic${NC}"
    echo -e "Exit monitor: Press ${YELLOW}Ctrl+C${NC}"
    
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "Auto-refresh in 30 seconds..."
    
    sleep 30
done