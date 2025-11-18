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
from enum import Enum
import os
from app.query_processor import QueryProcessor
from app.database import log_search, save_feedback, get_analytics

# Initialize FastAPI app
app = FastAPI(
    title="Article Search API",
    description="Multi-mode search API supporting BM25, Semantic (Vector), and Hybrid search for articles",
    version="2.0.0"
)

# Global variables for OpenSearch client, embedding model, query processor, and suggestions cache
opensearch_client: Optional[OpenSearch] = None
embedding_model: Optional[SentenceTransformer] = None
query_processor: Optional[QueryProcessor] = None
suggestions_cache: List[str] = []

# Configuration
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "articles")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class SearchType(str, Enum):
    """Search type enumeration."""
    BM25 = "bm25"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    RRF = "rrf"


class SortBy(str, Enum):
    """Sort option enumeration."""
    RELEVANCE = "relevance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    TITLE_AZ = "title_az"


class SearchRequest(BaseModel):
    """Request model for search."""
    query: str
    search_type: SearchType = SearchType.HYBRID
    top_k: int = 10
    bm25_weight: float = 0.5
    vector_weight: float = 0.5
    sort_by: SortBy = SortBy.RELEVANCE


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
    processed_query: Optional[str] = None
    total_results: int
    results: List[SearchResult]
    search_log_id: Optional[int] = None


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    query: str
    doc_id: str
    doc_title: Optional[str]
    search_type: str
    rating: int  # 1 for thumbs up, -1 for thumbs down
    result_position: int
    search_log_id: Optional[int] = None
    session_id: Optional[str] = None


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


def get_query_processor() -> QueryProcessor:
    """Get or create query processor."""
    global query_processor
    if query_processor is None:
        print("Initializing query processor...")
        query_processor = QueryProcessor()
    return query_processor


def load_suggestions():
    """Load article titles from OpenSearch for autocomplete suggestions."""
    global suggestions_cache
    try:
        client = get_opensearch_client()
        if not client.indices.exists(index=INDEX_NAME):
            print("Index does not exist yet, skipping suggestions loading")
            return
        
        # Get article titles (limit to 1000 for performance)
        response = client.search(
            index=INDEX_NAME,
            body={
                "size": 1000,
                "_source": ["title"],
                "query": {"match_all": {}}
            }
        )
        
        # Extract unique titles
        titles = set()
        for hit in response['hits']['hits']:
            title = hit['_source'].get('title')
            if title and isinstance(title, str):
                titles.add(title.strip())
        
        suggestions_cache = sorted(list(titles))
        print(f"Loaded {len(suggestions_cache)} article titles for suggestions")
    except Exception as e:
        print(f"Warning: Could not load suggestions: {e}")
        suggestions_cache = []


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
    
    # Load suggestions
    load_suggestions()
    
    print("FastAPI app ready!")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Article Search API",
        "version": "2.0.0",
        "search_types": {
            "bm25": "Keyword-based search using BM25 algorithm",
            "semantic": "Vector similarity search using embeddings",
            "hybrid": "Combined BM25 + semantic search with configurable weights"
        },
        "endpoints": {
            "/search": "GET/POST - Multi-mode search (bm25, semantic, hybrid)",
            "/health": "GET - Health check",
            "/docs": "GET - Interactive API documentation"
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


@app.get("/suggestions")
async def get_suggestions(
    q: str = Query(..., min_length=2, description="Query prefix for suggestions"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions")
):
    """
    Get search suggestions based on query prefix.
    Returns matching article titles.
    
    Args:
        q: Query prefix (minimum 2 characters)
        limit: Maximum number of suggestions to return
    
    Returns:
        List of matching titles
    """
    if not q or len(q) < 2:
        return []
    
    q_lower = q.lower()
    
    # Find matching titles
    matches = [title for title in suggestions_cache if q_lower in title.lower()]
    
    # Return limited results
    return matches[:limit]


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback on a search result.
    
    Args:
        request: FeedbackRequest with query, doc_id, rating, etc.
    
    Returns:
        Success status and feedback ID
    """
    try:
        # Validate rating
        if request.rating not in [1, -1]:
            raise HTTPException(
                status_code=400,
                detail="Rating must be 1 (thumbs up) or -1 (thumbs down)"
            )
        
        # Save feedback to database
        feedback_id = save_feedback(
            query=request.query,
            doc_id=request.doc_id,
            doc_title=request.doc_title,
            search_type=request.search_type,
            rating=request.rating,
            result_position=request.result_position,
            search_log_id=request.search_log_id,
            session_id=request.session_id
        )
        
        return {
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Thank you for your feedback!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")


@app.get("/analytics")
async def get_analytics_data(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back")
):
    """
    Get search analytics and feedback statistics.
    
    Args:
        days: Number of days to look back (1-365)
    
    Returns:
        Analytics data including search stats, feedback, top queries, etc.
    """
    try:
        analytics = get_analytics(days=days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")


def build_bm25_query(query: str, top_k: int) -> Dict[str, Any]:
    """Build BM25 text search query."""
    return {
        "size": top_k,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "excerpt^2", "body_text"],
                "type": "best_fields",
                "tie_breaker": 0.3
            }
        },
        "_source": {
            "excludes": ["embedding"]
        }
    }


def build_semantic_query(query_embedding: List[float], top_k: int) -> Dict[str, Any]:
    """Build semantic (vector-only) search query using native knn."""
    return {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": top_k
                }
            }
        },
        "_source": {
            "excludes": ["embedding"]
        }
    }


def build_hybrid_query(query: str, query_embedding: List[float], top_k: int, 
                       bm25_weight: float, vector_weight: float) -> Dict[str, Any]:
    """Build hybrid search query combining BM25 and vector similarity.
    
    Note: OpenSearch doesn't natively support weighted hybrid search in a single query,
    so we use a bool query with should clauses for both BM25 and knn.
    """
    return {
        "size": top_k,
        "query": {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "excerpt^2", "body_text"],
                            "type": "best_fields",
                            "tie_breaker": 0.3,
                            "boost": bm25_weight
                        }
                    },
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding,
                                "k": top_k * 2,  # Get more candidates for better hybrid results
                                "boost": vector_weight
                            }
                        }
                    }
                ]
            }
        },
        "_source": {
            "excludes": ["embedding"]
        }
    }


def apply_sort(search_body: Dict[str, Any], sort_by: SortBy) -> Dict[str, Any]:
    """
    Apply sort clause to search query.
    
    Args:
        search_body: OpenSearch query body
        sort_by: Sort option
    
    Returns:
        Modified search body with sort clause
    """
    if sort_by == SortBy.RELEVANCE:
        # Default relevance sorting (by _score)
        return search_body
    
    # Add sort clause
    if sort_by == SortBy.DATE_DESC:
        search_body["sort"] = [{"published_at": {"order": "desc"}}, "_score"]
    elif sort_by == SortBy.DATE_ASC:
        search_body["sort"] = [{"published_at": {"order": "asc"}}, "_score"]
    elif sort_by == SortBy.TITLE_AZ:
        search_body["sort"] = [{"title.keyword": {"order": "asc"}}, "_score"]
    
    return search_body


def reciprocal_rank_fusion(bm25_results: List[Dict], semantic_results: List[Dict], 
                           k: int = 60, top_k: int = 10) -> List[SearchResult]:
    """
    Merge BM25 and semantic search results using Reciprocal Rank Fusion (RRF) algorithm.
    
    RRF Formula: score(doc) = sum over all ranking lists: 1/(k + rank_in_list)
    where k is a constant (typically 60) that reduces the impact of high rankings.
    
    Args:
        bm25_results: Results from BM25 search
        semantic_results: Results from semantic search
        k: RRF constant (default 60)
        top_k: Number of final results to return
    
    Returns:
        Merged and re-ranked results as SearchResult objects
    """
    rrf_scores = {}
    doc_data = {}
    
    # Process BM25 results
    for rank, hit in enumerate(bm25_results, 1):
        doc_id = hit['_source']['id']
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank)
        if doc_id not in doc_data:
            doc_data[doc_id] = hit['_source']
    
    # Process semantic results
    for rank, hit in enumerate(semantic_results, 1):
        doc_id = hit['_source']['id']
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank)
        if doc_id not in doc_data:
            doc_data[doc_id] = hit['_source']
    
    # Sort by RRF score (descending) and take top k
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # Build SearchResult objects
    results = []
    for doc_id, score in sorted_docs:
        source = doc_data[doc_id]
        results.append(SearchResult(
            id=source.get('id', doc_id),
            title=source.get('title'),
            excerpt=source.get('excerpt'),
            body_text=source.get('body_text'),
            tags=source.get('tags', []),
            published_at=source.get('published_at'),
            score=score
        ))
    
    return results


@app.post("/search", response_model=SearchResponse)
async def search_articles(request: SearchRequest):
    """
    Multi-mode search endpoint supporting BM25, semantic, and hybrid search.
    
    Args:
        request: SearchRequest with query, search_type, top_k, and weight parameters
    
    Returns:
        SearchResponse with matching articles
    """
    try:
        client = get_opensearch_client()
        processor = get_query_processor()
        
        # Check if index exists
        if not client.indices.exists(index=INDEX_NAME):
            raise HTTPException(
                status_code=404,
                detail=f"Index '{INDEX_NAME}' does not exist. Please run index_bm25.py first."
            )
        
        # Preprocess query
        original_query = request.query
        processed_query, was_corrected = processor.process(original_query)
        
        # Use processed query for search
        search_query = processed_query if processed_query else original_query
        
        # Build query based on search type
        if request.search_type == SearchType.BM25:
            # BM25 only - keyword-based search
            search_body = build_bm25_query(search_query, request.top_k)
            search_body = apply_sort(search_body, request.sort_by)
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
            
            # Log search
            search_log_id = log_search(
                query=original_query,
                processed_query=processed_query if was_corrected else None,
                search_type=request.search_type.value,
                sort_by=request.sort_by.value,
                total_results=response['hits']['total']['value'],
                results_returned=len(results),
                session_id=None  # Will be added from frontend
            )
            
            return SearchResponse(
                query=original_query,
                processed_query=processed_query if was_corrected else None,
                total_results=response['hits']['total']['value'],
                results=results,
                search_log_id=search_log_id
            )
            
        elif request.search_type == SearchType.SEMANTIC:
            # Semantic only - vector similarity search
            model = get_embedding_model()
            query_embedding = model.encode(search_query, show_progress_bar=False).tolist()
            search_body = build_semantic_query(query_embedding, request.top_k)
            search_body = apply_sort(search_body, request.sort_by)
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
            
            # Log search
            search_log_id = log_search(
                query=original_query,
                processed_query=processed_query if was_corrected else None,
                search_type=request.search_type.value,
                sort_by=request.sort_by.value,
                total_results=response['hits']['total']['value'],
                results_returned=len(results),
                session_id=None  # Will be added from frontend
            )
            
            return SearchResponse(
                query=original_query,
                processed_query=processed_query if was_corrected else None,
                total_results=response['hits']['total']['value'],
                results=results,
                search_log_id=search_log_id
            )
            
        elif request.search_type == SearchType.HYBRID:
            # Hybrid - combination of BM25 and vector search using bool query
            model = get_embedding_model()
            query_embedding = model.encode(search_query, show_progress_bar=False).tolist()
            
            # Normalize weights
            total_weight = request.bm25_weight + request.vector_weight
            if total_weight == 0:
                bm25_weight = 0.5
                vector_weight = 0.5
            else:
                bm25_weight = request.bm25_weight / total_weight
                vector_weight = request.vector_weight / total_weight
            
            search_body = build_hybrid_query(
                search_query, query_embedding, request.top_k,
                bm25_weight, vector_weight
            )
            search_body = apply_sort(search_body, request.sort_by)
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
            
            # Log search
            search_log_id = log_search(
                query=original_query,
                processed_query=processed_query if was_corrected else None,
                search_type=request.search_type.value,
                sort_by=request.sort_by.value,
                total_results=response['hits']['total']['value'],
                results_returned=len(results),
                session_id=None  # Will be added from frontend
            )
            
            return SearchResponse(
                query=original_query,
                processed_query=processed_query if was_corrected else None,
                total_results=response['hits']['total']['value'],
                results=results,
                search_log_id=search_log_id
            )
            
        else:  # SearchType.RRF
            # RRF - Reciprocal Rank Fusion combining BM25 and semantic results
            model = get_embedding_model()
            query_embedding = model.encode(search_query, show_progress_bar=False).tolist()
            
            # Execute BM25 search (get 2x results for better fusion)
            bm25_body = build_bm25_query(search_query, request.top_k * 2)
            bm25_body = apply_sort(bm25_body, request.sort_by)
            bm25_response = client.search(index=INDEX_NAME, body=bm25_body)
            
            # Execute semantic search (get 2x results for better fusion)
            semantic_body = build_semantic_query(query_embedding, request.top_k * 2)
            semantic_body = apply_sort(semantic_body, request.sort_by)
            semantic_response = client.search(index=INDEX_NAME, body=semantic_body)
            
            # Merge results using RRF
            results = reciprocal_rank_fusion(
                bm25_response['hits']['hits'],
                semantic_response['hits']['hits'],
                k=60,
                top_k=request.top_k
            )
            
            # Get total results (approximate - use max of both searches)
            total_results = max(
                bm25_response['hits']['total']['value'],
                semantic_response['hits']['total']['value']
            )
            
            # Log search
            search_log_id = log_search(
                query=original_query,
                processed_query=processed_query if was_corrected else None,
                search_type=request.search_type.value,
                sort_by=request.sort_by.value,
                total_results=total_results,
                results_returned=len(results),
                session_id=None  # Will be added from frontend
            )
            
            return SearchResponse(
                query=original_query,
                processed_query=processed_query if was_corrected else None,
                total_results=total_results,
                results=results,
                search_log_id=search_log_id
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/search", response_model=SearchResponse)
async def search_articles_get(
    q: str = Query(..., description="Search query"),
    search_type: SearchType = Query(SearchType.HYBRID, description="Search type: bm25, semantic, or hybrid"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    bm25_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for BM25 search (0-1, used in hybrid mode)"),
    vector_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for vector search (0-1, used in hybrid mode)")
):
    """
    GET endpoint for multi-mode search (convenience endpoint).
    
    Args:
        q: Search query string
        search_type: Type of search - bm25, semantic, or hybrid
        top_k: Number of results to return
        bm25_weight: Weight for BM25 search (0-1, only used in hybrid mode)
        vector_weight: Weight for vector search (0-1, only used in hybrid mode)
    
    Returns:
        SearchResponse with matching articles
    """
    request = SearchRequest(
        query=q,
        search_type=search_type,
        top_k=top_k,
        bm25_weight=bm25_weight,
        vector_weight=vector_weight
    )
    return await search_articles(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

