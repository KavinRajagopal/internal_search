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

Install all dependencies:
```bash
pip install -r app/requirements.txt
```


