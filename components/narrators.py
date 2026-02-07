"""
Narrators component — groups books by narrator, shows listen counts,
and links to the narrator's other books in the library.
"""

import math
import streamlit as st
from typing import Any, Dict, List
from api.audiobookshelf import AudiobookshelfAPI, AudiobookData
from config.config import config
from utils.helpers import render_skeleton_grid, render_empty_state
import logging

logger = logging.getLogger(__name__)


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_all_items(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    items = []
    for lib in api.get_libraries():
        items.extend(api.get_library_items(lib["id"]))
    return items


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_progress_map(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_media_progress_map()


def _build_narrator_map(
    items: List[Dict[str, Any]],
    progress_map: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Group books by narrator name."""
    narrators: Dict[str, Dict[str, Any]] = {}
    for item in items:
        meta = AudiobookData.extract_metadata(item)
        narrator_str = meta.get("narrator") or ""
        if not narrator_str:
            continue
        # A book may have multiple narrators separated by commas
        names = [n.strip() for n in narrator_str.split(",") if n.strip()]
        prog = progress_map.get(meta["id"], {})
        for name in names:
            if name not in narrators:
                narrators[name] = {"name": name, "books": [], "total_duration": 0, "finished": 0}
            narrators[name]["books"].append({
                "id": meta["id"],
                "title": meta["title"],
                "author": meta["author"],
                "duration": meta["duration"],
                "is_finished": prog.get("isFinished", False),
            })
            narrators[name]["total_duration"] += meta["duration"]
            if prog.get("isFinished"):
                narrators[name]["finished"] += 1
    return narrators


def render_narrators_view(api: AudiobookshelfAPI):
    """Render the narrators view."""
    st.markdown("### Narrators")

    _sk = st.empty()
    with _sk.container():
        render_skeleton_grid(config.ITEMS_PER_ROW, 2)
    items = _fetch_all_items(api.base_url, api.token)
    progress_map = _fetch_progress_map(api.base_url, api.token)
    _sk.empty()

    narrator_map = _build_narrator_map(items, progress_map)

    if not narrator_map:
        render_empty_state(
            "No narrators found",
            "Your library items need narrator metadata to appear here.",
            icon="🎙️",
        )
        return

    # Controls
    ctrl1, ctrl2 = st.columns([3, 1])
    with ctrl1:
        search = st.text_input(
            "Search narrators",
            placeholder="Search by narrator name...",
            label_visibility="collapsed",
            key="narrator_search",
        )
    with ctrl2:
        sort_by = st.selectbox(
            "Sort",
            ["Most Books", "Name A-Z", "Most Hours"],
            label_visibility="collapsed",
            key="narrator_sort",
        )

    narrator_list = list(narrator_map.values())

    if search:
        q = search.lower()
        narrator_list = [n for n in narrator_list if q in n["name"].lower()]

    if sort_by == "Most Books":
        narrator_list.sort(key=lambda n: len(n["books"]), reverse=True)
    elif sort_by == "Name A-Z":
        narrator_list.sort(key=lambda n: n["name"].lower())
    elif sort_by == "Most Hours":
        narrator_list.sort(key=lambda n: n["total_duration"], reverse=True)

    if not narrator_list:
        st.info("No narrators match your search.")
        return

    # Detail view if selected
    selected = st.session_state.get("selected_narrator")
    if selected and selected in narrator_map:
        _render_narrator_detail(api, narrator_map[selected])
        return

    # Pagination
    per_page = 20
    total_pages = max(1, math.ceil(len(narrator_list) / per_page))
    page = st.session_state.get("narrator_page", 0)
    if page >= total_pages:
        page = 0
    start = page * per_page
    end = min(start + per_page, len(narrator_list))
    visible = narrator_list[start:end]

    st.caption(f"Showing {start + 1}–{end} of {len(narrator_list)} narrators")

    # Grid
    items_per_row = config.ITEMS_PER_ROW
    rows = math.ceil(len(visible) / items_per_row)

    _inject_narrator_css()

    for row in range(rows):
        cols = st.columns(items_per_row)
        for ci in range(items_per_row):
            idx = row * items_per_row + ci
            if idx >= len(visible):
                break
            nar = visible[idx]
            with cols[ci]:
                book_count = len(nar["books"])
                dur_h = int(nar["total_duration"] // 3600)
                st.markdown(
                    f'<div class="narrator-card">'
                    f'<div style="font-size:36px;margin-bottom:8px;">🎙️</div>'
                    f'<div class="narrator-name">{nar["name"]}</div>'
                    f'<div class="narrator-stat">{book_count} book{"s" if book_count != 1 else ""}</div>'
                    f'<div class="narrator-stat">{dur_h}h total</div>'
                    f'<div class="narrator-stat">{nar["finished"]} finished</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("View", key=f"nar_{start + idx}", use_container_width=True):
                    st.session_state["selected_narrator"] = nar["name"]
                    st.rerun()

    # Pagination
    if total_pages > 1:
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc1:
            if st.button("Previous", disabled=page == 0, key="nar_prev"):
                st.session_state["narrator_page"] = page - 1
                st.rerun()
        with pc2:
            st.markdown(
                f'<div style="text-align:center;color:#a8a8a8;">Page {page + 1} / {total_pages}</div>',
                unsafe_allow_html=True,
            )
        with pc3:
            if st.button("Next", disabled=page >= total_pages - 1, key="nar_next"):
                st.session_state["narrator_page"] = page + 1
                st.rerun()


def _render_narrator_detail(api: AudiobookshelfAPI, narrator: Dict[str, Any]):
    """Show detail view for a single narrator."""
    if st.button("Back to all narrators"):
        del st.session_state["selected_narrator"]
        st.rerun()

    st.markdown(f"### 🎙️ {narrator['name']}")
    book_count = len(narrator["books"])
    dur_h = int(narrator["total_duration"] // 3600)

    cols = st.columns(3)
    with cols[0]:
        st.metric("Books Narrated", book_count)
    with cols[1]:
        st.metric("Total Hours", dur_h)
    with cols[2]:
        st.metric("Finished", narrator["finished"])

    st.markdown("---")
    st.markdown("#### Books")

    for book in narrator["books"]:
        col_cover, col_info = st.columns([1, 4])
        with col_cover:
            st.image(api.get_cover_url(book["id"]), width=80)
        with col_info:
            status = "Finished" if book["is_finished"] else "In Library"
            st.markdown(f"**{book['title']}**")
            st.caption(f"by {book['author']} — {AudiobookData.format_duration(book['duration'])} — {status}")


def _inject_narrator_css():
    st.markdown(
        "<style>"
        ".narrator-card{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);"
        "border-radius:12px;padding:20px;text-align:center;margin-bottom:16px;"
        "box-shadow:0 4px 12px rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.05);"
        "transition:transform .2s;cursor:default}"
        ".narrator-card:hover{transform:translateY(-4px)}"
        ".narrator-name{font-size:16px;font-weight:600;color:#e8e8e8;margin-bottom:8px;"
        "overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
        ".narrator-stat{font-size:13px;color:#a8a8a8;margin-bottom:2px}"
        "</style>",
        unsafe_allow_html=True,
    )
