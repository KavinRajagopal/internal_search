#!/usr/bin/env python3
"""
Analytics Dashboard for Article Search System.
Displays search statistics, user feedback, and performance metrics.
"""

import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuration
API_URL = "http://localhost:8000"
ANALYTICS_ENDPOINT = f"{API_URL}/analytics"
HEALTH_ENDPOINT = f"{API_URL}/health"

# Page configuration
st.set_page_config(
    page_title="Search Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        background-color: #f9f9f9;
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


def fetch_analytics(days: int = 7) -> Dict[str, Any]:
    """
    Fetch analytics data from the API.
    
    Args:
        days: Number of days to look back
    
    Returns:
        Analytics data dictionary
    """
    try:
        response = requests.get(ANALYTICS_ENDPOINT, params={"days": days}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching analytics: {str(e)}")
        return None


def display_overview_metrics(overview: Dict[str, Any]):
    """Display overview metrics in a grid."""
    st.markdown("### 📈 Overview (Last 7 Days)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_searches = overview.get('total_searches') or 0
        total_searches = int(total_searches) if total_searches is not None else 0
        st.metric("Total Searches", f"{total_searches:,}")
    
    with col2:
        unique_queries = overview.get('unique_queries') or 0
        unique_queries = int(unique_queries) if unique_queries is not None else 0
        st.metric("Unique Queries", f"{unique_queries:,}")
    
    with col3:
        total_feedback = overview.get('total_feedback') or 0
        total_feedback = int(total_feedback) if total_feedback is not None else 0
        st.metric("Total Feedback", f"{total_feedback:,}")
    
    with col4:
        satisfaction_rate = overview.get('satisfaction_rate') or 0
        satisfaction_rate = float(satisfaction_rate) if satisfaction_rate is not None else 0.0
        st.metric("Satisfaction Rate", f"{satisfaction_rate:.1f}%")
    
    # Additional metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_results = overview.get('avg_results') or 0
        avg_results = float(avg_results) if avg_results is not None else 0.0
        st.metric("Avg Results per Search", f"{avg_results:.1f}")
    
    with col2:
        positive_feedback = overview.get('positive_feedback') or 0
        positive_feedback = int(positive_feedback) if positive_feedback is not None else 0
        st.metric("👍 Positive Feedback", f"{positive_feedback:,}")
    
    with col3:
        negative_feedback = overview.get('negative_feedback') or 0
        negative_feedback = int(negative_feedback) if negative_feedback is not None else 0
        st.metric("👎 Negative Feedback", f"{negative_feedback:,}")
    
    with col4:
        avg_returned = overview.get('avg_returned') or 0
        avg_returned = float(avg_returned) if avg_returned is not None else 0.0
        st.metric("Avg Returned Results", f"{avg_returned:.1f}")


def display_search_statistics(analytics: Dict[str, Any]):
    """Display search statistics with charts."""
    st.markdown("### 🔍 Search Statistics")
    
    col1, col2 = st.columns(2)
    
    # Top queries
    with col1:
        st.markdown("#### Top 10 Queries")
        top_queries = analytics.get('top_queries', [])
        if top_queries:
            df = pd.DataFrame(top_queries)
            st.dataframe(
                df,
                column_config={
                    "query": st.column_config.TextColumn("Query", width="large"),
                    "count": st.column_config.NumberColumn("Searches", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No search data available yet")
    
    # Search type distribution
    with col2:
        st.markdown("#### Search Type Distribution")
        search_type_stats = analytics.get('search_type_stats', {})
        if search_type_stats:
            df_search_types = pd.DataFrame([
                {"Search Type": k.upper(), "Count": v}
                for k, v in search_type_stats.items()
            ])
            
            fig = px.pie(
                df_search_types,
                values='Count',
                names='Search Type',
                title='',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=True, height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No search type data available yet")
    
    # Searches over time
    st.markdown("#### 📅 Searches Over Time")
    searches_by_day = analytics.get('searches_by_day', [])
    if searches_by_day:
        df_time = pd.DataFrame(searches_by_day)
        df_time['date'] = pd.to_datetime(df_time['date'])
        
        fig = px.line(
            df_time,
            x='date',
            y='count',
            title='',
            markers=True,
            labels={'date': 'Date', 'count': 'Number of Searches'}
        )
        fig.update_traces(line_color='#1f77b4', marker_color='#1f77b4')
        fig.update_layout(
            height=300,
            xaxis_title='Date',
            yaxis_title='Searches',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No time series data available yet")


def display_feedback_analysis(analytics: Dict[str, Any]):
    """Display feedback analysis with charts."""
    st.markdown("### 💬 Feedback Analysis")
    
    # Feedback by search type
    st.markdown("#### Feedback by Search Type")
    feedback_by_type = analytics.get('feedback_by_search_type', {})
    if feedback_by_type:
        feedback_data = []
        for search_type, stats in feedback_by_type.items():
            feedback_data.append({
                "Search Type": search_type.upper(),
                "Positive": stats.get('positive', 0),
                "Negative": stats.get('negative', 0),
                "Total": stats.get('total', 0)
            })
        
        df_feedback = pd.DataFrame(feedback_data)
        
        fig = go.Figure(data=[
            go.Bar(name='Positive 👍', x=df_feedback['Search Type'], y=df_feedback['Positive'], marker_color='#28a745'),
            go.Bar(name='Negative 👎', x=df_feedback['Search Type'], y=df_feedback['Negative'], marker_color='#dc3545')
        ])
        fig.update_layout(
            barmode='group',
            xaxis_title='Search Type',
            yaxis_title='Feedback Count',
            height=350,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No feedback by search type available yet")
    
    col1, col2 = st.columns(2)
    
    # Most helpful articles
    with col1:
        st.markdown("#### 🌟 Most Helpful Articles")
        most_helpful = analytics.get('most_helpful_articles', [])
        if most_helpful:
            df_helpful = pd.DataFrame(most_helpful)
            df_helpful = df_helpful.rename(columns={
                'doc_title': 'Article Title',
                'net_rating': 'Net Rating',
                'feedback_count': 'Feedback Count'
            })
            st.dataframe(
                df_helpful[['Article Title', 'Net Rating', 'Feedback Count']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No helpful articles data yet")
    
    # Least helpful articles
    with col2:
        st.markdown("#### ⚠️ Least Helpful Articles")
        least_helpful = analytics.get('least_helpful_articles', [])
        if least_helpful:
            df_unhelpful = pd.DataFrame(least_helpful)
            df_unhelpful = df_unhelpful.rename(columns={
                'doc_title': 'Article Title',
                'net_rating': 'Net Rating',
                'feedback_count': 'Feedback Count'
            })
            st.dataframe(
                df_unhelpful[['Article Title', 'Net Rating', 'Feedback Count']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No problematic articles data yet")


def display_problem_areas(analytics: Dict[str, Any]):
    """Display problem areas and areas needing attention."""
    st.markdown("### 🚨 Problem Areas")
    
    # Zero result queries
    st.markdown("#### Zero-Result Queries")
    zero_result_queries = analytics.get('zero_result_queries', [])
    if zero_result_queries:
        df_zero = pd.DataFrame(zero_result_queries)
        st.dataframe(
            df_zero,
            column_config={
                "query": st.column_config.TextColumn("Query", width="large"),
                "count": st.column_config.NumberColumn("Occurrences", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )
        st.warning(f"⚠️ {len(zero_result_queries)} queries returned no results. Consider expanding your content or improving query handling.")
    else:
        st.success("✅ No zero-result queries in this period!")


def display_recent_activity(analytics: Dict[str, Any]):
    """Display recent searches and feedback."""
    st.markdown("### 🕐 Recent Activity")
    
    col1, col2 = st.columns(2)
    
    # Recent searches
    with col1:
        st.markdown("#### Recent Searches (Last 20)")
        recent_searches = analytics.get('recent_searches', [])
        if recent_searches:
            df_searches = pd.DataFrame(recent_searches)
            df_searches['timestamp'] = pd.to_datetime(df_searches['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            df_searches = df_searches.rename(columns={
                'query': 'Query',
                'search_type': 'Type',
                'total_results': 'Results',
                'timestamp': 'Time'
            })
            st.dataframe(
                df_searches[['Query', 'Type', 'Results', 'Time']],
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No recent searches yet")
    
    # Recent feedback
    with col2:
        st.markdown("#### Recent Feedback (Last 20)")
        recent_feedback = analytics.get('recent_feedback', [])
        if recent_feedback:
            df_feedback = pd.DataFrame(recent_feedback)
            df_feedback['timestamp'] = pd.to_datetime(df_feedback['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            df_feedback['rating_icon'] = df_feedback['rating'].apply(lambda x: '👍' if x > 0 else '👎')
            df_feedback = df_feedback.rename(columns={
                'query': 'Query',
                'doc_title': 'Article',
                'rating_icon': 'Rating',
                'result_position': 'Position',
                'timestamp': 'Time'
            })
            st.dataframe(
                df_feedback[['Query', 'Article', 'Rating', 'Position', 'Time']],
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No recent feedback yet")


def main():
    """Main dashboard application."""
    
    # Header
    st.markdown('<div class="main-header">📊 Search Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Monitor search performance, user feedback, and system insights</div>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Cannot connect to the FastAPI backend. Please ensure it's running on http://localhost:8000")
        st.info("Start the API with: `uvicorn app.api:app --host 0.0.0.0 --port 8000`")
        st.stop()
    
    # Sidebar for date range
    with st.sidebar:
        st.header("⚙️ Dashboard Settings")
        
        days = st.slider(
            "Data Range (Days)",
            min_value=1,
            max_value=30,
            value=7,
            help="Select how many days of data to analyze"
        )
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📖 Quick Links")
        st.markdown("- [Search Frontend](http://localhost:8501)")
        st.markdown("- [API Docs](http://localhost:8000/docs)")
        st.markdown("- [Health Check](http://localhost:8000/health)")
    
    # Fetch analytics data
    with st.spinner("Loading analytics data..."):
        analytics = fetch_analytics(days)
    
    if not analytics:
        st.error("Failed to load analytics data. Please check the API connection.")
        st.stop()
    
    # Display sections
    overview = analytics.get('overview', {})
    
    # Overview metrics
    display_overview_metrics(overview)
    
    st.markdown("---")
    
    # Search statistics
    display_search_statistics(analytics)
    
    st.markdown("---")
    
    # Feedback analysis
    display_feedback_analysis(analytics)
    
    st.markdown("---")
    
    # Problem areas
    display_problem_areas(analytics)
    
    st.markdown("---")
    
    # Recent activity
    display_recent_activity(analytics)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
        Showing data from last {days} days | 
        Auto-refresh available
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

