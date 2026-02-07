"""
Dashboard / Home tab component — shows an at-a-glance overview:
currently listening, recently finished, upcoming releases,
and recommendation of the day.
"""

import streamlit as st
from typing import Any, Dict, List
from api.audiobookshelf import AudiobookshelfAPI, AudiobookData
from config.config import config
from utils.helpers import format_date_short, render_skeleton_stats, render_empty_state
import logging

logger = logging.getLogger(__name__)


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_in_progress(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_user_items_in_progress()


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_progress_map(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_media_progress_map()


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_listening_stats(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_user_listening_stats()


def render_dashboard(api: AudiobookshelfAPI, db=None):
    """Render the dashboard home tab."""

    _sk = st.empty()
    with _sk.container():
        render_skeleton_stats(4)

    items_in_progress = _fetch_in_progress(api.base_url, api.token)
    progress_map = _fetch_progress_map(api.base_url, api.token)
    listening_stats = _fetch_listening_stats(api.base_url, api.token)
    _sk.empty()

    # --- Quick stats row ---
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    total_hours = int((listening_stats.get("totalTime", 0) / 3600)) if listening_stats else 0
    finished_count = sum(
        1 for p in progress_map.values() if p.get("isFinished")
    )
    in_progress_count = len(items_in_progress) if items_in_progress else 0

    _inject_dashboard_css()

    cols = st.columns(4)
    with cols[0]:
        _mini_stat(str(in_progress_count), "In Progress")
    with cols[1]:
        _mini_stat(str(finished_count), "Finished")
    with cols[2]:
        _mini_stat(str(total_hours), "Hours Listened")
    with cols[3]:
        _mini_stat(str(len(stats_items)), "Books Touched")

    st.markdown("---")

    # --- Currently Listening ---
    left, right = st.columns(2)

    with left:
        st.markdown("#### Currently Listening")
        if items_in_progress:
            # Show top 3 most recently updated
            sorted_items = sorted(
                items_in_progress,
                key=lambda x: (
                    progress_map.get(x.get("id", ""), {}).get("lastUpdate", 0)
                    or x.get("userMediaProgress", x.get("mediaProgress", {})).get("lastUpdate", 0)
                ),
                reverse=True,
            )
            for item in sorted_items[:3]:
                meta = AudiobookData.extract_metadata(item)
                prog = (
                    progress_map.get(item.get("id", ""))
                    or item.get("userMediaProgress")
                    or item.get("mediaProgress")
                    or {}
                )
                pct = (prog.get("progress", 0) * 100)
                remaining_s = max(0, meta["duration"] - prog.get("currentTime", 0))
                remaining = AudiobookData.format_duration(remaining_s)

                cover_url = api.get_cover_url(meta["id"])
                col_cover, col_info = st.columns([1, 3])
                with col_cover:
                    st.image(cover_url, width=80)
                with col_info:
                    st.markdown(f"**{meta['title']}**")
                    st.caption(f"{meta['author']}")
                    st.progress(min(pct / 100, 1.0), text=f"{pct:.0f}% — {remaining} left")
        else:
            render_empty_state(
                "Nothing playing",
                "Open Audiobookshelf and start listening!",
                icon="🎧",
                action_label="Open Audiobookshelf",
                action_url=config.ABS_URL,
            )

    with right:
        st.markdown("#### Recently Finished")
        # Find last 3 finished books
        finished = []
        for lib_id, prog in progress_map.items():
            if prog.get("isFinished"):
                stats_item = stats_items.get(lib_id, {})
                meta = stats_item.get("mediaMetadata", {})
                authors = meta.get("authors", [])
                author_str = ", ".join(a.get("name", "") for a in authors) if authors else "Unknown"
                finished.append({
                    "id": lib_id,
                    "title": meta.get("title", "Unknown"),
                    "author": author_str,
                    "finished_at": prog.get("finishedAt"),
                })
        finished.sort(key=lambda x: x.get("finished_at") or 0, reverse=True)

        if finished:
            for book in finished[:3]:
                cover_url = api.get_cover_url(book["id"])
                col_cover, col_info = st.columns([1, 3])
                with col_cover:
                    st.image(cover_url, width=80)
                with col_info:
                    st.markdown(f"**{book['title']}**")
                    st.caption(book["author"])
                    if book.get("finished_at"):
                        st.caption(f"Finished {format_date_short(book['finished_at'])}")
        else:
            render_empty_state(
                "No finished books yet",
                "Complete your first audiobook to see it here.",
                icon="📖",
            )

    st.markdown("---")

    # --- Upcoming Releases ---
    bottom_left, bottom_right = st.columns(2)

    with bottom_left:
        st.markdown("#### Upcoming Releases")
        if db:
            try:
                next_releases = db.get_next_releases(limit=3)
                if next_releases:
                    for rel in next_releases:
                        series_info = f" ({rel['series_name']})" if rel.get("series_name") else ""
                        st.markdown(f"**{rel['book_title']}**{series_info}")
                        date_text = rel.get("release_date", "TBD")
                        st.caption(f"by {rel['author_name']} — {date_text}")
                else:
                    render_empty_state(
                        "No upcoming releases",
                        "Track your favorite authors to see upcoming books here.",
                        icon="📅",
                    )
            except Exception:
                st.caption("Release tracker not available.")
        else:
            st.caption("Release tracker is disabled.")

    # --- Recommendation of the day ---
    with bottom_right:
        st.markdown("#### Recommendation of the Day")
        if config.has_book_recommender():
            try:
                import book_recommender
                recs = book_recommender.recommend(free_text_prompt="surprise me with something great", top_k=1)
                if recs:
                    rec = recs[0]
                    st.markdown(f"**{rec['title']}**")
                    st.caption(f"by {', '.join(rec.get('authors', []))}")
                    if rec.get("description"):
                        st.caption(rec["description"][:200])
                    st.progress(min(rec["score"], 1.0), text=f"Match: {rec['score']:.0%}")
                else:
                    render_empty_state(
                        "No recommendations yet",
                        "Add books to the recommender catalog first.",
                        icon="💡",
                    )
            except Exception:
                render_empty_state(
                    "Recommender unavailable",
                    "Check that Ollama is running and models are pulled.",
                    icon="💡",
                )
        else:
            st.caption("Book recommender is disabled.")


def _inject_dashboard_css():
    st.markdown(
        "<style>"
        ".dash-stat{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);"
        "border-radius:12px;padding:20px;text-align:center;"
        "box-shadow:0 4px 12px rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.05)}"
        ".dash-stat-value{font-size:32px;font-weight:700;color:#4a9eff;margin-bottom:2px}"
        ".dash-stat-label{font-size:13px;color:#a8a8a8;text-transform:uppercase;letter-spacing:1px}"
        "</style>",
        unsafe_allow_html=True,
    )


def _mini_stat(value: str, label: str):
    st.markdown(
        f'<div class="dash-stat">'
        f'<div class="dash-stat-value">{value}</div>'
        f'<div class="dash-stat-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
