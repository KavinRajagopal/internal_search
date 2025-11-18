#!/bin/bash
# Check status of all Article Search System services
# Usage: ./status.sh

# Change to project root (parent of orchestration directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   📊 Article Search System Status         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

RUNNING_COUNT=0
TOTAL_SERVICES=4

# Function to check service status
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -t -i:$port)
        echo -e "${GREEN}✓${NC} $service_name"
        echo -e "   ${BLUE}→${NC} Port: $port | PID: $PID"
        echo -e "   ${BLUE}→${NC} URL: ${YELLOW}$url${NC}"
        RUNNING_COUNT=$((RUNNING_COUNT + 1))
    else
        echo -e "${RED}✗${NC} $service_name"
        echo -e "   ${RED}→${NC} Not running on port $port"
    fi
    echo ""
}

# Check each service
check_service "OpenSearch" "9200" "http://localhost:9200"
check_service "FastAPI Backend" "8000" "http://localhost:8000/docs"
check_service "Search Frontend" "8501" "http://localhost:8501"
check_service "Analytics Dashboard" "8502" "http://localhost:8502"

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ $RUNNING_COUNT -eq $TOTAL_SERVICES ]; then
    echo -e "${GREEN}✅ All services running ($RUNNING_COUNT/$TOTAL_SERVICES)${NC}"
elif [ $RUNNING_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Partial: $RUNNING_COUNT/$TOTAL_SERVICES services running${NC}"
else
    echo -e "${RED}❌ No services running (0/$TOTAL_SERVICES)${NC}"
fi
echo ""

# Show available commands
if [ $RUNNING_COUNT -gt 0 ]; then
    echo -e "${YELLOW}📋 Available Commands:${NC}"
    echo -e "   ./logs.sh      - View all logs"
    echo -e "   ./logs.sh api  - View specific service logs"
    echo -e "   ./stop.sh      - Stop all services"
    echo ""
else
    echo -e "${YELLOW}💡 To start services:${NC}"
    echo -e "   ./start.sh"
    echo ""
fi

# Show log info
if [ -d "orchestration/logs" ] && [ "$(ls -A orchestration/logs 2>/dev/null)" ]; then
    echo -e "${BLUE}📁 Recent Log Activity:${NC}"
    for log in orchestration/logs/*.log; do
        if [ -f "$log" ]; then
            size=$(du -h "$log" | cut -f1)
            modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$log" 2>/dev/null || stat -c "%y" "$log" 2>/dev/null | cut -d. -f1)
            echo -e "   $(basename $log): ${size} (modified: $modified)"
        fi
    done
    echo ""
fi

