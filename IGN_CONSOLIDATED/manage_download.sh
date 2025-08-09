#!/bin/bash

# IGN 50GB Download Manager
# Ensures download runs in background and can be managed easily

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOWNLOAD_SCRIPT="$SCRIPT_DIR/scripts/download_50gb_systematic.py"
LOG_FILE="$SCRIPT_DIR/02_downloads/systematic_fixed.log"
PID_FILE="$SCRIPT_DIR/.download.pid"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

function start_download() {
    if is_running; then
        echo -e "${YELLOW}Download is already running with PID $(cat $PID_FILE)${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Starting IGN 50GB download in background...${NC}"
    cd "$SCRIPT_DIR/scripts"
    nohup python3 download_50gb_systematic.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 2
    if is_running; then
        echo -e "${GREEN}✅ Download started successfully (PID: $(cat $PID_FILE))${NC}"
        echo -e "   Log file: $LOG_FILE"
        echo -e "   Monitor with: ./monitor_download.sh"
    else
        echo -e "${RED}❌ Failed to start download${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

function stop_download() {
    if ! is_running; then
        echo -e "${YELLOW}Download is not running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping download (PID: $PID)...${NC}"
    kill $PID 2>/dev/null
    
    sleep 2
    if ! is_running; then
        echo -e "${GREEN}✅ Download stopped${NC}"
        rm -f "$PID_FILE"
    else
        echo -e "${RED}⚠️ Download still running, forcing stop...${NC}"
        kill -9 $PID 2>/dev/null
        rm -f "$PID_FILE"
    fi
}

function restart_download() {
    echo -e "${YELLOW}Restarting download...${NC}"
    stop_download
    sleep 2
    start_download
}

function status_download() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}● Download is RUNNING${NC} (PID: $PID)"
        
        # Show process stats
        ps -p $PID -o pid,ppid,%cpu,%mem,etime,cmd --no-headers
        
        # Show latest progress
        echo -e "\n${YELLOW}Latest progress:${NC}"
        tail -5 "$LOG_FILE" | grep -E "✅|Progress:|Total size:|Rate:"
        
        # Show storage
        echo -e "\n${YELLOW}Storage status:${NC}"
        TOTAL_SIZE=$(du -sh "$SCRIPT_DIR" | cut -f1)
        TOTAL_MB=$(du -sm "$SCRIPT_DIR" | cut -f1)
        PERCENTAGE=$(echo "scale=2; $TOTAL_MB / 51200 * 100" | bc 2>/dev/null || echo "0")
        echo -e "   Total size: $TOTAL_SIZE"
        echo -e "   Progress to 50GB: ${PERCENTAGE}%"
    else
        echo -e "${RED}○ Download is STOPPED${NC}"
        echo -e "   Start with: $0 start"
    fi
}

function is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        fi
    fi
    
    # Check if process is running without PID file
    ACTUAL_PID=$(pgrep -f "download_50gb_systematic.py" | head -1)
    if [ -n "$ACTUAL_PID" ]; then
        echo $ACTUAL_PID > "$PID_FILE"
        return 0
    fi
    
    return 1
}

function show_help() {
    echo "IGN 50GB Download Manager"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|monitor|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the download in background"
    echo "  stop     - Stop the download"
    echo "  restart  - Restart the download"
    echo "  status   - Show download status"
    echo "  monitor  - Open real-time monitor"
    echo "  help     - Show this help message"
}

# Main
case "$1" in
    start)
        start_download
        ;;
    stop)
        stop_download
        ;;
    restart)
        restart_download
        ;;
    status)
        status_download
        ;;
    monitor)
        "$SCRIPT_DIR/monitor_download.sh"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        status_download
        echo ""
        echo "Use '$0 help' for more options"
        ;;
esac