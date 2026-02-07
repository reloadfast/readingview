"""
Utility functions for the Shelf application.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import streamlit as st
from collections import defaultdict
from config.config import config


# ---------------------------------------------------------------------------
# Date format mapping
# ---------------------------------------------------------------------------

_DATE_FORMAT_MAP = {
    "MM/DD/YYYY": "%m/%d/%Y",
    "DD/MM/YYYY": "%d/%m/%Y",
    "YYYY-MM-DD": "%Y-%m-%d",
}


def _resolve_date_fmt(long: bool = False) -> str:
    """Return the strftime pattern for the configured DATE_FORMAT."""
    fmt = config.DATE_FORMAT.strip()
    if fmt in _DATE_FORMAT_MAP:
        return _DATE_FORMAT_MAP[fmt]
    if fmt:
        return fmt  # allow raw strftime patterns
    return "%B %d, %Y" if long else "%b %d, %Y"


def format_date_obj(dt: datetime) -> str:
    """Format a datetime object using the configured date format."""
    return dt.strftime(_resolve_date_fmt(long=False))


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
        return dt.strftime(_resolve_date_fmt(long=True))
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
        return dt.strftime(_resolve_date_fmt(long=False))
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


_SKELETON_CSS_INJECTED = False


def render_skeleton_grid(cols: int = 5, rows: int = 2):
    """Render a CSS-animated skeleton grid that mimics a book card layout."""
    global _SKELETON_CSS_INJECTED
    if not _SKELETON_CSS_INJECTED:
        st.markdown(
            "<style>"
            "@keyframes sk-pulse{0%,100%{opacity:.15}50%{opacity:.3}}"
            ".sk-card{background:rgba(255,255,255,.06);border-radius:10px;"
            "padding:12px;animation:sk-pulse 1.5s ease-in-out infinite}"
            ".sk-cover{background:rgba(255,255,255,.1);border-radius:6px;"
            "width:100%;aspect-ratio:2/3;margin-bottom:8px}"
            ".sk-line{background:rgba(255,255,255,.1);border-radius:4px;"
            "height:12px;margin-bottom:6px}"
            ".sk-line.short{width:60%}"
            "</style>",
            unsafe_allow_html=True,
        )
        _SKELETON_CSS_INJECTED = True

    for _ in range(rows):
        row_cols = st.columns(cols)
        for c in row_cols:
            with c:
                st.markdown(
                    '<div class="sk-card">'
                    '<div class="sk-cover"></div>'
                    '<div class="sk-line"></div>'
                    '<div class="sk-line short"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )


def render_skeleton_stats(count: int = 3):
    """Render skeleton stat cards for the statistics view."""
    global _SKELETON_CSS_INJECTED
    if not _SKELETON_CSS_INJECTED:
        render_skeleton_grid(0, 0)  # inject CSS only
    cols = st.columns(count)
    for c in cols:
        with c:
            st.markdown(
                '<div class="sk-card" style="min-height:80px">'
                '<div class="sk-line" style="height:28px;width:40%;margin-bottom:10px"></div>'
                '<div class="sk-line short"></div>'
                '</div>',
                unsafe_allow_html=True,
            )


def render_skeleton_list(count: int = 4):
    """Render skeleton rows for list-style views (authors, series)."""
    global _SKELETON_CSS_INJECTED
    if not _SKELETON_CSS_INJECTED:
        render_skeleton_grid(0, 0)
    for _ in range(count):
        st.markdown(
            '<div class="sk-card" style="display:flex;gap:12px;align-items:center;margin-bottom:8px">'
            '<div style="background:rgba(255,255,255,.1);border-radius:50%;'
            'width:48px;height:48px;flex-shrink:0"></div>'
            '<div style="flex:1">'
            '<div class="sk-line" style="width:50%"></div>'
            '<div class="sk-line short"></div>'
            '</div></div>',
            unsafe_allow_html=True,
        )


def render_empty_state(
    title: str,
    message: str,
    icon: str = "📭",
    action_label: str | None = None,
    action_url: str | None = None,
):
    """Render a helpful empty state instead of a plain st.info message."""
    link_html = ""
    if action_label and action_url:
        safe_url = sanitize_url(action_url)
        if safe_url:
            link_html = (
                f'<a href="{safe_url}" target="_blank" '
                f'style="color:#4a9eff;text-decoration:none;font-weight:600;">'
                f'{action_label}</a>'
            )
    st.markdown(
        f'<div style="text-align:center;padding:48px 24px;'
        f'background:rgba(255,255,255,0.03);border-radius:12px;'
        f'border:1px dashed rgba(255,255,255,0.1);margin:24px 0;">'
        f'<div style="font-size:48px;margin-bottom:12px;">{icon}</div>'
        f'<div style="font-size:18px;font-weight:600;color:#e8e8e8;margin-bottom:8px;">{title}</div>'
        f'<div style="color:#a8a8a8;max-width:400px;margin:0 auto 12px;">{message}</div>'
        f'{link_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
