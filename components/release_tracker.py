"""
Release Tracker component - track upcoming book releases from favorite authors.
Now with Open Library integration for automatic book lookup!
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from database.db import ReleaseTrackerDB
from api.audiobookshelf import AudiobookshelfAPI
from api.openlibrary import OpenLibraryAPI


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
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                                border-radius: 12px; padding: 20px; margin-bottom: 16px;
                                border: 2px solid #4a9eff;">
                        <h3 style="color: #4a9eff; margin-bottom: 8px;">
                            {release['book_title']}
                        </h3>
                        <p style="color: #a8a8a8; margin-bottom: 4px;">
                            by {release['author_name']}
                            {f" - {release['series_name']}" if release['series_name'] else ""}
                            {f" #{release['book_number']}" if release['book_number'] else ""}
                        </p>
                        <p style="color: #e8e8e8; font-size: 18px; margin-bottom: 4px;">
                            📅 {format_release_date(release['release_date'])}
                            {' ✓' if release['release_date_confirmed'] else ' (tentative)'}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if release.get('goodreads_url'):
                        st.link_button("Goodreads", release['goodreads_url'])
                with col2:
                    if release.get('amazon_url'):
                        st.link_button("Amazon", release['amazon_url'])
                with col3:
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
    
    # Display releases in a table-like format
    for release in filtered_releases:
        with st.expander(
            f"📖 {release['book_title']} - {format_release_date(release['release_date']) if release['release_date'] else 'TBD'}",
            expanded=st.session_state.get(f'edit_release_{release["id"]}', False)
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Author:** {release['author_name']}")
                if release['series_name']:
                    book_num = f"#{release['book_number']}" if release['book_number'] else ""
                    st.markdown(f"**Series:** {release['series_name']} {book_num}")
                if release['notes']:
                    st.markdown(f"**Notes:** {release['notes']}")
            
            with col2:
                if release['release_date']:
                    st.markdown(f"**Release:** {format_release_date(release['release_date'])}")
                    if release['release_date_confirmed']:
                        st.markdown("✅ Confirmed")
                    else:
                        st.markdown("⚠️ Tentative")
            
            # Links
            if release.get('goodreads_url') or release.get('amazon_url'):
                st.markdown("**Links:**")
                lcol1, lcol2 = st.columns(2)
                with lcol1:
                    if release.get('goodreads_url'):
                        st.link_button("📚 Goodreads", release['goodreads_url'], use_container_width=True)
                with lcol2:
                    if release.get('amazon_url'):
                        st.link_button("🛒 Amazon", release['amazon_url'], use_container_width=True)
            
            # Edit/Delete buttons
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                if st.button("✏️ Edit", key=f"edit_btn_{release['id']}", use_container_width=True):
                    show_edit_release_form(db, release)
            with ecol2:
                if st.button("🗑️ Delete", key=f"delete_{release['id']}", use_container_width=True):
                    db.delete_release(release['id'])
                    st.success("Release deleted!")
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
    
    # Search form
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
    
    # Search button
    if st.button("🔍 Search", type="primary", disabled=not search_query):
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
        )
        
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
        ol_url = st.text_input(
            "Open Library URL",
            value=f"https://openlibrary.org{book_info['work_key']}"
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
            # Add author if new
            if new_author:
                author_id = db.add_tracked_author(
                    new_author,
                    book_info['author_keys'][0] if book_info['author_keys'] else None
                )
            
            # Add series if new
            if use_series and series_name and not series_id:
                author_id_for_series = author_id if author_id else \
                    next((a['id'] for a in existing_authors if a['author_name'] == author_choice), None)
                if author_id_for_series:
                    series_id = db.add_tracked_series(series_name, author_id_for_series)
            
            # Add release
            db.add_release(
                book_title=book_title,
                author_id=author_id if author_id else \
                    next((a['id'] for a in existing_authors if a['author_name'] == author_choice), None),
                series_id=series_id if use_series else None,
                release_date=release_date.isoformat() if release_date else None,
                release_date_confirmed=date_confirmed,
                book_number=book_number if book_number else None,
                goodreads_url=goodreads_url if goodreads_url else None,
                amazon_url=amazon_url if amazon_url else None,
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
        goodreads_url = st.text_input("Goodreads URL (optional)", placeholder="https://www.goodreads.com/book/show/...")
        amazon_url = st.text_input("Amazon URL (optional)", placeholder="https://www.amazon.com/...")
        
        notes = st.text_area("Notes (optional)", placeholder="Additional information...")
        
        submitted = st.form_submit_button("Add Release", type="primary")
        
        if submitted:
            if not author_name or not book_title:
                st.error("Author name and book title are required!")
            else:
                # Add author if new
                if not author_id:
                    author_id = db.add_tracked_author(author_name)
                
                # Add series if new
                if use_series and series_name and not series_id:
                    series_id = db.add_tracked_series(series_name, author_id)
                
                # Add release
                db.add_release(
                    book_title=book_title,
                    author_id=author_id,
                    series_id=series_id if use_series else None,
                    release_date=release_date.isoformat() if release_date else None,
                    release_date_confirmed=date_confirmed,
                    book_number=book_number,
                    goodreads_url=goodreads_url if goodreads_url else None,
                    amazon_url=amazon_url if amazon_url else None,
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
                st.markdown(f"**Upcoming Releases:** {len(releases)}")

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
        
        book_number = st.text_input("Book Number", value=release['book_number'] or "")
        goodreads_url = st.text_input("Goodreads URL", value=release['goodreads_url'] or "")
        amazon_url = st.text_input("Amazon URL", value=release['amazon_url'] or "")
        notes = st.text_area("Notes", value=release['notes'] or "")
        
        if st.form_submit_button("Update Release"):
            db.update_release(
                release['id'],
                book_title=book_title,
                release_date=release_date.isoformat() if release_date else None,
                release_date_confirmed=int(date_confirmed),
                book_number=book_number if book_number else None,
                goodreads_url=goodreads_url if goodreads_url else None,
                amazon_url=amazon_url if amazon_url else None,
                notes=notes if notes else None
            )
            st.success("Release updated!")
            st.session_state[f'edit_release_{release["id"]}'] = False
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
    except:
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
