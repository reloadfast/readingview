"""
Utility functions for the Shelf application.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import streamlit as st
from collections import defaultdict


def sanitize_url(url: Optional[str]) -> Optional[str]:
    """
    Sanitize a user-supplied URL for safe storage and rendering.

    Returns the cleaned URL if it uses http/https, or None otherwise.
    """
    if not url or not url.strip():
        return None
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    # Escape double-quotes to prevent HTML attribute injection
    # (used in unsafe_allow_html <a href="..."> contexts)
    url = url.replace('"', "%22")
    return url


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


def get_finished_books(
    progress_map: Dict[str, Dict[str, Any]],
    stats_items: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build list of finished books with metadata.

    Joins mediaProgress (from /api/me) with listening-stats items
    (from /api/me/listening-stats) to get both completion dates and
    book metadata.

    Args:
        progress_map: Dict mapping libraryItemId to progress data
        stats_items: The 'items' dict from listening-stats endpoint

    Returns:
        List of finished book dicts sorted by finishedAt ascending
    """
    finished: List[Dict[str, Any]] = []

    for lib_item_id, progress in progress_map.items():
        if not progress.get('isFinished'):
            continue

        stats_item = stats_items.get(lib_item_id, {})
        metadata = stats_item.get('mediaMetadata', {})

        authors = metadata.get('authors', [])
        author_str = ', '.join(a.get('name', '') for a in authors) if authors else 'Unknown Author'

        finished.append({
            'library_item_id': lib_item_id,
            'title': metadata.get('title', 'Unknown Title'),
            'author': author_str,
            'series': metadata.get('series', []),
            'narrator': ', '.join(metadata.get('narrators', [])),
            'finished_at': progress.get('finishedAt'),
            'started_at': progress.get('startedAt'),
            'duration': progress.get('duration', 0),
            'time_listening': stats_item.get('timeListening', 0),
        })

    finished.sort(key=lambda x: x.get('finished_at') or 0)
    return finished


def group_finished_by_month(
    finished_books: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group finished books by month (YYYY-MM key)."""
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for book in finished_books:
        ts = book.get('finished_at')
        if ts:
            dt = datetime.fromtimestamp(ts / 1000)
            grouped[dt.strftime("%Y-%m")].append(book)
    return dict(sorted(grouped.items()))


def group_finished_by_year(
    finished_books: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group finished books by year."""
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for book in finished_books:
        ts = book.get('finished_at')
        if ts:
            dt = datetime.fromtimestamp(ts / 1000)
            grouped[str(dt.year)].append(book)
    return dict(sorted(grouped.items()))


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
