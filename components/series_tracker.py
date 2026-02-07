"""
Series progress tracker component.
Shows per-series completion using series metadata from Audiobookshelf.
"""

import math
import streamlit as st
from typing import Dict, List, Any

from api.audiobookshelf import AudiobookshelfAPI, AudiobookData
from config.config import config

import logging

logger = logging.getLogger(__name__)


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_series_data(base_url: str, token: str):
    """Fetch all library items and group them by series."""
    api = AudiobookshelfAPI(base_url, token)
    progress_map = api.get_media_progress_map()

    items = []
    for lib in api.get_libraries():
        items.extend(api.get_library_items(lib["id"]))

    # Group by series name
    series_map: Dict[str, Dict[str, Any]] = {}

    for item in items:
        metadata = AudiobookData.extract_metadata(item)
        raw_series = metadata.get("series", [])
        if not raw_series:
            continue

        progress_data = (
            progress_map.get(item.get("id", ""))
            or item.get("userMediaProgress")
            or item.get("mediaProgress")
            or {}
        )
        progress_info = AudiobookData.calculate_progress(
            progress_data, metadata["duration"]
        )

        for s in raw_series:
            series_name = s.get("name", "").strip()
            if not series_name:
                continue

            if series_name not in series_map:
                series_map[series_name] = {
                    "name": series_name,
                    "books": [],
                    "author": metadata["author"],
                }

            series_map[series_name]["books"].append({
                "id": metadata["id"],
                "title": metadata["title"],
                "author": metadata["author"],
                "sequence": s.get("sequence", ""),
                "is_finished": progress_info["is_finished"],
                "progress": progress_info["progress"],
                "duration": metadata["duration"],
                "cover_path": metadata.get("cover_path"),
            })

    # Sort books within each series by sequence number
    for series in series_map.values():
        series["books"].sort(key=lambda b: _parse_sequence(b["sequence"]))

    return series_map


def _parse_sequence(seq) -> float:
    """Parse a sequence string into a sortable number."""
    if not seq:
        return float("inf")
    try:
        return float(str(seq))
    except (ValueError, TypeError):
        return float("inf")


def render_series_tracker(api: AudiobookshelfAPI):
    """Render the series progress tracker view."""
    st.markdown("### Series Progress")

    with st.spinner("Loading series data..."):
        series_map = _fetch_series_data(api.base_url, api.token)

    if not series_map:
        st.info("No series found in your library.")
        return

    # Sort options
    sort_col, filter_col = st.columns([1, 1])
    with sort_col:
        sort_by = st.selectbox(
            "Sort by",
            ["Name (A-Z)", "Completion (%)", "Most Books"],
            key="series_sort",
            label_visibility="collapsed",
        )
    with filter_col:
        filter_mode = st.selectbox(
            "Filter",
            ["All Series", "In Progress", "Complete", "Not Started"],
            key="series_filter",
            label_visibility="collapsed",
        )

    # Compute stats for each series
    series_list = []
    for name, data in series_map.items():
        books = data["books"]
        total = len(books)
        finished = sum(1 for b in books if b["is_finished"])
        in_progress = sum(1 for b in books if not b["is_finished"] and b["progress"] > 0)
        not_started = total - finished - in_progress
        completion_pct = (finished / total * 100) if total > 0 else 0

        series_list.append({
            **data,
            "total": total,
            "finished": finished,
            "in_progress": in_progress,
            "not_started": not_started,
            "completion_pct": completion_pct,
        })

    # Filter
    if filter_mode == "In Progress":
        series_list = [s for s in series_list if 0 < s["completion_pct"] < 100]
    elif filter_mode == "Complete":
        series_list = [s for s in series_list if s["completion_pct"] == 100]
    elif filter_mode == "Not Started":
        series_list = [s for s in series_list if s["completion_pct"] == 0]

    # Sort
    if sort_by == "Name (A-Z)":
        series_list.sort(key=lambda s: s["name"].lower())
    elif sort_by == "Completion (%)":
        series_list.sort(key=lambda s: s["completion_pct"], reverse=True)
    elif sort_by == "Most Books":
        series_list.sort(key=lambda s: s["total"], reverse=True)

    if not series_list:
        st.info("No series match the current filter.")
        return

    st.caption(f"{len(series_list)} series found")

    # Render each series as an expandable card
    for series in series_list:
        completion = series["completion_pct"]
        status_emoji = ""
        if completion == 100:
            status_emoji = " ✓"
        elif completion > 0:
            status_emoji = ""

        header = (
            f"{series['name']} — {series['author']} "
            f"({series['finished']}/{series['total']}){status_emoji}"
        )

        with st.expander(header):
            # Series progress bar
            st.progress(
                min(completion / 100, 1.0),
                text=f"{completion:.0f}% complete — "
                     f"{series['finished']} finished, "
                     f"{series['in_progress']} in progress, "
                     f"{series['not_started']} not started",
            )

            # Book list
            for book in series["books"]:
                seq_label = f"#{book['sequence']} " if book["sequence"] else ""

                if book["is_finished"]:
                    icon = "✅"
                    status = "Finished"
                elif book["progress"] > 0:
                    icon = "📖"
                    status = f"{book['progress']:.0f}%"
                else:
                    icon = "📕"
                    status = "Not started"

                duration_str = AudiobookData.format_duration(book["duration"])
                st.markdown(
                    f"{icon} {seq_label}**{book['title']}** — {status} ({duration_str})"
                )
