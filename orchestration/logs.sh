#!/bin/bash
# View logs for Article Search System services
# Usage: ./logs.sh [service]
#   service: api, frontend, analytics, or all (default)

# Change to project root (parent of orchestration directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SERVICE=${1:-all}

# Check if logs directory exists
if [ ! -d "orchestration/logs" ]; then
    echo -e "${RED}❌ Logs directory not found!${NC}"
    echo "Run ./orchestration/start.sh first to start the services."
    exit 1
fi

# Function to check if log file exists and has content
check_log() {
    local logfile=$1
    if [ ! -f "$logfile" ]; then
        echo -e "${RED}❌ Log file not found: $logfile${NC}"
        return 1
    elif [ ! -s "$logfile" ]; then
        echo -e "${YELLOW}⚠️  Log file is empty: $logfile${NC}"
        return 1
    fi
    return 0
}

case $SERVICE in
    api)
        echo -e "${BLUE}📋 API Logs (Ctrl+C to exit)${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        if check_log "orchestration/logs/api.log"; then
            tail -f orchestration/logs/api.log
        fi
        ;;
    
    frontend)
        echo -e "${BLUE}📋 Frontend Logs (Ctrl+C to exit)${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        if check_log "orchestration/logs/frontend.log"; then
            tail -f orchestration/logs/frontend.log
        fi
        ;;
    
    analytics)
        echo -e "${BLUE}📋 Analytics Logs (Ctrl+C to exit)${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        if check_log "orchestration/logs/analytics.log"; then
            tail -f orchestration/logs/analytics.log
        fi
        ;;
    
    all)
        echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║   📋 All Service Logs (Ctrl+C to exit)    ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
        echo ""
        
        # Check which logs exist
        LOGS_TO_TAIL=""
        
        if [ -f "orchestration/logs/api.log" ] && [ -s "orchestration/logs/api.log" ]; then
            LOGS_TO_TAIL="$LOGS_TO_TAIL orchestration/logs/api.log"
            echo -e "${GREEN}✓${NC} Including API logs"
        fi
        
        if [ -f "orchestration/logs/frontend.log" ] && [ -s "orchestration/logs/frontend.log" ]; then
            LOGS_TO_TAIL="$LOGS_TO_TAIL orchestration/logs/frontend.log"
            echo -e "${GREEN}✓${NC} Including Frontend logs"
        fi
        
        if [ -f "orchestration/logs/analytics.log" ] && [ -s "orchestration/logs/analytics.log" ]; then
            LOGS_TO_TAIL="$LOGS_TO_TAIL orchestration/logs/analytics.log"
            echo -e "${GREEN}✓${NC} Including Analytics logs"
        fi
        
        if [ -z "$LOGS_TO_TAIL" ]; then
            echo -e "${RED}❌ No log files found or all are empty${NC}"
            echo "Run ./start.sh first to start the services."
            exit 1
        fi
        
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        # Tail all logs together
        tail -f $LOGS_TO_TAIL
        ;;
    
    *)
        echo -e "${RED}❌ Unknown service: $SERVICE${NC}"
        echo ""
        echo -e "${YELLOW}Usage:${NC}"
        echo "  ./logs.sh           - View all logs"
        echo "  ./logs.sh api       - View API logs only"
        echo "  ./logs.sh frontend  - View Frontend logs only"
        echo "  ./logs.sh analytics - View Analytics logs only"
        echo ""
        exit 1
        ;;
esac

