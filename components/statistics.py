"""
Statistics view component - displays listening analytics.
"""

import streamlit as st
from typing import Dict, Any
from api.audiobookshelf import AudiobookshelfAPI
from utils.helpers import (
    get_monthly_completion_counts,
    get_yearly_completion_counts,
    calculate_completion_stats
)
import pandas as pd
from datetime import datetime


def render_statistics_view(api: AudiobookshelfAPI):
    """
    Render the statistics view with charts and metrics.
    
    Args:
        api: Audiobookshelf API client
    """
    st.markdown("### 📊 Statistics")
    
    # Fetch data
    with st.spinner("Loading statistics..."):
        sessions = api.get_user_listening_sessions()
        listening_stats = api.get_user_listening_stats()
        progress_map = api.get_media_progress_map()

    if not sessions and not listening_stats:
        st.info("No listening data available yet. Start listening to build your statistics!")
        return
    
    # Custom CSS for stats cards
    st.markdown("""
        <style>
        .stat-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: 700;
            color: #4a9eff;
            margin-bottom: 4px;
        }
        
        .stat-label {
            font-size: 14px;
            color: #a8a8a8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .chart-title {
            font-size: 18px;
            font-weight: 600;
            color: #e8e8e8;
            margin-bottom: 16px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Calculate statistics from sessions (for charts)
    completion_stats = calculate_completion_stats(sessions)
    monthly_counts = get_monthly_completion_counts(sessions)
    yearly_counts = get_yearly_completion_counts(sessions)

    # Use server data for overview stats
    if listening_stats:
        total_time_hours = listening_stats.get('totalTime', 0) / 3600
    else:
        total_time_hours = completion_stats['total_time_hours']

    # Count finished books from /me mediaProgress (reliable source)
    books_finished = sum(1 for p in progress_map.values() if p.get('isFinished'))

    # Overall Stats Row
    st.markdown("#### Overview")
    cols = st.columns(3)

    with cols[0]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{books_finished}</div>
                <div class="stat-label">Books Completed</div>
            </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        hours = int(total_time_hours)
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{hours}</div>
                <div class="stat-label">Hours Listened</div>
            </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        # Calculate average per month
        if monthly_counts:
            avg_per_month = books_finished / len(monthly_counts)
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{avg_per_month:.1f}</div>
                    <div class="stat-label">Avg Books/Month</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">-</div>
                    <div class="stat-label">Avg Books/Month</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Yearly completion chart
    if yearly_counts:
        st.markdown("#### Books Completed Per Year")
        
        # Prepare data for chart
        yearly_df = pd.DataFrame([
            {"Year": year, "Books": count}
            for year, count in sorted(yearly_counts.items())
        ])
        
        # Display bar chart
        st.bar_chart(yearly_df.set_index("Year")["Books"], use_container_width=True)
        
        # Display table
        with st.expander("View Details"):
            st.dataframe(
                yearly_df.set_index("Year"),
                use_container_width=True
            )
    
    st.markdown("---")
    
    # Monthly completion chart
    if monthly_counts:
        st.markdown("#### Books Completed Per Month")
        
        # Prepare data for chart
        monthly_df = pd.DataFrame([
            {"Month": month, "Books": count}
            for month, count in sorted(monthly_counts.items())
        ])
        
        # Format month labels
        monthly_df['Month_Label'] = monthly_df['Month'].apply(
            lambda x: datetime.strptime(x, "%Y-%m").strftime("%b %Y")
        )
        
        # Display line chart
        st.line_chart(monthly_df.set_index("Month_Label")["Books"], use_container_width=True)
        
        # Display table
        with st.expander("View Details"):
            display_df = monthly_df[['Month_Label', 'Books']].rename(
                columns={'Month_Label': 'Month'}
            )
            st.dataframe(
                display_df.set_index("Month"),
                use_container_width=True
            )
    
    # Additional insights
    if listening_stats:
        st.markdown("---")
        st.markdown("#### Additional Insights")

        items_stats = listening_stats.get('items', {})
        total_items = len(items_stats) if isinstance(items_stats, dict) else 0
        unique_authors: set[str] = set()
        if isinstance(items_stats, dict):
            for item in items_stats.values():
                for author in item.get('mediaMetadata', {}).get('authors', []):
                    name = author.get('name')
                    if name:
                        unique_authors.add(name)

        cols = st.columns(2)

        with cols[0]:
            st.metric("Books Listened To", total_items)

        with cols[1]:
            st.metric("Unique Authors", len(unique_authors))
    
    # Footer
    st.markdown("---")
    st.caption("Statistics update automatically as you listen")
