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

## API Usage

### Interactive Documentation
Visit: http://localhost:8000/docs

### Search Endpoints

**POST /search** - Search with JSON body:
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Donald Trump",
       "top_k": 10,
       "bm25_weight": 0.5,
       "vector_weight": 0.5
     }'
```

**GET /search** - Search with query parameters:
```bash
curl "http://localhost:8000/search?q=Donald+Trump&top_k=5"
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
- **Search Type:** Hybrid (BM25 + Vector Similarity)
- **Database:** OpenSearch with k-NN plugin
- **API Framework:** FastAPI

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


