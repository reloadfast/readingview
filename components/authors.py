"""
Authors view component - browse authors from your library with bios and release tracking.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from api.audiobookshelf import AudiobookshelfAPI, AudiobookData
from api.openlibrary import OpenLibraryAPI
from database.db import ReleaseTrackerDB


def render_authors_view(
    api: AudiobookshelfAPI,
    db: Optional[ReleaseTrackerDB] = None,
):
    """
    Render the authors view.

    Args:
        api: Audiobookshelf API client
        db: Release tracker database (optional)
    """
    ol_api = OpenLibraryAPI()

    st.markdown("### Authors")

    # Gather authors from all libraries
    with st.spinner("Loading authors from your library..."):
        authors_map = _collect_authors(api)

    if not authors_map:
        st.info("No authors found in your library.")
        return

    sorted_names = sorted(authors_map.keys())

    # Check if an author is selected
    selected = st.session_state.get("selected_author")

    if selected and selected in authors_map:
        # Back button
        if st.button("Back to all authors"):
            st.session_state.pop("selected_author", None)
            st.rerun()

        author_data = authors_map[selected]
        _render_author_detail(selected, author_data, ol_api, api, db)
    else:
        # Show clickable author grid
        _render_author_grid(sorted_names, authors_map)


def _collect_authors(api: AudiobookshelfAPI) -> Dict[str, Dict[str, Any]]:
    """Extract unique authors and their books from the user's libraries."""
    authors: Dict[str, Dict[str, Any]] = {}

    libraries = api.get_libraries()
    for lib in libraries:
        items = api.get_library_items(lib["id"])
        for item in items:
            metadata = AudiobookData.extract_metadata(item)
            name = metadata.get("author", "Unknown Author")
            if not name or name == "Unknown Author":
                continue

            if name not in authors:
                authors[name] = {"books": [], "abs_author_id": None}

            authors[name]["books"].append(metadata)

            # Capture ABS author ID if available
            raw_authors = (
                item.get("media", {})
                .get("metadata", {})
                .get("authors", [])
            )
            if raw_authors and not authors[name]["abs_author_id"]:
                authors[name]["abs_author_id"] = raw_authors[0].get("id")

    return authors


def _render_author_grid(names: List[str], authors_map: Dict[str, Any]):
    """Show a clickable grid of all authors."""
    cols_per_row = 4
    for i in range(0, len(names), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(names):
                break
            name = names[idx]
            book_count = len(authors_map[name]["books"])
            with col:
                if st.button(
                    f"{name}\n{book_count} book{'s' if book_count != 1 else ''}",
                    key=f"author_{idx}",
                    use_container_width=True,
                ):
                    st.session_state["selected_author"] = name
                    st.rerun()

    st.caption(f"{len(names)} authors in your library")


def _render_author_detail(
    name: str,
    author_data: Dict[str, Any],
    ol_api: OpenLibraryAPI,
    api: AudiobookshelfAPI,
    db: Optional[ReleaseTrackerDB],
):
    """Render detailed author view with bio, photo, books, and tracking."""
    st.markdown("---")

    # Look up author on Open Library
    ol_author = _lookup_author(name, ol_api)

    # Layout: photo + info
    col_photo, col_info = st.columns([1, 3])

    with col_photo:
        photo_url = _get_author_photo_url(ol_author, ol_api)
        if photo_url:
            st.image(photo_url, width=180)
        else:
            st.markdown(
                '<div style="width:180px;height:240px;background:#16213e;'
                'border-radius:12px;display:flex;align-items:center;'
                'justify-content:center;color:#555;font-size:48px;">?</div>',
                unsafe_allow_html=True,
            )

    with col_info:
        st.markdown(f"## {name}")

        if ol_author:
            # Birth/death dates
            dates = []
            if ol_author.get("birth_date"):
                dates.append(f"Born: {ol_author['birth_date']}")
            if ol_author.get("death_date"):
                dates.append(f"Died: {ol_author['death_date']}")
            if dates:
                st.markdown(" | ".join(dates))

            # Biography
            bio = ol_author.get("bio")
            if bio:
                bio_text = bio if isinstance(bio, str) else bio.get("value", "")
                if bio_text:
                    if len(bio_text) > 600:
                        with st.expander("Biography", expanded=True):
                            st.markdown(bio_text)
                    else:
                        st.markdown(bio_text)

            # Links
            links = ol_author.get("links", [])
            if links:
                link_cols = st.columns(min(len(links), 4))
                for i, link in enumerate(links[:4]):
                    with link_cols[i]:
                        st.link_button(
                            link.get("title", "Link"),
                            link.get("url", "#"),
                            use_container_width=True,
                        )
        else:
            st.markdown("*No biography available from Open Library.*")

        # Track releases button
        if db:
            tracked = db.get_tracked_authors()
            already_tracked = any(
                a["author_name"].lower() == name.lower() for a in tracked
            )
            if already_tracked:
                st.success("Tracking this author's releases")
            else:
                if st.button("Track Releases", type="primary"):
                    ol_key = ol_author.get("key") if ol_author else None
                    db.add_tracked_author(name, ol_key)
                    st.success(f"Now tracking {name}!")
                    st.rerun()

    # Books in library
    st.markdown("---")
    st.markdown(f"#### Books in Your Library ({len(author_data['books'])})")

    books = author_data["books"]
    cols_per_row = 5
    for i in range(0, len(books), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(books):
                break
            book = books[idx]
            with col:
                cover_url = api.get_cover_url(book["id"])
                st.image(cover_url, width=120)
                st.markdown(
                    f'<div style="font-size:13px;color:#e8e8e8;font-weight:600;">'
                    f'{book["title"]}</div>',
                    unsafe_allow_html=True,
                )


def _lookup_author(name: str, ol_api: OpenLibraryAPI) -> Optional[Dict[str, Any]]:
    """Search Open Library for author details by name."""
    results = ol_api.search_books(author=name, limit=1)
    if not results:
        return None

    author_keys = results[0].get("author_key", [])
    if not author_keys:
        return None

    return ol_api.get_author_details(author_keys[0])


def _get_author_photo_url(
    ol_author: Optional[Dict[str, Any]], ol_api: OpenLibraryAPI
) -> Optional[str]:
    """Get author photo URL from Open Library data."""
    if not ol_author:
        return None

    # Try photos list
    photos = ol_author.get("photos", [])
    if photos:
        photo_id = photos[0]
        if photo_id and photo_id != -1:
            return f"{ol_api.COVERS_URL}/a/id/{photo_id}-M.jpg"

    # Try OLID-based URL
    key = ol_author.get("key", "")
    if key:
        olid = key.replace("/authors/", "")
        return f"{ol_api.COVERS_URL}/a/olid/{olid}-M.jpg"

    return None
