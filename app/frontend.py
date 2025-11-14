#!/usr/bin/env python3
"""
Streamlit frontend for Article Search System.
Provides a user-friendly interface for BM25, Semantic, and Hybrid search.
"""

import streamlit as st
import requests
from typing import Dict, List, Any
import json

# Configuration
API_URL = "http://localhost:8000"
SEARCH_ENDPOINT = f"{API_URL}/search"
HEALTH_ENDPOINT = f"{API_URL}/health"

# Page configuration
st.set_page_config(
    page_title="Article Search System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .result-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .result-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .result-meta {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .result-score {
        font-size: 0.9rem;
        font-weight: bold;
        color: #28a745;
    }
    .search-info {
        padding: 1rem;
        background-color: #e7f3ff;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=2)
        return response.status_code == 200
    except:
        return False


def perform_search(query: str, search_type: str, top_k: int, sort_by: str = "relevance") -> Dict[str, Any]:
    """
    Perform search via the FastAPI backend.
    
    Args:
        query: Search query string
        search_type: One of 'bm25', 'semantic', 'hybrid', 'rrf'
        top_k: Number of results to return
        sort_by: Sort option
    
    Returns:
        API response as dictionary
    """
    payload = {
        "query": query,
        "search_type": search_type.lower(),
        "top_k": top_k,
        "bm25_weight": 0.5,
        "vector_weight": 0.5,
        "sort_by": sort_by.lower()
    }
    
    try:
        response = requests.post(SEARCH_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None


def get_suggestions(query_prefix: str, limit: int = 5) -> List[str]:
    """
    Get search suggestions from the API.
    
    Args:
        query_prefix: Query prefix to get suggestions for
        limit: Maximum number of suggestions
    
    Returns:
        List of suggestions
    """
    if not query_prefix or len(query_prefix) < 2:
        return []
    
    try:
        response = requests.get(
            f"{API_URL}/suggestions",
            params={"q": query_prefix, "limit": limit},
            timeout=2
        )
        if response.ok:
            return response.json()
    except:
        pass
    return []


def display_result(result: Dict[str, Any], index: int):
    """Display a single search result."""
    with st.container():
        # Title
        st.markdown(f"### {index}. {result.get('title', 'Untitled')}")
        
        # Metadata
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            published = result.get('published_at', 'N/A')
            st.markdown(f"📅 **Published:** {published}")
        with col2:
            tags = result.get('tags', [])
            if tags:
                tags_str = ", ".join(tags)
                st.markdown(f"🏷️ **Tags:** {tags_str}")
        with col3:
            score = result.get('score', 0)
            st.markdown(f"⭐ **Score:** {score:.4f}")
        
        # Content
        excerpt = result.get('excerpt', '') or result.get('body_text', '')
        if excerpt:
            # Limit excerpt length for display
            max_length = 500
            if len(excerpt) > max_length:
                excerpt = excerpt[:max_length] + "..."
            
            with st.expander("📄 View Article Content"):
                st.markdown(excerpt)
        
        st.markdown("---")


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">🔍 Article Search System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Hybrid BM25 + Vector Search powered by OpenSearch</div>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Cannot connect to the FastAPI backend. Please ensure it's running on http://localhost:8000")
        st.info("Start the API with: `uvicorn app.api:app --host 0.0.0.0 --port 8000`")
        st.stop()
    
    st.success("✅ Connected to API backend")
    
    # Sidebar for search configuration
    with st.sidebar:
        st.header("⚙️ Search Configuration")
        
        # Search type selection
        search_type = st.radio(
            "Search Type",
            ["BM25", "Semantic", "Hybrid", "RRF"],
            index=2,  # Default to Hybrid
            help="""
            - **BM25**: Keyword-based text search (classic search)
            - **Semantic**: Vector similarity search using embeddings
            - **Hybrid**: Combined BM25 + semantic with bool query
            - **RRF**: Reciprocal Rank Fusion (advanced hybrid algorithm)
            """
        )
        
        # Number of results
        top_k = st.number_input(
            "Number of Results",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum number of results to display"
        )
        
        # Sort by selection
        sort_by = st.selectbox(
            "Sort Results By",
            ["Relevance", "Newest First", "Oldest First", "Title A-Z"],
            help="Choose how to sort search results"
        )
        
        # Map display names to API values
        sort_map = {
            "Relevance": "relevance",
            "Newest First": "date_desc",
            "Oldest First": "date_asc",
            "Title A-Z": "title_az"
        }
        sort_by_value = sort_map[sort_by]
        
        # Search type info
        st.markdown("---")
        st.markdown("### 📊 Search Type Info")
        if search_type == "BM25":
            st.info("**BM25** uses traditional keyword matching with TF-IDF scoring. Best for exact term matches.")
        elif search_type == "Semantic":
            st.info("**Semantic** uses AI embeddings to find conceptually similar articles, even if they use different words.")
        elif search_type == "Hybrid":
            st.info("**Hybrid** combines both BM25 and semantic search using bool query with 50/50 weights.")
        else:  # RRF
            st.info("**RRF** uses Reciprocal Rank Fusion algorithm to intelligently merge BM25 and semantic results for optimal ranking.")
    
    # Main search interface
    st.markdown("### 🔎 Enter Your Search Query")
    
    # Initialize query in session state if not present
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    # Search input (using session state for dynamic updates)
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(
            "Search Query",
            value=st.session_state.search_query,
            placeholder="e.g., healthcare policy, climate change, immigration reform...",
            label_visibility="collapsed",
            key="query_input"
        )
        # Update session state when user types
        st.session_state.search_query = query
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Show suggestions if query is long enough
    if query and len(query) >= 2 and not search_button:
        suggestions = get_suggestions(query, limit=5)
        if suggestions:
            st.markdown("**💡 Suggestions:**")
            cols = st.columns(min(len(suggestions), 3))
            for idx, suggestion in enumerate(suggestions[:3]):
                with cols[idx]:
                    # Truncate long titles for display
                    display_title = suggestion if len(suggestion) <= 40 else suggestion[:37] + "..."
                    if st.button(f"🔍 {display_title}", key=f"sug_{idx}", use_container_width=True):
                        # Update session state and trigger search
                        st.session_state.search_query = suggestion
                        st.session_state.trigger_search = True
                        st.rerun()
    
    # Check if search should be triggered
    trigger_search = search_button or st.session_state.get('trigger_search', False)
    
    # Reset trigger flag
    if st.session_state.get('trigger_search', False):
        st.session_state.trigger_search = False
    
    # Perform search
    if trigger_search or (query and 'last_query' in st.session_state and st.session_state.last_query != query):
        if not query or query.strip() == "":
            st.warning("⚠️ Please enter a search query")
        else:
            st.session_state.last_query = query
            
            with st.spinner(f"Searching with {search_type} mode..."):
                results = perform_search(query, search_type, top_k, sort_by_value)
            
            if results:
                # Show preprocessing feedback if query was corrected
                if results.get('processed_query') and results.get('processed_query') != results.get('query'):
                    st.info(f"🔍 **Searched for:** {results.get('processed_query')} (corrected from: {results.get('query')})")
                
                # Display search info
                total_results = results.get('total_results', 0)
                returned_results = len(results.get('results', []))
                
                st.markdown("---")
                st.markdown(f"### 📊 Search Results")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Matches", f"{total_results:,}")
                with col2:
                    st.metric("Showing Results", returned_results)
                with col3:
                    st.metric("Search Type", search_type)
                with col4:
                    st.metric("Sort By", sort_by)
                
                st.markdown("---")
                
                # Display results
                if returned_results > 0:
                    for idx, result in enumerate(results['results'], 1):
                        display_result(result, idx)
                else:
                    st.info("No results found. Try a different query or search type.")
    
    # Initial state message
    elif not query:
        st.info("👆 Enter a search query above and click Search to find articles")
        
        # Example queries
        st.markdown("### 💡 Example Queries")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏥 Healthcare Policy"):
                st.session_state.example_query = "healthcare policy"
                st.rerun()
        with col2:
            if st.button("🌍 Climate Change"):
                st.session_state.example_query = "climate change"
                st.rerun()
        with col3:
            if st.button("🗳️ Election News"):
                st.session_state.example_query = "election news"
                st.rerun()
        
        # Set example query if button was clicked
        if 'example_query' in st.session_state:
            query = st.session_state.example_query
            del st.session_state.example_query
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        Built with Streamlit | Powered by OpenSearch & FastAPI | Using all-MiniLM-L6-v2 embeddings
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

