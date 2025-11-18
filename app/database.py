#!/usr/bin/env python3
"""
Database module for storing search logs and user feedback.
Uses SQLite for simplicity and portability.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path


# Database file location
DB_PATH = Path(__file__).parent.parent / "feedback.db"


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_database():
    """
    Initialize database with required tables.
    Creates tables if they don't exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create search_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            processed_query TEXT,
            search_type TEXT NOT NULL,
            sort_by TEXT,
            total_results INTEGER,
            results_returned INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT
        )
    """)
    
    # Create feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_log_id INTEGER,
            query TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            doc_title TEXT,
            search_type TEXT NOT NULL,
            rating INTEGER NOT NULL,
            result_position INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            FOREIGN KEY (search_log_id) REFERENCES search_logs(id)
        )
    """)
    
    # Create indices for better query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_search_logs_timestamp 
        ON search_logs(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_search_logs_query 
        ON search_logs(query)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_timestamp 
        ON feedback(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_rating 
        ON feedback(rating)
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")


def log_search(
    query: str,
    processed_query: Optional[str],
    search_type: str,
    sort_by: str,
    total_results: int,
    results_returned: int,
    session_id: Optional[str] = None
) -> int:
    """
    Log a search query to the database.
    
    Args:
        query: Original search query
        processed_query: Processed/corrected query
        search_type: Type of search (bm25, semantic, hybrid, rrf)
        sort_by: Sort option used
        total_results: Total number of matching results
        results_returned: Number of results returned
        session_id: User session identifier
    
    Returns:
        ID of the created search log entry
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO search_logs 
        (query, processed_query, search_type, sort_by, total_results, results_returned, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (query, processed_query, search_type, sort_by, total_results, results_returned, session_id))
    
    search_log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return search_log_id


def save_feedback(
    query: str,
    doc_id: str,
    doc_title: Optional[str],
    search_type: str,
    rating: int,
    result_position: int,
    search_log_id: Optional[int] = None,
    session_id: Optional[str] = None
) -> int:
    """
    Save user feedback on a search result.
    
    Args:
        query: Search query that produced this result
        doc_id: Document ID that was rated
        doc_title: Document title
        search_type: Type of search used
        rating: 1 for thumbs up, -1 for thumbs down
        result_position: Position of result in search results (1-based)
        search_log_id: Related search log entry ID
        session_id: User session identifier
    
    Returns:
        ID of the created feedback entry
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO feedback 
        (search_log_id, query, doc_id, doc_title, search_type, rating, result_position, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (search_log_id, query, doc_id, doc_title, search_type, rating, result_position, session_id))
    
    feedback_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return feedback_id


def get_analytics(days: int = 7) -> Dict[str, Any]:
    """
    Get comprehensive analytics data.
    
    Args:
        days: Number of days to look back
    
    Returns:
        Dictionary with analytics data
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calculate date threshold
    date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
    
    # Overview metrics
    cursor.execute("""
        SELECT COUNT(*) as total_searches,
               COUNT(DISTINCT query) as unique_queries,
               AVG(total_results) as avg_results,
               AVG(results_returned) as avg_returned
        FROM search_logs
        WHERE timestamp >= ?
    """, (date_threshold,))
    overview = dict(cursor.fetchone())
    
    # Total feedback
    cursor.execute("""
        SELECT COUNT(*) as total_feedback,
               SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) as positive_feedback,
               SUM(CASE WHEN rating < 0 THEN 1 ELSE 0 END) as negative_feedback
        FROM feedback
        WHERE timestamp >= ?
    """, (date_threshold,))
    feedback_stats = dict(cursor.fetchone())
    overview.update(feedback_stats)
    
    # Calculate satisfaction rate
    if overview['total_feedback'] > 0:
        overview['satisfaction_rate'] = (overview['positive_feedback'] / overview['total_feedback']) * 100
    else:
        overview['satisfaction_rate'] = 0.0
    
    # Top queries
    cursor.execute("""
        SELECT query, COUNT(*) as count
        FROM search_logs
        WHERE timestamp >= ?
        GROUP BY query
        ORDER BY count DESC
        LIMIT 10
    """, (date_threshold,))
    top_queries = [dict(row) for row in cursor.fetchall()]
    
    # Zero result queries
    cursor.execute("""
        SELECT query, COUNT(*) as count
        FROM search_logs
        WHERE timestamp >= ? AND total_results = 0
        GROUP BY query
        ORDER BY count DESC
        LIMIT 10
    """, (date_threshold,))
    zero_result_queries = [dict(row) for row in cursor.fetchall()]
    
    # Search type distribution
    cursor.execute("""
        SELECT search_type, COUNT(*) as count
        FROM search_logs
        WHERE timestamp >= ?
        GROUP BY search_type
        ORDER BY count DESC
    """, (date_threshold,))
    search_type_stats = {row['search_type']: row['count'] for row in cursor.fetchall()}
    
    # Feedback by search type
    cursor.execute("""
        SELECT search_type,
               COUNT(*) as total,
               SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) as positive,
               SUM(CASE WHEN rating < 0 THEN 1 ELSE 0 END) as negative
        FROM feedback
        WHERE timestamp >= ?
        GROUP BY search_type
    """, (date_threshold,))
    feedback_by_search_type = {row['search_type']: dict(row) for row in cursor.fetchall()}
    
    # Recent searches
    cursor.execute("""
        SELECT id, query, search_type, total_results, timestamp
        FROM search_logs
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT 20
    """, (date_threshold,))
    recent_searches = [dict(row) for row in cursor.fetchall()]
    
    # Most helpful articles
    cursor.execute("""
        SELECT doc_title, doc_id, 
               SUM(rating) as net_rating,
               COUNT(*) as feedback_count
        FROM feedback
        WHERE timestamp >= ? AND doc_title IS NOT NULL
        GROUP BY doc_id
        HAVING SUM(rating) > 0
        ORDER BY net_rating DESC, feedback_count DESC
        LIMIT 10
    """, (date_threshold,))
    most_helpful_articles = [dict(row) for row in cursor.fetchall()]
    
    # Least helpful articles
    cursor.execute("""
        SELECT doc_title, doc_id,
               SUM(rating) as net_rating,
               COUNT(*) as feedback_count
        FROM feedback
        WHERE timestamp >= ? AND doc_title IS NOT NULL
        GROUP BY doc_id
        HAVING SUM(rating) < 0
        ORDER BY net_rating ASC, feedback_count DESC
        LIMIT 10
    """, (date_threshold,))
    least_helpful_articles = [dict(row) for row in cursor.fetchall()]
    
    # Recent feedback
    cursor.execute("""
        SELECT query, doc_title, rating, result_position, timestamp
        FROM feedback
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT 20
    """, (date_threshold,))
    recent_feedback = [dict(row) for row in cursor.fetchall()]
    
    # Searches by day (for time series)
    cursor.execute("""
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM search_logs
        WHERE timestamp >= ?
        GROUP BY DATE(timestamp)
        ORDER BY date ASC
    """, (date_threshold,))
    searches_by_day = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "overview": overview,
        "top_queries": top_queries,
        "zero_result_queries": zero_result_queries,
        "search_type_stats": search_type_stats,
        "feedback_by_search_type": feedback_by_search_type,
        "recent_searches": recent_searches,
        "most_helpful_articles": most_helpful_articles,
        "least_helpful_articles": least_helpful_articles,
        "recent_feedback": recent_feedback,
        "searches_by_day": searches_by_day
    }


# Initialize database on module import
try:
    init_database()
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")

