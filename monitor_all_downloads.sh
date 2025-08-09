#!/bin/bash

# Unified IGN Download Monitor
# Shows status of all download methods

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

while true; do
    clear
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}    🗺️  IGN 50GB COLLECTION - PARALLEL DOWNLOADS${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    
    # Check processes
    WMTS_PID=$(pgrep -f "download_50gb_collection.py" | head -1)
    BULK_PID=$(pgrep -f "bulk_download_optimized.py" | head -1)
    
    echo -e "\n${GREEN}📊 Download Methods Status:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # WMTS Status
    if [ -n "$WMTS_PID" ]; then
        echo -e "1. WMTS Tiles:     ${GREEN}● RUNNING${NC} (PID: $WMTS_PID)"
        if [ -f "IGN_CONSOLIDATED/02_downloads/download.log" ]; then
            LAST_WMTS=$(tail -1 IGN_CONSOLIDATED/02_downloads/download.log | cut -c1-50)
            echo -e "   └─ $LAST_WMTS..."
        fi
    else
        echo -e "1. WMTS Tiles:     ${RED}○ STOPPED${NC}"
    fi
    
    # Bulk API Status
    if [ -n "$BULK_PID" ]; then
        echo -e "2. Bulk API:       ${GREEN}● RUNNING${NC} (PID: $BULK_PID)"
        if [ -f "IGN_CONSOLIDATED/02_downloads/bulk_download.log" ]; then
            LAST_BULK=$(tail -1 IGN_CONSOLIDATED/02_downloads/bulk_download.log | cut -c1-50)
            echo -e "   └─ $LAST_BULK..."
        fi
    else
        echo -e "2. Bulk API:       ${YELLOW}○ READY${NC}"
    fi
    
    # Storage stats
    echo -e "\n${BLUE}💾 Storage Statistics:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Total size
    if [ -d "IGN_CONSOLIDATED" ]; then
        TOTAL_SIZE=$(du -sh IGN_CONSOLIDATED 2>/dev/null | cut -f1)
        TOTAL_MB=$(du -sm IGN_CONSOLIDATED 2>/dev/null | cut -f1)
        PERCENTAGE=$(echo "scale=2; $TOTAL_MB / 51200 * 100" | bc 2>/dev/null || echo "0")
        
        echo -e "Total Size:        ${YELLOW}$TOTAL_SIZE${NC}"
        echo -e "Progress to 50GB:  ${YELLOW}${PERCENTAGE}%${NC}"
        
        # Count MBTiles
        MBTILES_COUNT=$(find IGN_CONSOLIDATED -name "*.mbtiles" 2>/dev/null | wc -l)
        echo -e "MBTiles Files:     ${YELLOW}$MBTILES_COUNT${NC}"
        
        # Show largest files
        echo -e "\nTop 3 MBTiles:"
        find IGN_CONSOLIDATED -name "*.mbtiles" -exec ls -lh {} \; 2>/dev/null | \
            sort -k5 -hr | head -3 | \
            awk '{print "  • " $9 ": " $5}'
    fi
    
    # Quick commands
    echo -e "\n${BLUE}⚡ Quick Commands:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "View WMTS log:  ${YELLOW}tail -f IGN_CONSOLIDATED/02_downloads/download.log${NC}"
    echo -e "View Bulk log:  ${YELLOW}tail -f IGN_CONSOLIDATED/02_downloads/bulk_download.log${NC}"
    echo -e "Stop all:       ${YELLOW}pkill -f download${NC}"
    
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "Refreshing in 10 seconds... Press Ctrl+C to exit"
    
    sleep 10
done