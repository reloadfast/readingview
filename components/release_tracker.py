"""
Release Tracker component - track upcoming book releases from favorite authors.
Now with Open Library integration for automatic book lookup!
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
from database.db import ReleaseTrackerDB
from api.audiobookshelf import AudiobookshelfAPI
from api.openlibrary import OpenLibraryAPI
from utils.helpers import sanitize_url


def render_release_tracker_view(api: AudiobookshelfAPI, db: ReleaseTrackerDB):
    """
    Render the release tracker view.
    
    Args:
        api: Audiobookshelf API client
        db: Release tracker database
    """
    # Initialize Open Library API
    ol_api = OpenLibraryAPI()
    
    st.markdown("### 📅 Release Tracker")
    st.markdown("Track upcoming releases from your favorite authors and series")
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📆 Upcoming Releases", "➕ Add Tracking", "⚙️ Manage"])
    
    with tab1:
        render_upcoming_releases(db)
    
    with tab2:
        render_add_tracking(api, db, ol_api)
    
    with tab3:
        render_manage_tracking(db)


def render_upcoming_releases(db: ReleaseTrackerDB):
    """Display upcoming book releases."""
    
    # Get upcoming releases
    releases = db.get_upcoming_releases(sort_by="release_date")
    
    if not releases:
        st.info("No upcoming releases tracked yet. Add authors or series in the 'Add Tracking' tab!")
        return
    
    # Next release highlight
    next_releases = db.get_next_releases(limit=3)
    if next_releases:
        st.markdown("#### 🎉 Coming Soon")
        
        for release in next_releases:
            with st.container():
                title_text = release['book_title']
                safe_link = sanitize_url(release.get('link_url'))
                if safe_link:
                    title_html = f'<a href="{safe_link}" target="_blank" style="color: #4a9eff; text-decoration: none;">{title_text}</a>'
                else:
                    title_html = title_text
                series_info = f" - {release['series_name']}" if release.get('series_name') else ""
                book_num = f" #{release['book_number']}" if release.get('book_number') else ""
                date_text = format_release_date(release['release_date'])
                confirmed = ' ✓' if release.get('release_date_confirmed') else ' (tentative)'
                st.markdown(
                    f'<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 2px solid #4a9eff;">'
                    f'<h3 style="color: #4a9eff; margin-bottom: 8px;">{title_html}</h3>'
                    f'<p style="color: #a8a8a8; margin-bottom: 4px;">by {release["author_name"]}{series_info}{book_num}</p>'
                    f'<p style="color: #e8e8e8; font-size: 18px; margin-bottom: 4px;">📅 {date_text}{confirmed}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Action buttons
                link_cols = []
                if release.get('link_url'):
                    link_cols.append(('link_url', 'Book Page', release['link_url']))
                if release.get('goodreads_url'):
                    link_cols.append(('goodreads', 'Goodreads', release['goodreads_url']))
                if release.get('amazon_url'):
                    link_cols.append(('amazon', 'Amazon', release['amazon_url']))

                btn_cols = st.columns(max(len(link_cols) + 1, 3))
                for i, (_, label, url) in enumerate(link_cols):
                    with btn_cols[i]:
                        st.link_button(label, url)
                with btn_cols[-1]:
                    if st.button("Edit", key=f"edit_next_{release['id']}"):
                        st.session_state[f'edit_release_{release["id"]}'] = True
        
        st.markdown("---")
    
    # All upcoming releases
    st.markdown("#### All Upcoming Releases")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        authors = db.get_tracked_authors()
        author_filter = st.selectbox(
            "Filter by Author",
            options=[{"id": None, "author_name": "All Authors"}] + authors,
            format_func=lambda x: x['author_name']
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Release Date", "Author Name", "Book Title"]
        )
    
    # Apply filters
    sort_map = {
        "Release Date": "release_date",
        "Author Name": "author_name",
        "Book Title": "book_title"
    }
    
    filtered_releases = db.get_upcoming_releases(
        author_id=author_filter['id'],
        sort_by=sort_map[sort_by]
    )
    
    # Paginate releases
    releases_per_page = 10
    total_release_pages = max(1, -(-len(filtered_releases) // releases_per_page))
    release_page = st.session_state.get("release_list_page", 1)
    release_page = min(release_page, total_release_pages)
    r_start = (release_page - 1) * releases_per_page
    r_end = min(r_start + releases_per_page, len(filtered_releases))
    page_releases = filtered_releases[r_start:r_end]

    # Display releases in a table-like format
    for release in page_releases:
        with st.expander(
            f"📖 {release['book_title']} - {format_release_date(release['release_date']) if release['release_date'] else 'TBD'}",
            expanded=st.session_state.get(f'edit_release_{release["id"]}', False)
        ):
            # Check if we should show the edit form
            if st.session_state.get(f'edit_release_{release["id"]}'):
                show_edit_release_form(db, release)
            else:
                col1, col2 = st.columns([2, 1])

                with col1:
                    if release.get('link_url'):
                        st.markdown(f"**Title:** [{release['book_title']}]({release['link_url']})")
                    st.markdown(f"**Author:** {release['author_name']}")
                    if release.get('series_name'):
                        book_num = f"#{release['book_number']}" if release.get('book_number') else ""
                        st.markdown(f"**Series:** {release['series_name']} {book_num}")
                    if release.get('notes'):
                        st.markdown(f"**Notes:** {release['notes']}")

                with col2:
                    if release.get('release_date'):
                        st.markdown(f"**Release:** {format_release_date(release['release_date'])}")
                        if release.get('release_date_confirmed'):
                            st.markdown("Confirmed")
                        else:
                            st.markdown("Tentative")

                # Links
                link_items = []
                if release.get('link_url'):
                    link_items.append(('Book Page', release['link_url']))
                if release.get('goodreads_url'):
                    link_items.append(('Goodreads', release['goodreads_url']))
                if release.get('amazon_url'):
                    link_items.append(('Amazon', release['amazon_url']))

                if link_items:
                    st.markdown("**Links:**")
                    lcols = st.columns(len(link_items))
                    for i, (label, url) in enumerate(link_items):
                        with lcols[i]:
                            st.link_button(label, url, use_container_width=True)

                # Edit/Delete buttons
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    if st.button("Edit", key=f"edit_btn_{release['id']}", use_container_width=True):
                        st.session_state[f'edit_release_{release["id"]}'] = True
                        st.rerun()
                with ecol2:
                    if st.button("Delete", key=f"delete_{release['id']}", use_container_width=True):
                        db.delete_release(release['id'])
                        st.success("Release deleted!")
                        st.rerun()

    # Pagination controls
    if total_release_pages > 1:
        nav_cols = st.columns([1, 2, 1])
        with nav_cols[0]:
            if st.button("Previous", disabled=release_page <= 1, key="release_prev"):
                st.session_state["release_list_page"] = release_page - 1
                st.rerun()
        with nav_cols[1]:
            st.markdown(
                f"<div style='text-align:center;color:#a8a8a8;'>Page {release_page} of {total_release_pages}</div>",
                unsafe_allow_html=True,
            )
        with nav_cols[2]:
            if st.button("Next", disabled=release_page >= total_release_pages, key="release_next"):
                st.session_state["release_list_page"] = release_page + 1
                st.rerun()


def render_add_tracking(api: AudiobookshelfAPI, db: ReleaseTrackerDB, ol_api: OpenLibraryAPI):
    """Add authors/series to track."""
    
    st.markdown("#### Add Authors or Series to Track")
    
    # Three options: From Audiobookshelf, Search Open Library, or Manual
    add_method = st.radio(
        "How would you like to add?",
        ["🔍 Search Open Library", "📚 From Your Audiobooks", "✍️ Manual Entry"],
        horizontal=True
    )
    
    if add_method == "🔍 Search Open Library":
        render_search_open_library(db, ol_api)
    elif add_method == "📚 From Your Audiobooks":
        render_add_from_audiobookshelf(api, db)
    else:
        render_manual_add(db)


def render_search_open_library(db: ReleaseTrackerDB, ol_api: OpenLibraryAPI):
    """Search and add books from Open Library."""
    
    st.markdown("Search the Open Library database for books to track")

    # Search form — wrapped in st.form so reruns only happen on submit
    with st.form("ol_search_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            search_query = st.text_input(
                "Search for a book",
                placeholder="e.g., Wind and Truth, Stormlight Archive, Brandon Sanderson",
                help="Search by title, author, or series name"
            )

        with col2:
            search_type = st.selectbox(
                "Search by",
                ["General", "Author", "Title", "Series"],
                help="Choose what you're searching for"
            )

        submitted = st.form_submit_button("Search", type="primary")

    if submitted and search_query:
        with st.spinner("Searching Open Library..."):
            # Perform search based on type
            if search_type == "Author":
                results = ol_api.search_books(author=search_query, limit=20)
            elif search_type == "Title":
                results = ol_api.search_books(title=search_query, limit=20)
            else:
                results = ol_api.search_books(query=search_query, limit=20)

            # Store results in session state
            st.session_state['ol_search_results'] = results
            st.session_state['search_query'] = search_query
    
    # Display results
    if 'ol_search_results' in st.session_state:
        results = st.session_state['ol_search_results']
        
        if not results:
            st.warning(f"No results found for '{st.session_state.get('search_query', '')}'")
            st.info("Try:\n- Simpler search terms\n- Different spelling\n- Author name only\n- Series name")
        else:
            st.success(f"Found {len(results)} result(s)")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                show_covers = st.checkbox("Show covers", value=True)
            with col2:
                results_to_show = st.slider("Results to display", 5, 20, 10)
            
            st.markdown("---")
            
            # Display each result
            for idx, book in enumerate(results[:results_to_show]):
                book_info = ol_api.extract_book_info(book)
                
                with st.container():
                    # Create columns for layout
                    if show_covers and book_info.get('cover_id'):
                        col_img, col_info = st.columns([1, 4])
                        with col_img:
                            cover_url = ol_api.get_cover_url(
                                cover_id=book_info['cover_id'],
                                size='M'
                            )
                            if cover_url:
                                st.image(cover_url, width=120)
                        content_col = col_info
                    else:
                        content_col = st.container()
                    
                    with content_col:
                        # Title and author
                        st.markdown(f"### {book_info['title']}")
                        
                        if book_info['author_names']:
                            authors = ', '.join(book_info['author_names'][:3])
                            st.markdown(f"**By:** {authors}")
                        
                        # Additional info
                        info_items = []
                        if book_info['first_publish_year']:
                            info_items.append(f"📅 First published: {book_info['first_publish_year']}")
                        if book_info['edition_count']:
                            info_items.append(f"📚 {book_info['edition_count']} edition(s)")
                        if book_info['language']:
                            info_items.append(f"🌐 Languages: {', '.join(book_info['language'][:3])}")
                        
                        if info_items:
                            st.markdown(" • ".join(info_items))
                        
                        # Action buttons
                        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                        
                        with col_btn1:
                            if st.button(
                                "➕ Add to Tracker",
                                key=f"add_ol_{idx}",
                                type="primary",
                                use_container_width=True
                            ):
                                # Show form to add release details
                                st.session_state[f'adding_book_{idx}'] = book_info
                                st.rerun()
                        
                        with col_btn2:
                            ol_url = ol_api.get_openlibrary_url(book_info['work_key'])
                            st.link_button(
                                "🔗 Open Library",
                                ol_url,
                                use_container_width=True
                            )
                        
                        # Show add form if button was clicked
                        if st.session_state.get(f'adding_book_{idx}'):
                            st.markdown("---")
                            render_add_from_open_library_result(
                                db,
                                book_info,
                                idx
                            )
                    
                    st.markdown("---")


def render_add_from_open_library_result(
    db: ReleaseTrackerDB,
    book_info: Dict[str, Any],
    idx: int
):
    """Show form to add a book from Open Library search results."""
    
    st.markdown("#### Add This Book to Tracker")
    
    with st.form(f"add_ol_book_{idx}"):
        # Pre-filled information
        st.info(f"📖 **{book_info['title']}** by {', '.join(book_info['author_names'][:2])}")
        
        # Author selection or new
        existing_authors = db.get_tracked_authors()
        
        # Try to match author
        author_match = None
        for author_name in book_info['author_names']:
            for existing in existing_authors:
                if author_name.lower() in existing['author_name'].lower() or \
                   existing['author_name'].lower() in author_name.lower():
                    author_match = existing
                    break
            if author_match:
                break
        
        if author_match:
            author_options = [author_match['author_name'], "<Create New Author>"] + \
                           [a['author_name'] for a in existing_authors if a['id'] != author_match['id']]
            default_idx = 0
        else:
            author_options = ["<Create New Author>"] + [a['author_name'] for a in existing_authors]
            default_idx = 0
        
        author_choice = st.selectbox(
            "Author",
            author_options,
            index=default_idx,
            help="Select existing author or create new"
        )
        
        if author_choice == "<Create New Author>":
            # Use first author from Open Library
            new_author = st.text_input(
                "Author Name",
                value=book_info['author_names'][0] if book_info['author_names'] else ""
            )
            author_id = None
        else:
            new_author = None
            author_id = next(
                (a['id'] for a in existing_authors if a['author_name'] == author_choice),
                None
            )
        
        # Series (optional) - try to detect from title
        use_series = st.checkbox(
            "Part of a series?",
            help="Is this book part of a series you're tracking?"
        )
        
        series_id = None
        series_name = None
        book_number = None
        
        if use_series:
            existing_series: list[Dict[str, Any]] = []
            if author_id:
                existing_series = db.get_tracked_series(author_id)
                series_options = ["<Create New Series>"] + \
                               [s['series_name'] for s in existing_series]
            else:
                series_options = ["<Create New Series>"]

            series_choice = st.selectbox("Series", series_options)

            if series_choice == "<Create New Series>":
                series_name = st.text_input(
                    "Series Name",
                    placeholder="e.g., The Stormlight Archive"
                )
            else:
                series_name = series_choice
                series_id = next(
                    (s['id'] for s in existing_series if s['series_name'] == series_name),
                    None
                )

            book_number = st.text_input(
                "Book Number in Series",
                placeholder="e.g., 5"
            )

        # Title (editable)
        book_title = st.text_input(
            "Book Title",
            value=book_info['title']
        ) or book_info['title']
        
        # Release information
        col1, col2 = st.columns(2)
        with col1:
            release_date = st.date_input(
                "Release Date",
                value=None,
                help="When is this book being released?"
            )
        with col2:
            date_confirmed = st.checkbox(
                "Date Confirmed?",
                help="Is this the official release date?"
            )
        
        # Links
        link_url = st.text_input(
            "Book Link URL",
            value=f"https://openlibrary.org{book_info['work_key']}",
            help="Clicking the book title will open this URL"
        )

        goodreads_url = st.text_input(
            "Goodreads URL (optional)",
            placeholder="https://www.goodreads.com/book/show/..."
        )

        amazon_url = st.text_input(
            "Amazon URL (optional)",
            placeholder="https://www.amazon.com/..."
        )
        
        # Notes
        notes = st.text_area(
            "Notes (optional)",
            placeholder="Additional information about this release..."
        )
        
        # Submit buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Add to Tracker", type="primary")
        with col2:
            cancelled = st.form_submit_button("❌ Cancel")
        
        if submitted:
            # Resolve author ID
            resolved_author_id: Optional[int] = author_id
            if new_author:
                resolved_author_id = db.add_tracked_author(
                    new_author,
                    book_info['author_keys'][0] if book_info['author_keys'] else None
                )
            if not resolved_author_id:
                resolved_author_id = next(
                    (a['id'] for a in existing_authors if a['author_name'] == author_choice), None
                )
            if not resolved_author_id:
                st.error("Could not resolve author.")
            else:
                # Add series if new
                if use_series and series_name and not series_id:
                    series_id = db.add_tracked_series(series_name, resolved_author_id)

                # Add release
                db.add_release(
                    book_title=book_title,
                    author_id=resolved_author_id,
                    series_id=series_id if use_series else None,
                    release_date=release_date.isoformat() if release_date else None,
                    release_date_confirmed=date_confirmed,
                    book_number=book_number if book_number else None,
                    link_url=sanitize_url(link_url),
                    goodreads_url=sanitize_url(goodreads_url),
                    amazon_url=sanitize_url(amazon_url),
                    notes=notes if notes else None,
                    source="openlibrary"
                )
            
            st.success(f"✅ Added '{book_title}' to tracker!")
            # Clear the form state
            if f'adding_book_{idx}' in st.session_state:
                del st.session_state[f'adding_book_{idx}']
            st.rerun()
        
        if cancelled:
            if f'adding_book_{idx}' in st.session_state:
                del st.session_state[f'adding_book_{idx}']
            st.rerun()


def render_add_from_audiobookshelf(api: AudiobookshelfAPI, db: ReleaseTrackerDB):
    """Add tracking from user's Audiobookshelf library."""
    
    st.markdown("Select authors from your library to track:")
    
    # Get user's items
    with st.spinner("Loading your audiobooks..."):
        items = api.get_user_items_in_progress()
        if not items:
            for lib in api.get_libraries():
                items.extend(api.get_library_items(lib['id']))
    
    if not items:
        st.warning("No audiobooks found in your library.")
        return
    
    # Extract unique authors and series
    authors = {}
    series_by_author = {}
    
    for item in items:
        media = item.get('media', {})
        metadata = media.get('metadata', {})
        
        author_name = metadata.get('authorName', 'Unknown Author')
        if author_name and author_name != 'Unknown Author':
            authors[author_name] = item.get('media', {}).get('metadata', {}).get('authors', [{}])[0].get('id')
        
        # Series
        series_list = metadata.get('series', [])
        for series in series_list:
            series_name = series.get('name')
            if series_name and author_name:
                if author_name not in series_by_author:
                    series_by_author[author_name] = {}
                series_by_author[author_name][series_name] = series.get('id')
    
    # Author selection
    selected_authors = st.multiselect(
        "Select Authors to Track",
        options=sorted(authors.keys()),
        help="These authors appear in your library"
    )
    
    # Series selection
    selected_series = {}
    if selected_authors:
        for author in selected_authors:
            if author in series_by_author:
                st.markdown(f"**Series by {author}:**")
                series_list = list(series_by_author[author].keys())
                selected = st.multiselect(
                    f"Track series by {author}",
                    options=series_list,
                    key=f"series_{author}",
                    label_visibility="collapsed"
                )
                if selected:
                    selected_series[author] = selected
    
    # Add button
    if st.button("Add to Tracker", type="primary", disabled=not selected_authors):
        # Add authors
        for author in selected_authors:
            author_id = db.add_tracked_author(author, authors.get(author))
            
            # Add series if selected
            if author in selected_series:
                for series_name in selected_series[author]:
                    series_id = series_by_author[author].get(series_name)
                    db.add_tracked_series(series_name, author_id, series_id)
        
        st.success(f"Added {len(selected_authors)} author(s) to tracker!")
        
        # Prompt to add release info
        st.info("Now add upcoming release information in the 'Upcoming Releases' tab!")
        st.rerun()


def render_manual_add(db: ReleaseTrackerDB):
    """Manually add authors and releases."""
    
    st.markdown("**Add New Release Manually**")
    st.info("💡 **Tip**: Try the '🔍 Search Open Library' option above for automatic book lookup!")
    
    with st.form("manual_add_form"):
        
        # Author selection or new
        existing_authors = db.get_tracked_authors()
        author_options = ["<Create New Author>"] + [a['author_name'] for a in existing_authors]
        
        author_choice = st.selectbox("Author", author_options)
        
        if author_choice == "<Create New Author>":
            author_name = st.text_input("Author Name", placeholder="e.g., Brandon Sanderson")
            author_id = None
        else:
            author_name = author_choice
            author_id = next((a['id'] for a in existing_authors if a['author_name'] == author_name), None)
        
        # Series (optional)
        use_series = st.checkbox("Part of a series?")
        series_id = None
        series_name: Optional[str] = None
        book_number = None

        if use_series:
            existing_series: list[Dict[str, Any]] = []
            if author_id:
                existing_series = db.get_tracked_series(author_id)
                series_options = ["<Create New Series>"] + [s['series_name'] for s in existing_series]
            else:
                series_options = ["<Create New Series>"]

            series_choice = st.selectbox("Series", series_options)

            if series_choice == "<Create New Series>":
                series_name = st.text_input("Series Name", placeholder="e.g., Stormlight Archive")
            else:
                series_name = series_choice
                series_id = next((s['id'] for s in existing_series if s['series_name'] == series_name), None)

            book_number = st.text_input("Book Number", placeholder="e.g., 5")
        
        # Book details
        book_title = st.text_input("Book Title", placeholder="e.g., Wind and Truth")
        
        # Helper: Quick search link
        if book_title and author_name:
            search_author = author_name
            search_query = f"{book_title} {search_author}".replace(" ", "+")
            ol_search_url = f"https://openlibrary.org/search?q={search_query}"
            st.markdown(
                f"🔗 [Search Open Library for this book]({ol_search_url})",
                help="Opens Open Library in new tab to help you find book details"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            release_date = st.date_input("Release Date (if known)", value=None)
        with col2:
            date_confirmed = st.checkbox("Date Confirmed?")
        
        # Links
        link_url = st.text_input("Book Link URL (optional)", placeholder="https://...", help="Clicking the book title will open this URL")
        goodreads_url = st.text_input("Goodreads URL (optional)", placeholder="https://www.goodreads.com/book/show/...")
        amazon_url = st.text_input("Amazon URL (optional)", placeholder="https://www.amazon.com/...")

        notes = st.text_area("Notes (optional)", placeholder="Additional information...")

        submitted = st.form_submit_button("Add Release", type="primary")

        if submitted:
            if not author_name or not book_title:
                st.error("Author name and book title are required!")
            else:
                # Add author if new
                resolved_author_id: int = author_id if author_id else db.add_tracked_author(author_name)

                # Add series if new
                if use_series and series_name and not series_id:
                    series_id = db.add_tracked_series(series_name, resolved_author_id)

                # Add release
                db.add_release(
                    book_title=book_title,
                    author_id=resolved_author_id,
                    series_id=series_id if use_series else None,
                    release_date=release_date.isoformat() if release_date else None,
                    release_date_confirmed=date_confirmed,
                    book_number=book_number,
                    link_url=sanitize_url(link_url),
                    goodreads_url=sanitize_url(goodreads_url),
                    amazon_url=sanitize_url(amazon_url),
                    notes=notes if notes else None
                )
                
                st.success(f"Added '{book_title}' to tracker!")
                # Offer to add another release for the same author
                st.session_state['manual_add_last_author'] = author_name
                st.rerun()

    # After form: prompt to add another for same author
    last_author = st.session_state.pop('manual_add_last_author', None)
    if last_author:
        st.info(f"Add another release for **{last_author}**? Select them above and fill in the form again.")


def render_manage_tracking(db: ReleaseTrackerDB):
    """Manage tracked authors and series."""
    
    st.markdown("#### Manage Tracked Authors & Series")
    
    # Get tracked authors
    authors = db.get_tracked_authors()
    
    if not authors:
        st.info("No tracked authors yet. Add some in the 'Add Tracking' tab!")
        return
    
    for author in authors:
        with st.expander(f"📝 {author['author_name']}", expanded=False):
            # Get series for this author
            series = db.get_tracked_series(author['id'])
            
            if series:
                st.markdown("**Tracked Series:**")
                for s in series:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"- {s['series_name']}")
                    with col2:
                        if st.button("Remove", key=f"remove_series_{s['id']}"):
                            db.conn.cursor().execute(
                                'UPDATE tracked_series SET is_active = 0 WHERE id = ?',
                                (s['id'],)
                            )
                            db.conn.commit()
                            st.rerun()
            
            # Get releases for this author
            releases = db.get_upcoming_releases(author_id=author['id'])
            if releases:
                st.markdown(f"**Tracked Releases ({len(releases)}):**")
                for rel in releases:
                    r_col1, r_col2, r_col3 = st.columns([3, 1, 1])
                    with r_col1:
                        title_display = rel['book_title']
                        if rel.get('link_url'):
                            title_display = f"[{title_display}]({rel['link_url']})"
                        date_display = format_release_date(rel['release_date']) if rel.get('release_date') else 'TBD'
                        st.markdown(f"{title_display} — {date_display}")
                    with r_col2:
                        if st.button("Edit", key=f"manage_edit_rel_{rel['id']}", use_container_width=True):
                            st.session_state[f'manage_edit_release_{rel["id"]}'] = True
                            st.rerun()
                    with r_col3:
                        if st.button("Delete", key=f"manage_del_rel_{rel['id']}", use_container_width=True):
                            db.delete_release(rel['id'])
                            st.success(f"Deleted '{rel['book_title']}'")
                            st.rerun()
                    # Inline edit form
                    if st.session_state.get(f'manage_edit_release_{rel["id"]}'):
                        show_edit_release_form(db, rel)
            else:
                st.markdown("*No releases tracked yet.*")

            # Add release for this author
            if st.button(
                f"Add Release for {author['author_name']}",
                key=f"add_release_{author['id']}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state['manage_add_release_author'] = author
                st.rerun()

            # Inline add-release form
            if st.session_state.get('manage_add_release_author', {}).get('id') == author['id']:
                _render_quick_add_release(db, author)

            # Remove author button
            if st.button(f"Remove {author['author_name']}", key=f"remove_author_{author['id']}"):
                db.remove_tracked_author(author['id'])
                st.success(f"Removed {author['author_name']} from tracking")
                st.rerun()


def show_edit_release_form(db: ReleaseTrackerDB, release: Dict[str, Any]):
    """Show inline edit form for a release."""
    
    with st.form(f"edit_form_{release['id']}"):
        book_title = st.text_input("Book Title", value=release['book_title'])

        col1, col2 = st.columns(2)
        with col1:
            current_date = datetime.strptime(release['release_date'], '%Y-%m-%d').date() if release['release_date'] else None
            release_date = st.date_input("Release Date", value=current_date)
        with col2:
            date_confirmed = st.checkbox("Confirmed?", value=bool(release['release_date_confirmed']))

        book_number = st.text_input("Book Number", value=release.get('book_number') or "")
        link_url = st.text_input("Book Link URL", value=release.get('link_url') or "", help="Clicking the book title will open this URL")
        goodreads_url = st.text_input("Goodreads URL", value=release.get('goodreads_url') or "")
        amazon_url = st.text_input("Amazon URL", value=release.get('amazon_url') or "")
        notes = st.text_area("Notes", value=release.get('notes') or "")

        col_save, col_cancel = st.columns(2)
        with col_save:
            save_clicked = st.form_submit_button("Update Release", type="primary")
        with col_cancel:
            cancel_clicked = st.form_submit_button("Cancel")

        if save_clicked:
            db.update_release(
                release['id'],
                book_title=book_title,
                release_date=release_date.isoformat() if release_date else None,
                release_date_confirmed=int(date_confirmed),
                book_number=book_number if book_number else None,
                link_url=sanitize_url(link_url),
                goodreads_url=sanitize_url(goodreads_url),
                amazon_url=sanitize_url(amazon_url),
                notes=notes if notes else None
            )
            st.success("Release updated!")
            st.session_state[f'edit_release_{release["id"]}'] = False
            st.session_state.pop(f'manage_edit_release_{release["id"]}', None)
            st.rerun()
        if cancel_clicked:
            st.session_state[f'edit_release_{release["id"]}'] = False
            st.session_state.pop(f'manage_edit_release_{release["id"]}', None)
            st.rerun()


def format_release_date(date_str: Optional[str]) -> str:
    """Format release date for display."""
    if not date_str:
        return "TBD"
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Calculate days until release
        today = datetime.now()
        days_until = (date_obj - today).days
        
        formatted = date_obj.strftime('%B %d, %Y')
        
        if days_until < 0:
            return f"{formatted} (Past)"
        elif days_until == 0:
            return f"{formatted} (TODAY!)"
        elif days_until <= 7:
            return f"{formatted} (In {days_until} days!)"
        elif days_until <= 30:
            return f"{formatted} (In {days_until} days)"
        else:
            return formatted
    except (ValueError, TypeError):
        return date_str


def _render_quick_add_release(db: ReleaseTrackerDB, author: Dict[str, Any]):
    """Inline form to quickly add a release for a specific author."""
    with st.form(f"quick_add_{author['id']}"):
        st.markdown(f"**New release for {author['author_name']}**")

        book_title = st.text_input("Book Title", key=f"qa_title_{author['id']}")

        col1, col2 = st.columns(2)
        with col1:
            release_date = st.date_input(
                "Release Date (if known)", value=None, key=f"qa_date_{author['id']}"
            )
        with col2:
            date_confirmed = st.checkbox("Confirmed?", key=f"qa_conf_{author['id']}")

        link_url = st.text_input("Book Link URL (optional)", key=f"qa_link_{author['id']}")
        notes = st.text_input("Notes (optional)", key=f"qa_notes_{author['id']}")

        col_sub, col_cancel = st.columns(2)
        with col_sub:
            submitted = st.form_submit_button("Add Release", type="primary")
        with col_cancel:
            cancelled = st.form_submit_button("Cancel")

        if submitted and book_title:
            db.add_release(
                book_title=book_title,
                author_id=author['id'],
                release_date=release_date.isoformat() if release_date else None,
                release_date_confirmed=date_confirmed,
                link_url=sanitize_url(link_url),
                notes=notes if notes else None,
            )
            st.session_state.pop('manage_add_release_author', None)
            st.success(f"Added '{book_title}'!")
            st.rerun()
        elif submitted:
            st.error("Book title is required.")

        if cancelled:
            st.session_state.pop('manage_add_release_author', None)
            st.rerun()
