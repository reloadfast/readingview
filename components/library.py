"""
Library view component - displays audiobooks in a bookshelf grid.
"""

import streamlit as st
from typing import List, Dict, Any
from api.audiobookshelf import AudiobookshelfAPI, AudiobookData
from api.openlibrary import OpenLibraryAPI
from config.config import config
from utils.helpers import format_date_short, render_skeleton_grid, render_empty_state
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
        # ISBN availability notice
        has_isbn = [ed for ed in editions if ed.get("isbn")]
        no_isbn = len(editions) - len(has_isbn)
        if no_isbn > 0:
            st.caption(f"{no_isbn} of {len(editions)} editions have no ISBN")

        # Group by format for large lists
        display_editions = editions
        if len(editions) > 20:
            formats = sorted({ed.get("format") or "Unknown" for ed in editions})
            if len(formats) > 1:
                fmt_filter = st.selectbox(
                    "Filter by format",
                    ["All formats"] + formats,
                    key="_rec_fmt_filter",
                )
                if fmt_filter != "All formats":
                    display_editions = [
                        ed for ed in editions
                        if (ed.get("format") or "Unknown") == fmt_filter
                    ]

            # Search filter for very large lists
            if len(display_editions) > 30:
                ed_search = st.text_input(
                    "Search editions",
                    placeholder="Filter by publisher, year, ISBN...",
                    key="_rec_ed_search",
                )
                if ed_search:
                    q = ed_search.lower()
                    display_editions = [
                        ed for ed in display_editions
                        if q in _format_edition_label(ed).lower()
                    ]

        # Map indices back to the full editions list
        ed_index_map = {id(ed): i for i, ed in enumerate(editions)}
        labels = [_format_edition_label(ed) for ed in display_editions]
        display_indices = list(range(len(display_editions)))

        # Find default within the displayed subset
        disp_default = 0
        if default_idx < len(editions):
            target = editions[default_idx]
            for di, ed in enumerate(display_editions):
                if ed is target:
                    disp_default = di
                    break

        selected_disp_idx = st.selectbox(
            "Select edition",
            display_indices,
            index=disp_default,
            format_func=lambda i: labels[i],
        )

        selected = display_editions[selected_disp_idx]

        # Show details for selected edition
        col1, col2 = st.columns([1, 2])
        with col1:
            if selected.get("cover_id"):
                ol = OpenLibraryAPI()
                cover_url = ol.get_cover_url(cover_id=selected["cover_id"], size="M")
                if cover_url:
                    st.image(cover_url, width=120)
        with col2:
            if selected.get("format"):
                st.markdown(f"**Format:** {selected['format']}")
            if selected.get("publish_date"):
                st.markdown(f"**Published:** {selected['publish_date']}")
            if selected.get("publishers"):
                st.markdown(f"**Publisher:** {', '.join(selected['publishers'][:2])}")
            if selected.get("isbn"):
                st.markdown(f"**ISBN:** {selected['isbn']}")
            else:
                st.caption("No ISBN available for this edition")
            if selected.get("pages"):
                st.markdown(f"**Pages:** {selected['pages']}")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Confirm", type="primary", use_container_width=True):
                with st.spinner("Ingesting..."):
                    try:
                        if selected.get("isbn"):
                            book_recommender.ingest(isbn=selected["isbn"])
                        elif work_key:
                            book_recommender.ingest(work_key=work_key)
                        else:
                            book_recommender.ingest(
                                title=book["title"], author=book["author"]
                            )
                        st.toast("Added to recommender!", icon="✅")
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
        st.info("No editions found on Open Library. Will ingest by title/author.")
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
                        st.toast("Added to recommender!", icon="✅")
                    except Exception as e:
                        logger.error("Recommender ingest failed: %s", e)
                        st.error(f"Failed: {e}")
                _cleanup_dialog_state()
        with btn_col2:
            if st.button("Cancel", use_container_width=True):
                _cleanup_dialog_state()
                st.rerun()


@st.dialog("Similar Books")
def _similar_book_dialog():
    """Show instant recommendations similar to the selected book."""
    import book_recommender

    book = st.session_state.get("_similar_book")
    if not book:
        st.warning("No book selected.")
        if st.button("Close"):
            del st.session_state["_similar_book"]
            st.rerun()
        return

    st.markdown(f"**Books similar to:** {book['title']} by {book['author']}")

    # Check if this book is in the recommender catalog
    from book_recommender._config import get_config
    from book_recommender._db import RecommenderDB
    cfg = get_config()
    rec_db = RecommenderDB(cfg.db_path)

    # Try to find by title match in the catalog
    all_books = rec_db.get_all_books()
    matched_id = None
    for b in all_books:
        if b["title"].lower() == book["title"].lower():
            matched_id = b["id"]
            break

    if matched_id:
        with st.spinner("Finding similar books..."):
            results = book_recommender.recommend(liked_book_ids=[matched_id])
    else:
        # Book not in catalog — use title + description as free-text prompt
        prompt_parts = [book["title"]]
        if book.get("author"):
            prompt_parts.append(f"by {book['author']}")
        if book.get("description"):
            prompt_parts.append(book["description"][:200])
        with st.spinner("Finding similar books..."):
            results = book_recommender.recommend(
                free_text_prompt=" — ".join(prompt_parts)
            )

    if not results:
        st.info("No similar books found. Try adding more books to the catalog first.")
    else:
        for rec in results[:5]:
            st.markdown(f"**{rec['title']}** — {', '.join(rec.get('authors', []))}")
            if rec.get("description"):
                st.caption(rec["description"][:200] + ("..." if len(rec["description"] or "") > 200 else ""))
            st.progress(min(rec["score"], 1.0), text=f"Similarity: {rec['score']:.0%}")
            if rec.get("explanation"):
                st.markdown(f"*{rec['explanation']}*")
            st.markdown("---")

    if st.button("Close", use_container_width=True):
        del st.session_state["_similar_book"]
        st.rerun()


def trigger_library_dialogs():
    """Call once per page render (before tabs) to avoid duplicate dialog IDs."""
    if not config.has_book_recommender():
        return
    if st.session_state.get("_rec_add_book"):
        _edition_picker_dialog()
    if st.session_state.get("_similar_book"):
        _similar_book_dialog()


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_items_in_progress(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_user_items_in_progress()


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_progress_map(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_media_progress_map()


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_all_library_items(base_url: str, token: str):
    """Fetch all items across all libraries."""
    api = AudiobookshelfAPI(base_url, token)
    items = []
    for lib in api.get_libraries():
        items.extend(api.get_library_items(lib["id"]))
    return items


def _inject_bookshelf_css():
    """Inject shared CSS for bookshelf card styling."""
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


def _render_book_card(api, metadata, progress_info, key_suffix, db=None):
    """Render a single book card in the bookshelf grid.

    Args:
        api: Audiobookshelf API client (for cover URLs)
        metadata: Book metadata dict from AudiobookData.extract_metadata()
        progress_info: Progress dict from AudiobookData.calculate_progress()
        key_suffix: Unique suffix for Streamlit widget keys
        db: Optional ReleaseTrackerDB for book notes
    """
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
        if st.button(metadata["author"], key=f"author_{key_suffix}"):
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

        # Finished date or time remaining
        if progress_info['is_finished'] and progress_info.get('finished_at'):
            date_finished = format_date_short(progress_info['finished_at'])
            st.markdown(
                f'<div class="book-stat"><span class="book-stat-label">Finished:</span> {date_finished}</div>',
                unsafe_allow_html=True
            )
        else:
            time_remaining = AudiobookData.format_duration(progress_info['time_remaining'])
            st.markdown(
                f'<div class="book-stat"><span class="book-stat-label">Remaining:</span> {time_remaining}</div>',
                unsafe_allow_html=True
            )

        # Book note indicator / toggle
        if db:
            note = db.get_book_note(metadata["id"])
            note_key = f"note_edit_{key_suffix}"
            if note:
                st.markdown(
                    f'<div class="book-stat" style="margin-top:4px;">'
                    f'<span class="book-stat-label">Note:</span> '
                    f'{note[:60]}{"..." if len(note) > 60 else ""}</div>',
                    unsafe_allow_html=True,
                )
            if st.button("Note" if not note else "Edit Note", key=f"note_btn_{key_suffix}",
                         use_container_width=True):
                st.session_state[note_key] = not st.session_state.get(note_key, False)
                st.rerun()
            if st.session_state.get(note_key):
                new_note = st.text_area(
                    "Note",
                    value=note or "",
                    key=f"note_ta_{key_suffix}",
                    label_visibility="collapsed",
                    height=80,
                )
                nc1, nc2 = st.columns(2)
                with nc1:
                    if st.button("Save", key=f"note_save_{key_suffix}", use_container_width=True):
                        if new_note.strip():
                            db.set_book_note(metadata["id"], new_note.strip())
                            st.toast("Note saved!", icon="✅")
                        else:
                            db.delete_book_note(metadata["id"])
                            st.toast("Note removed", icon="✅")
                        st.session_state[note_key] = False
                        st.rerun()
                with nc2:
                    if st.button("Cancel", key=f"note_cancel_{key_suffix}", use_container_width=True):
                        st.session_state[note_key] = False
                        st.rerun()

        # Action buttons (feature-gated)
        if config.has_book_recommender():
            btn_cols = st.columns(2)
            with btn_cols[0]:
                if st.button("+ Recommender", key=f"rec_{key_suffix}",
                             use_container_width=True):
                    st.session_state["_rec_add_book"] = metadata
                    st.rerun()
            with btn_cols[1]:
                if st.button("Similar", key=f"sim_{key_suffix}",
                             use_container_width=True):
                    st.session_state["_similar_book"] = metadata
                    st.rerun()


def _render_bulk_ingest(items: List[Dict[str, Any]], progress_map: Dict[str, Any]):
    """Render bulk ingest section allowing multi-select book addition to recommender."""
    import book_recommender

    with st.expander("Bulk Add to Recommender"):
        st.markdown("Select multiple books to add to the recommender catalog at once.")

        # Build book list with checkboxes
        book_list = []
        for item in items:
            meta = AudiobookData.extract_metadata(item)
            book_list.append({
                "title": meta["title"],
                "author": meta["author"],
                "isbn": meta.get("isbn"),
                "id": meta["id"],
            })

        if not book_list:
            st.info("No books available.")
            return

        # Use a form to batch the checkbox interactions
        with st.form("bulk_ingest_form"):
            selected = []
            for i, book in enumerate(book_list):
                label = f"{book['title']} — {book['author']}"
                if st.checkbox(label, key=f"bulk_{i}"):
                    selected.append(book)

            submitted = st.form_submit_button(
                f"Add Selected to Recommender",
                type="primary",
            )

        if submitted and selected:
            progress_bar = st.progress(0, text="Ingesting books...")
            success_count = 0
            for i, book in enumerate(selected):
                try:
                    if book.get("isbn"):
                        book_recommender.ingest(isbn=book["isbn"])
                    else:
                        book_recommender.ingest(
                            title=book["title"],
                            author=book["author"],
                        )
                    success_count += 1
                except Exception as e:
                    logger.error("Bulk ingest failed for %s: %s", book["title"], e)
                progress_bar.progress(
                    (i + 1) / len(selected),
                    text=f"Ingesting {i + 1}/{len(selected)}...",
                )
            st.toast(f"Added {success_count}/{len(selected)} books to the recommender.", icon="✅")
        elif submitted:
            st.warning("No books selected.")


def render_in_progress_view(api: AudiobookshelfAPI, db=None):
    """
    Render the in-progress books view with bookshelf-style grid.

    Args:
        api: Audiobookshelf API client
        db: Optional ReleaseTrackerDB for book notes
    """
    st.markdown("### 📖 In Progress")

    # Fetch in-progress items and progress data (cached)
    _sk = st.empty()
    with _sk.container():
        render_skeleton_grid(config.ITEMS_PER_ROW, 2)
    items = _fetch_items_in_progress(api.base_url, api.token)
    progress_map = _fetch_progress_map(api.base_url, api.token)
    _sk.empty()

    if not items:
        render_empty_state(
            "Nothing in progress",
            "Open Audiobookshelf and start listening to see your books here!",
            icon="🎧",
            action_label="Open Audiobookshelf",
            action_url=config.ABS_URL,
        )
        return
    
    # Configuration
    items_per_row = config.ITEMS_PER_ROW

    _inject_bookshelf_css()
    
    # Display filter options
    col1, col2 = st.columns([3, 1])
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Recently Updated", "Progress (Ascending)", "Progress (Descending)", "Title (A-Z)"],
            label_visibility="collapsed",
            key="in_progress_sort",
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
                _render_book_card(api, metadata, progress_info, f"ip_{item_idx}", db=db)

    # Display count
    st.markdown(f"---")
    st.caption(f"Showing {len(items)} audiobook{'s' if len(items) != 1 else ''} in progress")


def render_library_view(api: AudiobookshelfAPI, db=None):
    """
    Render the full library view with search, pagination, and bookshelf grid.
    Includes a toggle to show all books or only finished books.

    Args:
        api: Audiobookshelf API client
        db: Optional ReleaseTrackerDB for book notes
    """
    st.markdown("### 📚 Library")

    # Fetch all library items and progress data (cached)
    _sk = st.empty()
    with _sk.container():
        render_skeleton_grid(config.ITEMS_PER_ROW, 2)
    items = _fetch_all_library_items(api.base_url, api.token)
    progress_map = _fetch_progress_map(api.base_url, api.token)
    _sk.empty()

    if not items:
        render_empty_state(
            "Library is empty",
            "No audiobooks found. Add some books to your Audiobookshelf library to get started!",
            icon="📚",
            action_label="Open Audiobookshelf",
            action_url=config.ABS_URL,
        )
        return

    items_per_row = config.ITEMS_PER_ROW

    _inject_bookshelf_css()

    def _get_progress(item: Dict[str, Any]) -> Dict[str, Any]:
        """Look up progress from the progress map, falling back to inline fields."""
        return (
            progress_map.get(item.get('id', ''))
            or item.get('userMediaProgress')
            or item.get('mediaProgress')
            or {}
        )

    # View filter: All / Finished
    view_mode = st.radio(
        "View",
        ["All Books", "Finished"],
        horizontal=True,
        key="lib_view_mode",
        label_visibility="collapsed",
    )

    if view_mode == "Finished":
        items = [
            item for item in items
            if _get_progress(item).get('isFinished', False)
        ]
        if not items:
            st.info("No finished books found.")
            return

    # Controls row: search, items per page, sort
    sort_options = ["Recently Updated", "Progress (Ascending)", "Progress (Descending)", "Title (A-Z)"]
    if view_mode == "Finished":
        sort_options = ["Recently Finished", "Title (A-Z)", "Progress (Ascending)", "Progress (Descending)"]

    ctrl1, ctrl2, ctrl3 = st.columns([3, 1, 1])
    with ctrl1:
        search_query = st.text_input(
            "Search",
            placeholder="Search by title, author, or series...",
            label_visibility="collapsed",
            key="lib_search",
        )
    with ctrl2:
        per_page = st.selectbox(
            "Per page",
            [10, 20, 50, 100],
            index=1,
            label_visibility="collapsed",
            key="lib_per_page",
        )
    with ctrl3:
        sort_by = st.selectbox(
            "Sort by",
            sort_options,
            label_visibility="collapsed",
            key="lib_sort",
        )

    # Client-side search filtering (includes book notes)
    if search_query:
        query_lower = search_query.lower()
        notes_map = db.get_all_book_notes() if db else {}
        filtered = []
        for item in items:
            meta = item.get('media', {}).get('metadata', {})
            title = (meta.get('title') or '').lower()
            author = (meta.get('authorName') or '').lower()
            series_names = ' '.join(
                (s.get('name') or '') for s in (meta.get('series') or [])
            ).lower()
            note_text = (notes_map.get(item.get('id', '')) or '').lower()
            if query_lower in title or query_lower in author or query_lower in series_names or query_lower in note_text:
                filtered.append(item)
        items = filtered

    # Sort items
    if sort_by == "Progress (Ascending)":
        items.sort(key=lambda x: _get_progress(x).get('progress', 0))
    elif sort_by == "Progress (Descending)":
        items.sort(key=lambda x: _get_progress(x).get('progress', 0), reverse=True)
    elif sort_by == "Recently Updated":
        items.sort(key=lambda x: _get_progress(x).get('lastUpdate', 0), reverse=True)
    elif sort_by == "Recently Finished":
        items.sort(key=lambda x: _get_progress(x).get('finishedAt', 0), reverse=True)
    elif sort_by == "Title (A-Z)":
        items.sort(key=lambda x: x.get('media', {}).get('metadata', {}).get('title', ''))

    # Pagination state
    total_items = len(items)
    total_pages = max(1, math.ceil(total_items / per_page))

    if "lib_page" not in st.session_state:
        st.session_state["lib_page"] = 0

    # Reset page if out of bounds (e.g. after search narrows results)
    if st.session_state["lib_page"] >= total_pages:
        st.session_state["lib_page"] = 0

    current_page = st.session_state["lib_page"]
    start_idx = current_page * per_page
    end_idx = min(start_idx + per_page, total_items)
    page_items = items[start_idx:end_idx]

    # Pagination controls (top)
    def _render_pagination(position):
        pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
        with pcol1:
            if st.button("Previous", key=f"lib_prev_{position}", disabled=current_page == 0,
                         use_container_width=True):
                st.session_state["lib_page"] = current_page - 1
                st.rerun()
        with pcol2:
            if total_items > 0:
                st.markdown(
                    f'<div style="text-align: center; color: #a8a8a8; padding: 8px 0;">'
                    f'Showing {start_idx + 1}–{end_idx} of {total_items} books'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="text-align: center; color: #a8a8a8; padding: 8px 0;">No books match your search</div>',
                    unsafe_allow_html=True,
                )
        with pcol3:
            if st.button("Next", key=f"lib_next_{position}", disabled=current_page >= total_pages - 1,
                         use_container_width=True):
                st.session_state["lib_page"] = current_page + 1
                st.rerun()

    _render_pagination("top")

    # Grid rendering
    if page_items:
        num_rows = math.ceil(len(page_items) / items_per_row)
        for row in range(num_rows):
            cols = st.columns(items_per_row)
            for col_idx in range(items_per_row):
                item_idx = row * items_per_row + col_idx
                if item_idx >= len(page_items):
                    break

                item = page_items[item_idx]
                metadata = AudiobookData.extract_metadata(item)
                progress_data = _get_progress(item)
                progress_info = AudiobookData.calculate_progress(
                    progress_data,
                    metadata['duration']
                )

                # Use global index for unique keys
                global_idx = start_idx + item_idx
                with cols[col_idx]:
                    _render_book_card(api, metadata, progress_info, f"lib_{global_idx}", db=db)

    # Pagination controls (bottom)
    st.markdown("---")
    _render_pagination("bottom")

    # Bulk ingest to recommender (feature-gated)
    if config.has_book_recommender():
        _render_bulk_ingest(items, progress_map)
