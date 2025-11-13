#!/bin/bash
# Article Search Setup Script
# This script activates the virtual environment and provides commands

cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0.32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Article Search Environment ===${NC}"
echo ""
echo "Activating virtual environment..."
source article_s/bin/activate

echo -e "${GREEN}Environment activated!${NC}"
echo ""
echo -e "${BLUE}Available commands:${NC}"
echo "  1. Convert CSV to JSONL with embeddings:"
echo "     python app/convert_to_jsonl.py"
echo ""
echo "  2. Index documents into OpenSearch:"
echo "     python app/index_bm25.py"
echo ""
echo "  3. Start the FastAPI server:"
echo "     python app/api.py"
echo "     or: uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo -e "${BLUE}To deactivate the environment:${NC}"
echo "  deactivate"
echo ""

# Keep the shell active in the virtual environment
exec $SHELL


