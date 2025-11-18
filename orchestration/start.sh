#!/bin/bash
# Start all services for Article Search System
# Usage: ./start.sh

set -e

# Change to project root (parent of orchestration directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🚀 Starting Article Search System       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Create necessary directories
mkdir -p orchestration/logs
mkdir -p orchestration/.pids

# Check if virtual environment exists
if [ ! -d "article_s" ]; then
    echo -e "${RED}❌ Virtual environment 'article_s' not found!${NC}"
    echo "Please create it first with: python -m venv article_s"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source article_s/bin/activate

# Check if OpenSearch is already running
if docker-compose ps | grep -q "opensearch.*Up"; then
    echo -e "${YELLOW}⚠️  OpenSearch already running${NC}"
else
    echo -e "${BLUE}📦 Starting OpenSearch...${NC}"
    docker-compose up -d
    echo "   Waiting for OpenSearch to be ready..."
    sleep 5
    echo -e "${GREEN}   ✓ OpenSearch started${NC}"
fi

# Check if API is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  API already running on port 8000${NC}"
else
    echo -e "${BLUE}🔧 Starting FastAPI Backend...${NC}"
    nohup uvicorn app.api:app --host 0.0.0.0 --port 8000 > orchestration/logs/api.log 2>&1 &
    API_PID=$!
    echo $API_PID > orchestration/.pids/api.pid
    echo "   PID: $API_PID"
    sleep 2
    echo -e "${GREEN}   ✓ API started${NC}"
fi

# Check if Frontend is already running
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 8501${NC}"
else
    echo -e "${BLUE}🔍 Starting Search Frontend...${NC}"
    nohup streamlit run app/frontend.py --server.port 8501 --server.headless true > orchestration/logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > orchestration/.pids/frontend.pid
    echo "   PID: $FRONTEND_PID"
    sleep 2
    echo -e "${GREEN}   ✓ Frontend started${NC}"
fi

# Check if Analytics is already running
if lsof -Pi :8502 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Analytics already running on port 8502${NC}"
else
    echo -e "${BLUE}📊 Starting Analytics Dashboard...${NC}"
    nohup streamlit run app/analytics_dashboard.py --server.port 8502 --server.headless true > orchestration/logs/analytics.log 2>&1 &
    ANALYTICS_PID=$!
    echo $ANALYTICS_PID > orchestration/.pids/analytics.pid
    echo "   PID: $ANALYTICS_PID"
    sleep 2
    echo -e "${GREEN}   ✓ Analytics started${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ All Services Started Successfully!    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📍 Access Points:${NC}"
echo -e "   🔍 Search Frontend:      ${BLUE}http://localhost:8501${NC}"
echo -e "   📊 Analytics Dashboard:  ${BLUE}http://localhost:8502${NC}"
echo -e "   📚 API Docs:             ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   🔧 OpenSearch:           ${BLUE}http://localhost:9200${NC}"
echo ""
echo -e "${YELLOW}📋 Useful Commands:${NC}"
echo -e "   ./orchestration/status.sh    - Check service status"
echo -e "   ./orchestration/logs.sh      - View all logs"
echo -e "   ./orchestration/logs.sh api  - View API logs only"
echo -e "   ./orchestration/stop.sh      - Stop all services"
echo ""
echo -e "${GREEN}💡 Tip: Services are running in the background. Use './logs.sh' to monitor them.${NC}"
echo ""

