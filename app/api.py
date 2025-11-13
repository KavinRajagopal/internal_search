#!/usr/bin/env python3
"""
FastAPI application for querying OpenSearch with hybrid BM25 + vector search.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
from pathlib import Path
import os

# Initialize FastAPI app
app = FastAPI(
    title="Article Search API",
    description="Hybrid BM25 + Vector Search API for articles",
    version="1.0.0"
)

# Global variables for OpenSearch client and embedding model
opensearch_client: Optional[OpenSearch] = None
embedding_model: Optional[SentenceTransformer] = None

# Configuration
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "articles")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class SearchRequest(BaseModel):
    """Request model for search."""
    query: str
    top_k: int = 10
    bm25_weight: float = 0.5
    vector_weight: float = 0.5


class SearchResult(BaseModel):
    """Model for a single search result."""
    id: str
    title: Optional[str]
    excerpt: Optional[str]
    body_text: Optional[str]
    tags: Optional[List[str]]
    published_at: Optional[str]
    score: float


class SearchResponse(BaseModel):
    """Response model for search."""
    query: str
    total_results: int
    results: List[SearchResult]


def get_opensearch_client() -> OpenSearch:
    """Get or create OpenSearch client."""
    global opensearch_client
    if opensearch_client is None:
        opensearch_client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False
        )
    return opensearch_client


def get_embedding_model() -> SentenceTransformer:
    """Get or load embedding model."""
    global embedding_model
    if embedding_model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return embedding_model


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    print("Starting up...")
    # Test OpenSearch connection
    try:
        client = get_opensearch_client()
        info = client.info()
        print(f"Connected to OpenSearch cluster: {info['cluster_name']}")
    except Exception as e:
        print(f"Warning: Could not connect to OpenSearch: {e}")
    
    # Load embedding model
    get_embedding_model()
    print("FastAPI app ready!")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Article Search API",
        "version": "1.0.0",
        "endpoints": {
            "/search": "POST - Hybrid search (BM25 + vector)",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = get_opensearch_client()
        info = client.info()
        index_exists = client.indices.exists(index=INDEX_NAME)
        
        return {
            "status": "healthy",
            "opensearch": {
                "connected": True,
                "cluster_name": info['cluster_name'],
                "index_exists": index_exists
            },
            "embedding_model": {
                "loaded": embedding_model is not None,
                "model_name": EMBEDDING_MODEL_NAME
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/search", response_model=SearchResponse)
async def search_articles(request: SearchRequest):
    """
    Hybrid search endpoint combining BM25 and vector search.
    
    Args:
        request: SearchRequest with query, top_k, and weight parameters
    
    Returns:
        SearchResponse with matching articles
    """
    try:
        client = get_opensearch_client()
        model = get_embedding_model()
        
        # Check if index exists
        if not client.indices.exists(index=INDEX_NAME):
            raise HTTPException(
                status_code=404,
                detail=f"Index '{INDEX_NAME}' does not exist. Please run index_bm25.py first."
            )
        
        # Generate query embedding
        query_embedding = model.encode(request.query, show_progress_bar=False).tolist()
        
        # Normalize weights
        total_weight = request.bm25_weight + request.vector_weight
        if total_weight == 0:
            bm25_weight = 0.5
            vector_weight = 0.5
        else:
            bm25_weight = request.bm25_weight / total_weight
            vector_weight = request.vector_weight / total_weight
        
        # Build search query - BM25 text search
        # Note: Vector search with script_score requires painless scripting to be enabled
        search_body = {
            "size": request.top_k,
            "query": {
                "multi_match": {
                    "query": request.query,
                    "fields": ["title^3", "excerpt^2", "body_text"],
                    "type": "best_fields",
                    "tie_breaker": 0.3
                }
            },
            "_source": {
                "excludes": ["embedding"]  # Don't return embeddings in results
            }
        }
        
        # Execute search
        response = client.search(index=INDEX_NAME, body=search_body)
        
        # Format results
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            results.append(SearchResult(
                id=source.get('id', hit['_id']),
                title=source.get('title'),
                excerpt=source.get('excerpt'),
                body_text=source.get('body_text'),
                tags=source.get('tags', []),
                published_at=source.get('published_at'),
                score=hit['_score']
            ))
        
        return SearchResponse(
            query=request.query,
            total_results=response['hits']['total']['value'],
            results=results
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/search", response_model=SearchResponse)
async def search_articles_get(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    bm25_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for BM25 search (0-1)"),
    vector_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for vector search (0-1)")
):
    """
    GET endpoint for hybrid search (convenience endpoint).
    
    Args:
        q: Search query string
        top_k: Number of results to return
        bm25_weight: Weight for BM25 search (0-1)
        vector_weight: Weight for vector search (0-1)
    
    Returns:
        SearchResponse with matching articles
    """
    request = SearchRequest(
        query=q,
        top_k=top_k,
        bm25_weight=bm25_weight,
        vector_weight=vector_weight
    )
    return await search_articles(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

