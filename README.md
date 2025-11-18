# Article Search System

Hybrid BM25 + Vector Search system for articles using OpenSearch and FastAPI.

## Setup

### Virtual Environment
A virtual environment named `article_s` has been created with all dependencies installed.

To activate it:
```bash
source article_s/bin/activate
```

Or use the convenience script:
```bash
./run_search.sh
```

## Workflow

### 1. Start OpenSearch
```bash
docker-compose up -d
```

### 2. Convert CSV to JSONL with Embeddings
```bash
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

### 4. Start the FastAPI Server
```bash
python app/api.py
```

Or with auto-reload:
```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

### 5. Launch the Streamlit Frontend (Optional)

For a user-friendly web interface, you can use the Streamlit frontend:

```bash
streamlit run app/frontend.py
```

The frontend will be available at: http://localhost:8501

**Features:**
- 🔍 Search bar with real-time search
- 📊 Choose between BM25, Semantic, or Hybrid search modes
- 🎨 Clean, intuitive interface
- 📄 Expandable article previews
- ⚡ Real-time API health checking

**Note:** The FastAPI backend must be running on port 8000 for the frontend to work.

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

## File Locations

- **JSONL Output:** `data/articles.jsonl`
- **Embeddings:** Included in each JSON document (384-dimensional vector)
- **OpenSearch Index:** `articles` (localhost:9200)

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

## Running Multiple Components

To run the complete system with all features:

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


