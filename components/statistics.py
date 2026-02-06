"""
Statistics view component - displays listening analytics with book breakdowns
and a Year in Recap feature.
"""

import streamlit as st
from typing import Dict, Any, List
from api.audiobookshelf import AudiobookshelfAPI
from config.config import config
from utils.helpers import (
    get_finished_books,
    group_finished_by_month,
    group_finished_by_year,
    format_date_short,
)
import pandas as pd
from datetime import datetime
from collections import Counter


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_listening_stats(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_user_listening_stats()


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_progress_map(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    return api.get_media_progress_map()


def render_statistics_view(api: AudiobookshelfAPI):
    """Render the statistics view with charts, book breakdowns, and Year in Recap."""
    st.markdown("### Statistics")

    with st.spinner("Loading statistics..."):
        listening_stats = _fetch_listening_stats(api.base_url, api.token)
        progress_map = _fetch_progress_map(api.base_url, api.token)

    if not listening_stats and not progress_map:
        st.info("No listening data available yet. Start listening to build your statistics!")
        return

    # Build finished books list from progress + metadata
    stats_items = listening_stats.get('items', {}) if listening_stats else {}
    finished_books = get_finished_books(progress_map, stats_items)
    by_month = group_finished_by_month(finished_books)
    by_year = group_finished_by_year(finished_books)

    # --- Overview cards ---
    total_time_hours = (listening_stats.get('totalTime', 0) / 3600) if listening_stats else 0
    books_finished = len(finished_books)

    # Avg books/month: count distinct months that have at least one finish
    if by_month:
        avg_per_month = books_finished / len(by_month)
    else:
        avg_per_month = 0

    _render_stat_css()

    st.markdown("#### Overview")
    cols = st.columns(3)
    with cols[0]:
        _stat_card(str(books_finished), "Books Completed")
    with cols[1]:
        _stat_card(str(int(total_time_hours)), "Hours Listened")
    with cols[2]:
        _stat_card(f"{avg_per_month:.1f}" if by_month else "-", "Avg Books/Month")

    st.markdown("---")

    # --- Tabs: Yearly | Monthly | Year in Recap ---
    tab_year, tab_month, tab_recap = st.tabs([
        "Per Year", "Per Month", "Year in Recap"
    ])

    with tab_year:
        _render_yearly_breakdown(by_year, api)

    with tab_month:
        _render_monthly_breakdown(by_month, api)

    with tab_recap:
        _render_year_in_recap(finished_books, by_year, by_month, total_time_hours, api)

    # --- Additional insights ---
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
        icols = st.columns(2)
        with icols[0]:
            st.metric("Books Listened To", total_items)
        with icols[1]:
            st.metric("Unique Authors", len(unique_authors))

    st.markdown("---")
    st.caption("Statistics update automatically as you listen")


# ---------------------------------------------------------------------------
# Yearly breakdown
# ---------------------------------------------------------------------------

def _render_yearly_breakdown(
    by_year: Dict[str, List[Dict[str, Any]]],
    api: AudiobookshelfAPI,
):
    if not by_year:
        st.info("No completed books yet.")
        return

    st.markdown("#### Books Completed Per Year")

    # Bar chart
    yearly_df = pd.DataFrame([
        {"Year": year, "Books": len(books)}
        for year, books in by_year.items()
    ])
    st.bar_chart(yearly_df.set_index("Year")["Books"], use_container_width=True)

    # Expandable list per year (most recent first)
    for year in reversed(list(by_year.keys())):
        books = by_year[year]
        with st.expander(f"{year} — {len(books)} book{'s' if len(books) != 1 else ''}", expanded=False):
            _render_book_list(books, api)


# ---------------------------------------------------------------------------
# Monthly breakdown
# ---------------------------------------------------------------------------

def _render_monthly_breakdown(
    by_month: Dict[str, List[Dict[str, Any]]],
    api: AudiobookshelfAPI,
):
    if not by_month:
        st.info("No completed books yet.")
        return

    st.markdown("#### Books Completed Per Month")

    # Line chart
    monthly_df = pd.DataFrame([
        {"Month": month, "Books": len(books)}
        for month, books in by_month.items()
    ])
    monthly_df['Label'] = monthly_df['Month'].apply(
        lambda x: datetime.strptime(x, "%Y-%m").strftime("%b %Y")
    )
    st.line_chart(monthly_df.set_index("Label")["Books"], use_container_width=True)

    # Expandable list per month (most recent first)
    for month in reversed(list(by_month.keys())):
        books = by_month[month]
        label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
        with st.expander(f"{label} — {len(books)} book{'s' if len(books) != 1 else ''}", expanded=False):
            _render_book_list(books, api)


# ---------------------------------------------------------------------------
# Book list rendering (shared)
# ---------------------------------------------------------------------------

def _render_book_list(books: List[Dict[str, Any]], api: AudiobookshelfAPI, page_size: int = 10):
    """Render a list of finished books with cover, title, author, and dates."""
    if len(books) > page_size:
        page_key = f"stats_bl_{id(books)}"
        total_pages = max(1, -(-len(books) // page_size))
        page = st.session_state.get(page_key, 1)
        page = min(page, total_pages)
        start = (page - 1) * page_size
        visible = books[start:start + page_size]

        if total_pages > 1:
            nav_cols = st.columns([1, 2, 1])
            with nav_cols[0]:
                if st.button("Previous", disabled=page <= 1, key=f"{page_key}_prev"):
                    st.session_state[page_key] = page - 1
                    st.rerun()
            with nav_cols[1]:
                st.markdown(
                    f"<div style='text-align:center;color:#a8a8a8;'>Page {page}/{total_pages}</div>",
                    unsafe_allow_html=True,
                )
            with nav_cols[2]:
                if st.button("Next", disabled=page >= total_pages, key=f"{page_key}_next"):
                    st.session_state[page_key] = page + 1
                    st.rerun()
    else:
        visible = books

    for book in visible:
        col_cover, col_info = st.columns([1, 4])
        with col_cover:
            cover_url = api.get_cover_url(book['library_item_id'])
            st.image(cover_url, width=80)
        with col_info:
            st.markdown(f"**{book['title']}**")
            st.markdown(f"{book['author']}")
            parts = []
            if book.get('finished_at'):
                parts.append(f"Finished: {format_date_short(book['finished_at'])}")
            dur_h = int(book.get('duration', 0) // 3600)
            dur_m = int((book.get('duration', 0) % 3600) // 60)
            if dur_h or dur_m:
                parts.append(f"Length: {dur_h}h {dur_m}m")
            if book.get('series'):
                series_names = ', '.join(
                    s.get('name', '') + (f" #{s.get('sequence', '')}" if s.get('sequence') else '')
                    for s in book['series']
                )
                if series_names:
                    parts.append(f"Series: {series_names}")
            if parts:
                st.caption(" · ".join(parts))
        st.markdown("")  # spacing


# ---------------------------------------------------------------------------
# Year in Recap (Spotify Wrapped–style)
# ---------------------------------------------------------------------------

def _render_year_in_recap(
    all_finished: List[Dict[str, Any]],
    by_year: Dict[str, List[Dict[str, Any]]],
    by_month: Dict[str, List[Dict[str, Any]]],
    total_time_hours: float,
    api: AudiobookshelfAPI,
):
    if not by_year:
        st.info("Complete some books to unlock your Year in Recap!")
        return

    years = sorted(by_year.keys(), reverse=True)
    selected_year = st.selectbox("Select Year", years, index=0)

    books = by_year.get(selected_year, [])
    if not books:
        st.info(f"No books completed in {selected_year}.")
        return

    st.markdown(f"#### Your {selected_year} in Books")

    # --- Hero stats ---
    year_hours = sum(b.get('time_listening', 0) for b in books) / 3600
    year_duration_hours = sum(b.get('duration', 0) for b in books) / 3600

    # Months with completions in this year
    year_months = [m for m in by_month if m.startswith(selected_year)]

    hero_cols = st.columns(4)
    with hero_cols[0]:
        _stat_card(str(len(books)), "Books Finished")
    with hero_cols[1]:
        _stat_card(f"{int(year_hours)}", "Hours Listened")
    with hero_cols[2]:
        _stat_card(f"{int(year_duration_hours)}", "Hours of Content")
    with hero_cols[3]:
        _stat_card(str(len(year_months)), "Active Months")

    st.markdown("---")

    # --- Top Authors ---
    author_counts = Counter(b['author'] for b in books)
    top_authors = author_counts.most_common(5)
    if top_authors:
        st.markdown("##### Top Authors")
        for rank, (author, count) in enumerate(top_authors, 1):
            st.markdown(f"**{rank}.** {author} — {count} book{'s' if count != 1 else ''}")

    st.markdown("---")

    # --- Longest & Shortest book ---
    books_with_dur = [b for b in books if b.get('duration', 0) > 0]
    if books_with_dur:
        col_long, col_short = st.columns(2)
        longest = max(books_with_dur, key=lambda b: b['duration'])
        shortest = min(books_with_dur, key=lambda b: b['duration'])

        with col_long:
            st.markdown("##### Longest Book")
            dur = longest['duration']
            st.markdown(f"**{longest['title']}**")
            st.markdown(f"{longest['author']}")
            st.caption(f"{int(dur // 3600)}h {int((dur % 3600) // 60)}m")

        with col_short:
            st.markdown("##### Shortest Book")
            dur = shortest['duration']
            st.markdown(f"**{shortest['title']}**")
            st.markdown(f"{shortest['author']}")
            st.caption(f"{int(dur // 3600)}h {int((dur % 3600) // 60)}m")

    st.markdown("---")

    # --- Fastest & Slowest read ---
    books_with_times = [
        b for b in books
        if b.get('started_at') and b.get('finished_at') and b['finished_at'] > b['started_at']
    ]
    if books_with_times:
        col_fast, col_slow = st.columns(2)

        def _read_days(b: Dict[str, Any]) -> float:
            return (b['finished_at'] - b['started_at']) / (1000 * 86400)

        fastest = min(books_with_times, key=_read_days)
        slowest = max(books_with_times, key=_read_days)

        with col_fast:
            st.markdown("##### Fastest Read")
            days = _read_days(fastest)
            st.markdown(f"**{fastest['title']}**")
            st.caption(f"Finished in {days:.0f} day{'s' if days != 1 else ''}")

        with col_slow:
            st.markdown("##### Slowest Read")
            days = _read_days(slowest)
            st.markdown(f"**{slowest['title']}**")
            st.caption(f"Took {days:.0f} day{'s' if days != 1 else ''}")

    st.markdown("---")

    # --- Monthly pace chart for this year ---
    st.markdown("##### Monthly Reading Pace")
    all_months_in_year = [f"{selected_year}-{m:02d}" for m in range(1, 13)]
    pace_data = []
    for m in all_months_in_year:
        label = datetime.strptime(m, "%Y-%m").strftime("%b")
        count = len(by_month.get(m, []))
        pace_data.append({"Month": label, "Books": count})
    pace_df = pd.DataFrame(pace_data)
    st.bar_chart(pace_df.set_index("Month")["Books"], use_container_width=True)

    st.markdown("---")

    # --- Top Genres ---
    genre_counts: Counter[str] = Counter()
    for b in books:
        for s in b.get('series', []):
            name = s.get('name')
            if name:
                genre_counts[name] += 1
    if genre_counts:
        st.markdown("##### Top Series")
        for rank, (name, count) in enumerate(genre_counts.most_common(5), 1):
            st.markdown(f"**{rank}.** {name} — {count} book{'s' if count != 1 else ''}")
        st.markdown("---")

    # --- Full book list for the year ---
    st.markdown(f"##### All Books — {selected_year}")
    _render_book_list(books, api)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _render_stat_css():
    st.markdown(
        '<style>'
        '.stat-card{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);'
        'border-radius:12px;padding:24px;margin-bottom:20px;'
        'box-shadow:0 4px 12px rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.05)}'
        '.stat-value{font-size:36px;font-weight:700;color:#4a9eff;margin-bottom:4px}'
        '.stat-label{font-size:14px;color:#a8a8a8;text-transform:uppercase;letter-spacing:1px}'
        '</style>',
        unsafe_allow_html=True,
    )


def _stat_card(value: str, label: str):
    st.markdown(
        f'<div class="stat-card">'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
