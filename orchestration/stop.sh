#!/bin/bash
# Stop all services for Article Search System
# Usage: ./stop.sh

# Change to project root (parent of orchestration directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
echo -e "${RED}║   🛑 Stopping Article Search System       ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
echo ""

STOPPED_COUNT=0

# Function to stop a service by PID file
stop_service() {
    local service_name=$1
    local pid_file="orchestration/$2"
    local port=$3
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if kill -0 $PID 2>/dev/null; then
            kill $PID 2>/dev/null
            sleep 1
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID 2>/dev/null
            fi
            echo -e "${GREEN}✓${NC} Stopped $service_name (PID: $PID)"
            STOPPED_COUNT=$((STOPPED_COUNT + 1))
        else
            echo -e "${YELLOW}⚠${NC}  $service_name PID file exists but process not running"
        fi
        rm -f "$pid_file"
    else
        # Try to kill by port as fallback
        if PORT_PID=$(lsof -t -i:$port 2>/dev/null); then
            kill -9 $PORT_PID 2>/dev/null
            echo -e "${GREEN}✓${NC} Stopped $service_name (port $port)"
            STOPPED_COUNT=$((STOPPED_COUNT + 1))
        else
            echo -e "${YELLOW}⚠${NC}  $service_name not running"
        fi
    fi
}

# Stop API
stop_service "FastAPI Backend" ".pids/api.pid" "8000"

# Stop Frontend
stop_service "Search Frontend" ".pids/frontend.pid" "8501"

# Stop Analytics
stop_service "Analytics Dashboard" ".pids/analytics.pid" "8502"

# Stop OpenSearch
if docker-compose ps | grep -q "opensearch.*Up"; then
    echo -n "   Stopping OpenSearch... "
    docker-compose down > /dev/null 2>&1
    echo -e "${GREEN}✓${NC}"
    STOPPED_COUNT=$((STOPPED_COUNT + 1))
else
    echo -e "${YELLOW}⚠${NC}  OpenSearch not running"
fi

# Clean up PID directory
rm -rf orchestration/.pids

# Additional cleanup - kill any remaining processes on these ports
for port in 8000 8501 8502; do
    if PORT_PID=$(lsof -t -i:$port 2>/dev/null); then
        kill -9 $PORT_PID 2>/dev/null
    fi
done

echo ""
if [ $STOPPED_COUNT -gt 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ All Services Stopped ($STOPPED_COUNT services)     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
else
    echo -e "${YELLOW}╔════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   ⚠️  No Services Were Running             ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════╝${NC}"
fi
echo ""

