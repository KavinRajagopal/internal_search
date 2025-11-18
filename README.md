# Article Search System

Hybrid BM25 + Vector Search system for articles using OpenSearch and FastAPI.

## Table of Contents
- [Quick Start](#quick-start)
  - [Automated Orchestration (Recommended)](#automated-orchestration-recommended)
  - [Initial Setup (First Time Only)](#initial-setup-first-time-only)
- [Manual Setup Workflow](#manual-setup-workflow-for-first-time-data-preparation)
- [API Usage](#api-usage)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [User Feedback & Analytics](#user-feedback--analytics)
- [Running Multiple Components](#running-multiple-components)
- [Orchestration Scripts Reference](#orchestration-scripts-reference)
- [Troubleshooting](#troubleshooting)
- [Dependencies](#dependencies)

---

## Quick Start

### Automated Orchestration (Recommended)

Start all services with a single command:

```bash
./orchestration/start.sh
```

This will automatically:
- ✅ Start OpenSearch (Docker container)
- ✅ Start FastAPI Backend (port 8000)
- ✅ Start Search Frontend (port 8501)
- ✅ Start Analytics Dashboard (port 8502)
- ✅ Check for conflicts and skip already-running services

**Access Points:**
- 🔍 Search Frontend: http://localhost:8501
- 📊 Analytics Dashboard: http://localhost:8502
- 📚 API Docs: http://localhost:8000/docs
- 🔧 OpenSearch: http://localhost:9200

**Other Orchestration Commands:**
```bash
./orchestration/status.sh    # Check service status
./orchestration/logs.sh      # View all logs (tail -f)
./orchestration/logs.sh api  # View specific service logs
./orchestration/stop.sh      # Stop all services
```

### Initial Setup (First Time Only)

Before using the orchestration scripts for the first time:

1. **Ensure virtual environment exists:**
   ```bash
   # If not already created
   python -m venv article_s
   source article_s/bin/activate
   pip install -r app/requirements.txt
   ```

2. **Prepare the data (if not done):**
   ```bash
   source article_s/bin/activate
   python app/convert_to_jsonl.py  # Convert CSV to JSONL with embeddings
   python app/index_bm25.py        # Index into OpenSearch
   ```

Once data is indexed, you can use `./orchestration/start.sh` anytime to launch all services.

## Manual Setup Workflow (For First-Time Data Preparation)

If you're setting up the system for the first time, follow these steps to prepare the data:

### 1. Start OpenSearch
```bash
docker-compose up -d
```

### 2. Convert CSV to JSONL with Embeddings
```bash
source article_s/bin/activate
python app/convert_to_jsonl.py
```

This will:
- Read `data/Fake.csv` (23,491 articles)
- Generate 384-dimensional embeddings using `all-MiniLM-L6-v2`
- Output to `data/articles.jsonl`

**Note:** This may take some time as it generates embeddings for all articles.

### 3. Index Documents into OpenSearch
```bash
python app/index_bm25.py
```

This will:
- Create the `articles` index in OpenSearch
- Bulk index all documents with embeddings
- Enable hybrid BM25 + vector search

### 4. Start All Services

After data is indexed, you have two options:

**Option A: Use Orchestration Scripts (Recommended)**
```bash
./orchestration/start.sh
```

**Option B: Start Services Manually**

FastAPI Server:
```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

Streamlit Frontend:
```bash
streamlit run app/frontend.py
```

Analytics Dashboard (Optional):
```bash
streamlit run app/analytics_dashboard.py --server.port 8502
```

### Frontend Features
- 🔍 Search bar with real-time search
- 📊 Choose between BM25, Semantic, or Hybrid search modes
- 🎨 Clean, intuitive interface
- 📄 Expandable article previews
- ⚡ Real-time API health checking
- 👍👎 User feedback collection

## API Usage

### Interactive Documentation
Visit: http://localhost:8000/docs

### Search Modes

The API supports **three search modes**:

1. **BM25** (`search_type=bm25`): Traditional keyword-based search
2. **Semantic** (`search_type=semantic`): Vector similarity search using embeddings
3. **Hybrid** (`search_type=hybrid`): Combined BM25 + semantic search (default)

### Search Endpoints

**POST /search** - Search with JSON body:

```bash
# BM25 Search (keyword-based)
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Donald Trump",
       "search_type": "bm25",
       "top_k": 10
     }'

# Semantic Search (vector similarity)
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "political controversy",
       "search_type": "semantic",
       "top_k": 10
     }'

# Hybrid Search (combines both with weights)
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Donald Trump politics",
       "search_type": "hybrid",
       "top_k": 10,
       "bm25_weight": 0.5,
       "vector_weight": 0.5
     }'
```

**GET /search** - Search with query parameters:

```bash
# BM25 Search
curl "http://localhost:8000/search?q=Donald+Trump&search_type=bm25&top_k=5"

# Semantic Search
curl "http://localhost:8000/search?q=political+scandal&search_type=semantic&top_k=5"

# Hybrid Search (default)
curl "http://localhost:8000/search?q=election+news&search_type=hybrid&top_k=5"
```

**GET /health** - Health check:
```bash
curl "http://localhost:8000/health"
```

## Project Structure

```
internal_search/
├── app/                      # Application code
│   ├── api.py               # FastAPI backend
│   ├── frontend.py          # Streamlit search interface
│   ├── analytics_dashboard.py  # Analytics dashboard
│   ├── index_bm25.py        # OpenSearch indexing
│   ├── convert_to_jsonl.py  # CSV to JSONL converter
│   ├── query_processor.py   # Query processing logic
│   ├── database.py          # SQLite database for feedback
│   └── requirements.txt     # Python dependencies
├── data/                     # Data files
│   ├── Fake.csv            # Source CSV data
│   └── articles.jsonl      # Generated JSONL with embeddings
├── orchestration/           # Service orchestration scripts
│   ├── start.sh            # Start all services
│   ├── stop.sh             # Stop all services
│   ├── status.sh           # Check service status
│   ├── logs.sh             # View service logs
│   ├── logs/               # Service logs (generated)
│   │   ├── api.log
│   │   ├── frontend.log
│   │   └── analytics.log
│   └── .pids/              # Process IDs (generated)
├── opensearch/              # OpenSearch configuration
│   └── mapping.json        # Index mapping definition
├── article_s/               # Virtual environment (Python packages)
├── docker-compose.yml       # OpenSearch Docker setup
├── feedback.db             # SQLite database (generated)
└── README.md               # This file
```

### Generated Files (Gitignored)
These files are automatically created during runtime:
- `data/articles.jsonl` - JSONL output with embeddings
- `orchestration/logs/*.log` - Service logs
- `orchestration/.pids/*` - Process ID files
- `feedback.db` - SQLite database for user feedback

## File Locations

- **JSONL Output:** `data/articles.jsonl`
- **Embeddings:** Included in each JSON document (384-dimensional vector)
- **OpenSearch Index:** `articles` (localhost:9200)
- **Feedback Database:** `feedback.db` (SQLite, in project root)

## Architecture

- **Embedding Model:** `all-MiniLM-L6-v2` (384 dimensions)
- **Search Modes:** 
  - BM25: Keyword-based ranking (TF-IDF)
  - Semantic: Vector similarity (cosine similarity)
  - Hybrid: Weighted combination of BM25 + Semantic
- **Database:** OpenSearch with k-NN plugin
- **API Framework:** FastAPI with interactive docs

## Field Mapping

CSV → OpenSearch:
- `title` → `title`
- `text` → `body_text` and `excerpt`
- `subject` → `tags` (array)
- `date` → `published_at` and `updated_at` (ISO format)
- Generated: `id`, `embedding`

## User Feedback & Analytics

### Feedback Collection

The system includes user feedback collection to improve search quality over time.

**Features:**
- 👍 Thumbs up / 👎 Thumbs down buttons on each search result
- Feedback is stored with context (query, search type, result position, session)
- Automatic search logging for all queries
- Session tracking to understand user journeys

**How it works:**
1. Users perform searches through the frontend
2. Each search is automatically logged with metadata
3. Users can rate results as helpful (👍) or not helpful (👎)
4. Feedback is stored in a SQLite database (`feedback.db`)
5. Analytics dashboard aggregates this data for insights

### Analytics Dashboard

Launch the analytics dashboard to monitor search performance:

```bash
streamlit run app/analytics_dashboard.py --server.port 8502
```

The dashboard will be available at: http://localhost:8502

**Dashboard Sections:**

1. **📈 Overview Metrics**
   - Total searches and unique queries
   - Total feedback and satisfaction rate
   - Average results per search

2. **🔍 Search Statistics**
   - Top 10 most searched queries
   - Search type distribution (pie chart)
   - Searches over time (line chart)

3. **💬 Feedback Analysis**
   - Feedback by search type (bar chart)
   - Most helpful articles (top rated)
   - Least helpful articles (need improvement)

4. **🚨 Problem Areas**
   - Zero-result queries that need attention
   - Low-performing search types

5. **🕐 Recent Activity**
   - Last 20 searches with metadata
   - Recent feedback submissions

**Data Retention:**
- The dashboard can show data for the last 1-30 days
- Default view: Last 7 days
- All data is stored in `feedback.db` (SQLite)

### Database Schema

**search_logs table:**
- Stores every search query with metadata
- Fields: query, processed_query, search_type, sort_by, total_results, timestamp, session_id

**feedback table:**
- Stores user feedback on search results
- Fields: query, doc_id, doc_title, search_type, rating (-1 or 1), result_position, timestamp, session_id
- Links to search_logs via foreign key

### API Endpoints

**POST /feedback** - Submit user feedback:
```bash
curl -X POST "http://localhost:8000/feedback" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "healthcare policy",
       "doc_id": "123",
       "doc_title": "Healthcare Reform Act",
       "search_type": "hybrid",
       "rating": 1,
       "result_position": 1,
       "search_log_id": 456,
       "session_id": "abc-123"
     }'
```

**GET /analytics** - Get analytics data:
```bash
# Get analytics for last 7 days
curl "http://localhost:8000/analytics?days=7"

# Get analytics for last 30 days
curl "http://localhost:8000/analytics?days=30"
```

Returns comprehensive analytics including:
- Overview statistics
- Top queries and zero-result queries
- Search type usage
- Feedback by search type
- Most/least helpful articles
- Recent searches and feedback

### Database File Location

- **Database:** `feedback.db` (SQLite, in project root)
- **Automatically created** on first API startup
- **Gitignored** to prevent tracking user data

To reset analytics data:
```bash
rm feedback.db
# Database will be recreated on next API startup
```

## Running Multiple Components

### Option 1: Orchestration Scripts (Recommended)

Use the automated orchestration scripts for the easiest experience:

```bash
# Start all services (runs in background)
./orchestration/start.sh

# Check status
./orchestration/status.sh

# View logs (live tail)
./orchestration/logs.sh           # All services
./orchestration/logs.sh api       # API only
./orchestration/logs.sh frontend  # Frontend only
./orchestration/logs.sh analytics # Analytics only

# Stop all services
./orchestration/stop.sh
```

**Features:**
- ✅ Runs all services in the background with nohup
- ✅ Stores PIDs in `orchestration/.pids/` for easy management
- ✅ Logs stored in `orchestration/logs/` (api.log, frontend.log, analytics.log)
- ✅ Color-coded output and status indicators
- ✅ Detects already-running services to avoid conflicts
- ✅ Graceful shutdown with cleanup

### Option 2: Manual Terminal Sessions

If you prefer to run services in separate terminals for debugging:

1. **Terminal 1 - OpenSearch:**
   ```bash
   docker-compose up
   ```

2. **Terminal 2 - FastAPI Backend:**
   ```bash
   source article_s/bin/activate
   uvicorn app.api:app --host 0.0.0.0 --port 8000
   ```

3. **Terminal 3 - Search Frontend:**
   ```bash
   source article_s/bin/activate
   streamlit run app/frontend.py
   ```

4. **Terminal 4 - Analytics Dashboard (Optional):**
   ```bash
   source article_s/bin/activate
   streamlit run app/analytics_dashboard.py --server.port 8502
   ```

**Access Points:**
- Search Frontend: http://localhost:8501
- Analytics Dashboard: http://localhost:8502
- API Docs: http://localhost:8000/docs
- OpenSearch: http://localhost:9200

## Orchestration Scripts Reference

The `orchestration/` directory contains automation scripts for managing the entire system:

### start.sh
Starts all services (OpenSearch, API, Frontend, Analytics) in the background.

```bash
./orchestration/start.sh
```

**Features:**
- Auto-detects and activates virtual environment
- Checks for port conflicts before starting
- Stores process IDs in `.pids/` directory
- Outputs logs to `orchestration/logs/`
- Shows access points and helpful commands

### stop.sh
Stops all running services gracefully.

```bash
./orchestration/stop.sh
```

**Features:**
- Terminates processes using stored PIDs
- Falls back to port-based killing if needed
- Stops Docker containers (OpenSearch)
- Cleans up PID files
- Reports number of services stopped

### status.sh
Checks the status of all services.

```bash
./orchestration/status.sh
```

**Features:**
- Shows running/stopped status for each service
- Displays PIDs and ports
- Shows access URLs for running services
- Displays log file sizes and modification times
- Suggests next actions based on status

### logs.sh
Views logs from running services.

```bash
# View all logs (combined, live tail)
./orchestration/logs.sh

# View specific service logs
./orchestration/logs.sh api
./orchestration/logs.sh frontend
./orchestration/logs.sh analytics
```

**Features:**
- Live tail with `tail -f`
- Color-coded output
- Validates log file existence
- Can view individual or combined logs
- Ctrl+C to exit

## Troubleshooting

### Services Won't Start

**Port already in use:**
```bash
# Check what's running on the ports
lsof -i :8000  # API
lsof -i :8501  # Frontend
lsof -i :8502  # Analytics
lsof -i :9200  # OpenSearch

# Stop all services and try again
./orchestration/stop.sh
./orchestration/start.sh
```

**Virtual environment not found:**
```bash
# Create the virtual environment
python -m venv article_s
source article_s/bin/activate
pip install -r app/requirements.txt
```

**Docker/OpenSearch issues:**
```bash
# Check Docker is running
docker ps

# Restart OpenSearch
docker-compose down
docker-compose up -d

# Check OpenSearch health
curl http://localhost:9200/_cluster/health?pretty
```

### Services Not Responding

**Check service status:**
```bash
./orchestration/status.sh
```

**View logs for errors:**
```bash
./orchestration/logs.sh           # All logs
./orchestration/logs.sh api       # API logs only
./orchestration/logs.sh frontend  # Frontend logs only
```

**Restart specific service:**
```bash
# Stop all
./orchestration/stop.sh

# Start again
./orchestration/start.sh
```

### Search Not Working

**No results returned:**
- Ensure data is indexed: `python app/index_bm25.py`
- Check OpenSearch has data: `curl http://localhost:9200/articles/_count`
- Verify API is running: `curl http://localhost:8000/health`

**Slow searches:**
- Semantic search is slower than BM25 (embeddings computation)
- Hybrid search combines both, so takes longer
- Consider reducing `top_k` parameter for faster results

### Frontend/Analytics Not Loading

**Browser shows "Connection refused":**
- Check if services are running: `./orchestration/status.sh`
- Ensure API is running on port 8000 (frontend depends on it)
- Check logs: `./orchestration/logs.sh frontend`

**Streamlit shows errors:**
- Check Python dependencies are installed: `pip install -r app/requirements.txt`
- Verify virtual environment is activated: `source article_s/bin/activate`

### Clean Reset

If all else fails, perform a clean reset:

```bash
# Stop everything
./orchestration/stop.sh
docker-compose down

# Remove generated files
rm -f feedback.db
rm -rf orchestration/logs/*
rm -rf orchestration/.pids/*

# Restart OpenSearch
docker-compose up -d
sleep 10

# Re-index data (if needed)
source article_s/bin/activate
python app/index_bm25.py

# Start services
./orchestration/start.sh
```

## Dependencies

See `app/requirements.txt`:
- sentence-transformers
- opensearch-py
- pandas
- python-dateutil
- fastapi
- uvicorn[standard]
- streamlit
- requests
- pyspellchecker
- plotly

Install all dependencies:
```bash
pip install -r app/requirements.txt
```

---

## Summary

This Article Search System provides a complete solution for searching articles using modern NLP techniques:

1. **🚀 Quick Start:** Use `./orchestration/start.sh` to launch everything
2. **🔍 Three Search Modes:** BM25, Semantic, and Hybrid search
3. **📊 Analytics:** Track user behavior and search quality
4. **💻 User-Friendly:** Beautiful Streamlit frontends for search and analytics
5. **🛠️ Easy Management:** Orchestration scripts for starting, stopping, and monitoring

For questions or issues, check the [Troubleshooting](#troubleshooting) section.

