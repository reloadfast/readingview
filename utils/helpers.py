"""
Utility functions for the Shelf application.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import streamlit as st
from collections import defaultdict


def format_date(timestamp: Optional[int]) -> str:
    """
    Format Unix timestamp to readable date.
    
    Args:
        timestamp: Unix timestamp in milliseconds
        
    Returns:
        Formatted date string
    """
    if not timestamp:
        return "Unknown"
    
    try:
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return "Unknown"


def format_date_short(timestamp: Optional[int]) -> str:
    """
    Format Unix timestamp to short date format.
    
    Args:
        timestamp: Unix timestamp in milliseconds
        
    Returns:
        Short formatted date string
    """
    if not timestamp:
        return "Unknown"
    
    try:
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return "Unknown"


def group_sessions_by_month(sessions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group listening sessions by month.
    
    Args:
        sessions: List of session objects
        
    Returns:
        Dictionary with month keys and session lists
    """
    grouped = defaultdict(list)
    
    for session in sessions:
        timestamp = session.get('updatedAt') or session.get('startedAt')
        if timestamp:
            dt = datetime.fromtimestamp(timestamp / 1000)
            month_key = dt.strftime("%Y-%m")
            grouped[month_key].append(session)
    
    return dict(grouped)


def calculate_completion_stats(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate completion statistics from listening sessions.
    
    Args:
        sessions: List of session objects
        
    Returns:
        Statistics dictionary
    """
    completed_books = set()
    total_time = 0
    
    for session in sessions:
        if session.get('mediaProgress', {}).get('isFinished'):
            completed_books.add(session.get('libraryItemId'))
        total_time += session.get('timeListening', 0)
    
    return {
        'total_completed': len(completed_books),
        'total_time_seconds': total_time,
        'total_time_hours': total_time / 3600
    }


def get_monthly_completion_counts(sessions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get count of completed books per month.
    
    Args:
        sessions: List of session objects
        
    Returns:
        Dictionary with month keys and completion counts
    """
    monthly_counts = defaultdict(int)
    completed_books_by_month = defaultdict(set)
    
    for session in sessions:
        if session.get('mediaProgress', {}).get('isFinished'):
            timestamp = session.get('finishedAt') or session.get('updatedAt')
            if timestamp:
                dt = datetime.fromtimestamp(timestamp / 1000)
                month_key = dt.strftime("%Y-%m")
                book_id = session.get('libraryItemId')
                completed_books_by_month[month_key].add(book_id)
    
    # Convert sets to counts
    for month, books in completed_books_by_month.items():
        monthly_counts[month] = len(books)
    
    return dict(monthly_counts)


def get_yearly_completion_counts(sessions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get count of completed books per year.
    
    Args:
        sessions: List of session objects
        
    Returns:
        Dictionary with year keys and completion counts
    """
    yearly_counts = defaultdict(int)
    completed_books_by_year = defaultdict(set)
    
    for session in sessions:
        if session.get('mediaProgress', {}).get('isFinished'):
            timestamp = session.get('finishedAt') or session.get('updatedAt')
            if timestamp:
                dt = datetime.fromtimestamp(timestamp / 1000)
                year_key = str(dt.year)
                book_id = session.get('libraryItemId')
                completed_books_by_year[year_key].add(book_id)
    
    # Convert sets to counts
    for year, books in completed_books_by_year.items():
        yearly_counts[year] = len(books)
    
    return dict(yearly_counts)


@st.cache_data(ttl=300)
def cached_api_call(func, *args, **kwargs):
    """
    Cache API calls to reduce load on Audiobookshelf server.
    
    Args:
        func: Function to cache
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    return func(*args, **kwargs)


def display_error(message: str, details: Optional[str] = None):
    """
    Display a formatted error message.
    
    Args:
        message: Main error message
        details: Optional additional details
    """
    st.error(message)
    if details:
        with st.expander("Error Details"):
            st.code(details)


def display_info(message: str):
    """
    Display a formatted info message.
    
    Args:
        message: Info message
    """
    st.info(message)
