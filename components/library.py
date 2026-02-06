"""
Library view component - displays audiobooks in a bookshelf grid.
"""

import streamlit as st
from typing import List, Dict, Any
from api.audiobookshelf import AudiobookshelfAPI, AudiobookData
from api.openlibrary import OpenLibraryAPI
from config.config import config
from utils.helpers import format_date_short
import logging
import math

logger = logging.getLogger(__name__)


def _cleanup_dialog_state():
    """Remove all _rec_* keys from session_state."""
    keys = [k for k in st.session_state if k.startswith("_rec_")]
    for k in keys:
        del st.session_state[k]


def _format_edition_label(ed: Dict[str, Any]) -> str:
    """Build a human-readable label for the edition selectbox."""
    parts = []
    if ed["format"]:
        parts.append(ed["format"])
    if ed["publish_date"]:
        parts.append(ed["publish_date"])
    if ed["publishers"]:
        parts.append(", ".join(ed["publishers"][:2]))
    if ed["isbn"]:
        parts.append(f"ISBN {ed['isbn']}")
    if ed["pages"]:
        parts.append(f"{ed['pages']}p")
    return " | ".join(parts) if parts else ed.get("edition_key", "Unknown edition")


@st.dialog("Add to Recommender")
def _edition_picker_dialog():
    """Two-phase dialog: OL lookup then edition selection."""
    import book_recommender

    book = st.session_state.get("_rec_add_book")
    if not book:
        st.warning("No book selected.")
        if st.button("Close"):
            _cleanup_dialog_state()
            st.rerun()
        return

    st.markdown(f"**{book['title']}** by {book['author']}")

    # Phase 1: OL lookup (cached in session_state)
    if "_rec_editions" not in st.session_state:
        with st.spinner("Searching Open Library..."):
            ol = OpenLibraryAPI()
            work_key = None
            search_results = []

            # Try ISBN first
            isbn = book.get("isbn")
            if isbn:
                search_results = ol.search_books(query=f"isbn:{isbn}", limit=3)

            # Fallback to title + author
            if not search_results:
                search_results = ol.search_books(
                    title=book["title"], author=book["author"], limit=5
                )

            if search_results:
                work_key = search_results[0].get("key")

            if work_key:
                editions_raw = ol.get_work_editions(work_key)
                if editions_raw:
                    editions, default_idx = ol.select_default_edition(editions_raw)
                    st.session_state["_rec_work_key"] = work_key
                    st.session_state["_rec_editions"] = editions
                    st.session_state["_rec_default_idx"] = default_idx
                else:
                    # Work found but no editions — allow direct ingest
                    st.session_state["_rec_work_key"] = work_key
                    st.session_state["_rec_editions"] = []
                    st.session_state["_rec_default_idx"] = 0
            else:
                # No work found — direct ingest by title/author
                st.session_state["_rec_work_key"] = None
                st.session_state["_rec_editions"] = []
                st.session_state["_rec_default_idx"] = 0

        st.rerun()

    editions = st.session_state.get("_rec_editions", [])
    work_key = st.session_state.get("_rec_work_key")
    default_idx = st.session_state.get("_rec_default_idx", 0)

    # Phase 2: Edition picker or direct ingest
    if editions:
        labels = [_format_edition_label(ed) for ed in editions]
        selected_idx = st.selectbox(
            "Select edition",
            range(len(editions)),
            index=default_idx,
            format_func=lambda i: labels[i],
        )

        selected = editions[selected_idx]

        # Show details for selected edition
        col1, col2 = st.columns([1, 2])
        with col1:
            if selected["cover_id"]:
                ol = OpenLibraryAPI()
                cover_url = ol.get_cover_url(cover_id=selected["cover_id"], size="M")
                if cover_url:
                    st.image(cover_url, width=120)
        with col2:
            if selected["format"]:
                st.markdown(f"**Format:** {selected['format']}")
            if selected["publish_date"]:
                st.markdown(f"**Published:** {selected['publish_date']}")
            if selected["publishers"]:
                st.markdown(f"**Publisher:** {', '.join(selected['publishers'][:2])}")
            if selected["isbn"]:
                st.markdown(f"**ISBN:** {selected['isbn']}")
            if selected["pages"]:
                st.markdown(f"**Pages:** {selected['pages']}")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Confirm", type="primary", use_container_width=True):
                with st.spinner("Ingesting..."):
                    try:
                        if selected["isbn"]:
                            book_recommender.ingest(isbn=selected["isbn"])
                        elif work_key:
                            book_recommender.ingest(work_key=work_key)
                        else:
                            book_recommender.ingest(
                                title=book["title"], author=book["author"]
                            )
                        st.success("Added to recommender!")
                    except Exception as e:
                        logger.error("Recommender ingest failed: %s", e)
                        st.error(f"Failed: {e}")
                _cleanup_dialog_state()
        with btn_col2:
            if st.button("Cancel", use_container_width=True):
                _cleanup_dialog_state()
                st.rerun()
    else:
        # No editions available — direct ingest
        st.info("No editions found. Will ingest by title/author.")
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Confirm", type="primary", use_container_width=True):
                with st.spinner("Ingesting..."):
                    try:
                        if work_key:
                            book_recommender.ingest(work_key=work_key)
                        elif book.get("isbn"):
                            book_recommender.ingest(isbn=book["isbn"])
                        else:
                            book_recommender.ingest(
                                title=book["title"], author=book["author"]
                            )
                        st.success("Added to recommender!")
                    except Exception as e:
                        logger.error("Recommender ingest failed: %s", e)
                        st.error(f"Failed: {e}")
                _cleanup_dialog_state()
        with btn_col2:
            if st.button("Cancel", use_container_width=True):
                _cleanup_dialog_state()
                st.rerun()


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_items_in_progress(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_user_items_in_progress()


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_progress_map(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_media_progress_map()


def render_library_view(api: AudiobookshelfAPI):
    """
    Render the library view with bookshelf-style grid.

    Args:
        api: Audiobookshelf API client
    """
    # Trigger edition picker dialog if a book was selected
    if config.has_book_recommender() and st.session_state.get("_rec_add_book"):
        _edition_picker_dialog()

    st.markdown("### 📚 Library")

    # Fetch in-progress items and progress data (cached)
    with st.spinner("Loading your audiobooks..."):
        items = _fetch_items_in_progress(api.base_url, api.token)
        progress_map = _fetch_progress_map(api.base_url, api.token)

    if not items:
        st.info("No audiobooks in progress. Start listening to see them here!")
        return
    
    # Configuration
    items_per_row = 5
    
    # Custom CSS for bookshelf styling
    st.markdown("""
        <style>
        .book-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .book-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }
        
        .book-cover {
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            margin-bottom: 12px;
        }
        
        .book-title {
            font-size: 16px;
            font-weight: 600;
            color: #e8e8e8;
            margin-bottom: 4px;
            line-height: 1.3;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        .book-author {
            font-size: 14px;
            color: #a8a8a8;
            margin-bottom: 8px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .book-stat {
            font-size: 13px;
            color: #c0c0c0;
            margin-bottom: 4px;
        }
        
        .book-stat-label {
            color: #808080;
            font-weight: 500;
        }
        
        .progress-bar-container {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }
        
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #4a9eff 0%, #7b68ee 100%);
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        /* Author link button styled as text */
        [data-testid="stElementContainer"]:has(.author-link) + [data-testid="stElementContainer"] button {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: #a8a8a8 !important;
            font-size: 14px !important;
            min-height: 0 !important;
            font-weight: normal !important;
            text-align: left !important;
            cursor: pointer !important;
        }
        [data-testid="stElementContainer"]:has(.author-link) + [data-testid="stElementContainer"] button:hover {
            color: #4a9eff !important;
            text-decoration: underline !important;
            background: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display filter options
    col1, col2 = st.columns([3, 1])
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Recently Updated", "Progress (Ascending)", "Progress (Descending)", "Title (A-Z)"],
            label_visibility="collapsed"
        )
    
    def _get_progress(item: Dict[str, Any]) -> Dict[str, Any]:
        """Look up progress from the progress map, falling back to inline fields."""
        return (
            progress_map.get(item.get('id', ''))
            or item.get('userMediaProgress')
            or item.get('mediaProgress')
            or {}
        )

    # Sort items
    if sort_by == "Progress (Ascending)":
        items.sort(key=lambda x: _get_progress(x).get('progress', 0))
    elif sort_by == "Progress (Descending)":
        items.sort(key=lambda x: _get_progress(x).get('progress', 0), reverse=True)
    elif sort_by == "Recently Updated":
        items.sort(key=lambda x: _get_progress(x).get('lastUpdate', 0), reverse=True)
    elif sort_by == "Title (A-Z)":
        items.sort(key=lambda x: x.get('media', {}).get('metadata', {}).get('title', ''))
    
    # Calculate number of rows
    num_rows = math.ceil(len(items) / items_per_row)
    
    # Display items in grid
    for row in range(num_rows):
        cols = st.columns(items_per_row)
        
        for col_idx in range(items_per_row):
            item_idx = row * items_per_row + col_idx
            
            if item_idx >= len(items):
                break
            
            item = items[item_idx]
            metadata = AudiobookData.extract_metadata(item)
            progress_data = _get_progress(item)
            progress_info = AudiobookData.calculate_progress(
                progress_data, 
                metadata['duration']
            )
            
            with cols[col_idx]:
                # Book card
                with st.container():
                    # Cover image
                    cover_url = api.get_cover_url(metadata['id'])
                    st.markdown(
                        f'<img src="{cover_url}" class="book-cover" alt="{metadata["title"]}">',
                        unsafe_allow_html=True
                    )
                    
                    # Title and author
                    st.markdown(
                        f'<div class="book-title" title="{metadata["title"]}">{metadata["title"]}</div>'
                        f'<span class="author-link"></span>',
                        unsafe_allow_html=True
                    )
                    if st.button(metadata["author"], key=f"lib_author_{item_idx}"):
                        st.session_state["selected_author"] = metadata["author"]
                        st.session_state["navigate_to_authors"] = True
                        st.rerun()
                    
                    # Progress percentage
                    progress_pct = progress_info['progress']
                    st.markdown(
                        f'<div class="book-stat"><span class="book-stat-label">Progress:</span> {progress_pct:.1f}%</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Progress bar
                    st.markdown(
                        f'''
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" style="width: {progress_pct}%;"></div>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                    
                    # Date started
                    if progress_info['started_at']:
                        date_started = format_date_short(progress_info['started_at'])
                        st.markdown(
                            f'<div class="book-stat" style="margin-top: 8px;"><span class="book-stat-label">Started:</span> {date_started}</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Time remaining
                    time_remaining = AudiobookData.format_duration(progress_info['time_remaining'])
                    st.markdown(
                        f'<div class="book-stat"><span class="book-stat-label">Remaining:</span> {time_remaining}</div>',
                        unsafe_allow_html=True
                    )

                    # Add to Recommender button (feature-gated)
                    if config.has_book_recommender():
                        if st.button("+ Recommender", key=f"rec_add_{item_idx}",
                                     use_container_width=True):
                            st.session_state["_rec_add_book"] = metadata
                            st.rerun()
    
    # Display count
    st.markdown(f"---")
    st.caption(f"Showing {len(items)} audiobook{'s' if len(items) != 1 else ''} in progress")
