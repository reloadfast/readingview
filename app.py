"""
ReadingView - Audiobook Statistics Dashboard
Main application entry point.
"""

import io
import os
import tarfile
import logging
import traceback
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from config import config

logger = logging.getLogger(__name__)
from api.audiobookshelf import AudiobookshelfAPI
from components.library import render_library_view, render_in_progress_view, trigger_library_dialogs
from components.statistics import render_statistics_view
from components.release_tracker import render_release_tracker_view
from components.authors import render_authors_view
from components.notifications import render_notification_settings, render_notification_status_badge
from components.dashboard import render_dashboard
from components.narrators import render_narrators_view
from components.collections import render_collections_view
from database.db import ReleaseTrackerDB
from utils.helpers import display_error
from components.recommendations import render_recommendations_view
from components.series_tracker import render_series_tracker


# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def apply_custom_theme():
    """Apply custom CSS theme to the application."""
    st.markdown("""
        <style>
        /* Import Google Fonts - Distinctive typography */
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Playfair+Display:wght@600;700&display=swap');

        /* Main theme */
        .stApp {
            background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 100%);
        }

        /* Header styling */
        h1 {
            font-family: 'Playfair Display', serif;
            font-weight: 700;
            color: #e8e8e8;
            letter-spacing: -0.5px;
        }

        h2, h3, h4 {
            font-family: 'Space Mono', monospace;
            color: #e8e8e8;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #16213e 0%, #1a1a2e 100%);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: transparent;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 12px 24px;
            font-family: 'Space Mono', monospace;
            font-weight: 700;
            color: #a8a8a8;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #4a9eff 0%, #7b68ee 100%);
            color: white;
            border: 1px solid transparent;
        }

        /* Buttons */
        .stButton button {
            background: linear-gradient(135deg, #4a9eff 0%, #7b68ee 100%);
            color: white;
            font-family: 'Space Mono', monospace;
            font-weight: 700;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
        }

        .stButton button:hover {
            background: linear-gradient(135deg, #5aa9ff 0%, #8b78fe 100%);
            transform: translateY(-2px);
        }

        /* Selectbox */
        .stSelectbox label {
            font-family: 'Space Mono', monospace;
            color: #a8a8a8;
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-family: 'Space Mono', monospace;
            font-size: 32px;
            color: #4a9eff;
        }

        /* Info/Error boxes */
        .stAlert {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Charts */
        [data-testid="stArrowVegaLiteChart"] {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            padding: 16px;
        }

        /* Expander */
        .streamlit-expanderHeader {
            font-family: 'Space Mono', monospace;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* QOL-10: Responsive grid for mobile/tablet */
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                min-width: calc(50% - 1rem) !important;
                flex: 0 0 calc(50% - 1rem) !important;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 8px 12px;
                font-size: 12px;
            }
        }
        @media (min-width: 641px) and (max-width: 1024px) {
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                min-width: calc(33.33% - 1rem) !important;
                flex: 0 0 calc(33.33% - 1rem) !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)


def show_configuration_guide():
    """Display configuration guide when app is not configured."""
    st.title("Configuration Required")

    st.markdown("""
    Welcome to **ReadingView**! To get started, you need to configure your Audiobookshelf connection.

    ### Required Configuration

    Create a `.env` file in the project directory with:
    """)

    st.code("""
ABS_URL=https://your-audiobookshelf-url
ABS_TOKEN=your_api_token
    """, language="bash")

    st.markdown("""
    ### Getting Your API Token

    1. Log into your Audiobookshelf instance
    2. Go to **Settings** → **Users**
    3. Click on your user
    4. Generate a new **API token**
    5. Copy the token and paste it in your `.env` file

    ### Docker Example

    If running in Docker, pass environment variables like this:
    """)

    st.code("""
docker run -d \\
  --name readingview \\
  -p 8506:8506 \\
  -e ABS_URL=https://your-audiobookshelf-url \\
  -e ABS_TOKEN=your_api_token \\
  readingview:latest
    """, language="bash")

    st.markdown("""
    ### Docker Compose Example
    """)

    st.code("""
version: '3.8'
services:
  readingview:
    image: readingview:latest
    container_name: readingview
    ports:
      - "8506:8506"
    environment:
      - ABS_URL=https://your-audiobookshelf-url
      - ABS_TOKEN=your_api_token
    restart: unless-stopped
    """, language="yaml")

    st.info("After creating the `.env` file, restart the application.")


# ---------------------------------------------------------------------------
# DATA-2: Database integrity check
# ---------------------------------------------------------------------------

def _check_db_integrity(db: ReleaseTrackerDB, label: str) -> bool:
    """Run integrity check on a database. Returns True if ok."""
    try:
        ok, msg = db.check_integrity()
        if not ok:
            logger.error("Database integrity check failed for %s: %s", label, msg)
            st.warning(
                f"Database integrity issue detected ({label}): {msg}. "
                f"Consider restoring from a backup."
            )
        return ok
    except Exception as e:
        logger.error("Integrity check error for %s: %s", label, e)
        return False


# ---------------------------------------------------------------------------
# DATA-1: Backup and restore
# ---------------------------------------------------------------------------

def _render_backup_restore():
    """Render backup and restore UI in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Data")

    # Backup
    if st.sidebar.button("Backup Databases", use_container_width=True):
        db_paths = []
        rt_path = Path(config.DB_PATH)
        if rt_path.exists():
            db_paths.append(rt_path)
        rec_path_str = os.getenv("BOOK_RECOMMENDER_DB_PATH", "/app/data/book_recommender.db")
        rec_path = Path(rec_path_str)
        if rec_path.exists():
            db_paths.append(rec_path)

        if not db_paths:
            st.sidebar.warning("No databases found to back up.")
        else:
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w:gz") as tar:
                for p in db_paths:
                    tar.add(str(p), arcname=p.name)
            buf.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.sidebar.download_button(
                label="Download Backup",
                data=buf,
                file_name=f"readingview_backup_{timestamp}.tar.gz",
                mime="application/gzip",
                use_container_width=True,
            )

    # Restore
    uploaded = st.sidebar.file_uploader(
        "Restore from backup",
        type=["gz", "tar.gz", "tgz"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        if st.sidebar.button("Restore", type="primary", use_container_width=True):
            try:
                buf = io.BytesIO(uploaded.read())
                with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                    # Validate: only allow known filenames
                    allowed = {"release_tracker.db", "book_recommender.db"}
                    members = tar.getmembers()
                    for m in members:
                        if m.name not in allowed:
                            st.sidebar.error(f"Unexpected file in archive: {m.name}")
                            return
                    # Extract to data dir
                    data_dir = Path(config.DB_PATH).parent
                    data_dir.mkdir(parents=True, exist_ok=True)
                    tar.extractall(path=str(data_dir), members=members)
                st.sidebar.success("Restored! Restart the app to load the new data.")
            except Exception as e:
                st.sidebar.error(f"Restore failed: {e}")


# ---------------------------------------------------------------------------
# QOL-11: Sidebar
# ---------------------------------------------------------------------------

def _render_sidebar(api: AudiobookshelfAPI, db, tab_names: list[str]):
    """Populate the sidebar with quick navigation and tools."""
    with st.sidebar:
        st.markdown(f"### {config.APP_TITLE}")

        # Quick nav links
        st.markdown("#### Quick Navigation")
        for i, name in enumerate(tab_names):
            if st.button(name, key=f"sidebar_nav_{i}", use_container_width=True):
                st.session_state["_rv_active_tab"] = i
                st.rerun()

        # Mini search
        st.markdown("---")
        sidebar_search = st.text_input(
            "Quick Search",
            placeholder="Search books...",
            key="sidebar_search",
        )
        if sidebar_search:
            st.session_state["lib_search"] = sidebar_search
            st.session_state["_rv_active_tab"] = 1  # Library tab
            st.rerun()

        # Notification badge
        if db:
            render_notification_status_badge()

        # Backup/Restore
        _render_backup_restore()


def main():
    """Main application function."""

    # Apply custom theme
    apply_custom_theme()

    # Check configuration
    is_valid, error_msg = config.validate()

    if not is_valid:
        show_configuration_guide()
        return

    # Initialize API client
    try:
        api = AudiobookshelfAPI(config.ABS_URL, config.ABS_TOKEN)
    except Exception as e:
        display_error("Failed to initialize API client", str(e))
        return

    # Test connection
    with st.spinner("Connecting to Audiobookshelf..."):
        if not api.test_connection():
            display_error(
                "Failed to connect to Audiobookshelf",
                f"Please check your ABS_URL ({config.ABS_URL}) and ABS_TOKEN configuration."
            )
            return

    # Header
    st.title(f"📚 {config.APP_TITLE}")
    st.markdown("Your personal audiobook statistics dashboard")
    st.markdown("---")

    # Initialize database for release tracker
    db = None
    if config.ENABLE_RELEASE_TRACKER:
        try:
            db = ReleaseTrackerDB(db_path=Path(config.DB_PATH))
            # DATA-2: Integrity check on startup (cached in session_state)
            if "_db_integrity_checked" not in st.session_state:
                _check_db_integrity(db, "release_tracker.db")
                st.session_state["_db_integrity_checked"] = True
        except Exception as e:
            st.warning(f"Release tracker unavailable: {e}")

    # Check recommender DB integrity too
    if config.has_book_recommender() and "_rec_db_integrity_checked" not in st.session_state:
        try:
            rec_path = os.getenv("BOOK_RECOMMENDER_DB_PATH", "/app/data/book_recommender.db")
            if Path(rec_path).exists():
                import sqlite3
                conn = sqlite3.connect(rec_path)
                result = conn.execute("PRAGMA integrity_check").fetchone()
                if result and result[0] != "ok":
                    logger.error("Recommender DB integrity issue: %s", result[0])
                    st.warning(f"Recommender database integrity issue: {result[0]}")
                conn.close()
            st.session_state["_rec_db_integrity_checked"] = True
        except Exception as e:
            logger.error("Recommender DB integrity check error: %s", e)
            st.session_state["_rec_db_integrity_checked"] = True

    # Trigger recommender dialogs once (before tabs to avoid duplicate IDs)
    trigger_library_dialogs()

    # Build tab list dynamically
    tab_names = [
        "🏠 Dashboard",
        "📚 Library",
        "📖 In Progress",
        "📊 Statistics",
        "👤 Authors",
        "🎙️ Narrators",
        "📖 Series",
    ]
    if db:
        tab_names.append("📂 Collections")
    if config.ENABLE_RELEASE_TRACKER and db:
        tab_names.append("📅 Release Tracker")
        tab_names.append("🔔 Notifications")
    if config.has_book_recommender():
        tab_names.append("💡 Recommendations")

    # QOL-11: Sidebar
    _render_sidebar(api, db, tab_names)

    # QOL-12: Remember last-visited tab
    if "_rv_active_tab" not in st.session_state:
        st.session_state["_rv_active_tab"] = 0

    # Navigate to Authors tab when requested from Library cards
    if st.session_state.pop("navigate_to_authors", False):
        # Authors is at index 4
        st.session_state["_rv_active_tab"] = 4

    # Clamp active tab to valid range
    active_tab = st.session_state["_rv_active_tab"]
    if active_tab >= len(tab_names):
        active_tab = 0
        st.session_state["_rv_active_tab"] = 0

    tabs = st.tabs(tab_names)

    # Use JS to switch to the remembered tab
    if active_tab > 0:
        components.html(f"""
            <script>
                const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs.length > {active_tab}) tabs[{active_tab}].click();
            </script>
        """, height=0)

    tab_index = 0

    def _safe_render(tab, name: str, fn, *args, **kwargs):
        """Wrap a tab render function with an error boundary."""
        with tab:
            try:
                fn(*args, **kwargs)
            except Exception as e:
                logger.error("Error rendering %s tab:\n%s", name, traceback.format_exc())
                st.error(f"Something went wrong loading the {name} tab.")
                with st.expander("Error details"):
                    st.code(traceback.format_exc())

    # Dashboard (QOL-8)
    _safe_render(tabs[tab_index], "Dashboard", render_dashboard, api, db)
    tab_index += 1

    _safe_render(tabs[tab_index], "Library", render_library_view, api, db)
    tab_index += 1

    _safe_render(tabs[tab_index], "In Progress", render_in_progress_view, api, db)
    tab_index += 1

    _safe_render(tabs[tab_index], "Statistics", render_statistics_view, api)
    tab_index += 1

    with tabs[tab_index]:
        try:
            if config.ENABLE_RELEASE_TRACKER and db:
                render_authors_view(api, db)
            else:
                render_authors_view(api)
        except Exception as e:
            logger.error("Error rendering Authors tab:\n%s", traceback.format_exc())
            st.error("Something went wrong loading the Authors tab.")
            with st.expander("Error details"):
                st.code(traceback.format_exc())
    tab_index += 1

    # Narrators (FUNC-11)
    _safe_render(tabs[tab_index], "Narrators", render_narrators_view, api)
    tab_index += 1

    _safe_render(tabs[tab_index], "Series", render_series_tracker, api)
    tab_index += 1

    # Collections (FUNC-15)
    if db:
        _safe_render(tabs[tab_index], "Collections", render_collections_view, api, db)
        tab_index += 1

    if config.ENABLE_RELEASE_TRACKER and db:
        _safe_render(tabs[tab_index], "Release Tracker", render_release_tracker_view, api, db)
        tab_index += 1
        _safe_render(tabs[tab_index], "Notifications", render_notification_settings, db)
        tab_index += 1

    if config.has_book_recommender():
        _safe_render(tabs[tab_index], "Recommendations", render_recommendations_view)
        tab_index += 1

    # QOL-12: Track which tab the user clicks via JS
    components.html("""
        <script>
        (function() {
            const doc = window.parent.document;
            if (doc._rvTabTracker) return;
            doc._rvTabTracker = true;
            doc.addEventListener('click', function(e) {
                const tab = e.target.closest('button[data-baseweb="tab"]');
                if (!tab) return;
                const tabs = Array.from(doc.querySelectorAll('button[data-baseweb="tab"]'));
                const idx = tabs.indexOf(tab);
                if (idx >= 0) {
                    // Store in URL params so Streamlit can read it
                    try {
                        const url = new URL(window.parent.location);
                        url.searchParams.set('tab', idx);
                        window.parent.history.replaceState({}, '', url);
                    } catch(e) {}
                }
            });
            // On load, read tab from URL
            try {
                const url = new URL(window.parent.location);
                const t = url.searchParams.get('tab');
                if (t !== null) {
                    const idx = parseInt(t);
                    const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
                    if (!isNaN(idx) && tabs.length > idx) tabs[idx].click();
                }
            } catch(e) {}
        })();
        </script>
    """, height=0)

    # Keyboard shortcuts: 1-9 switch tabs, / focuses search, Esc closes dialogs
    components.html("""
        <script>
        (function() {
            const doc = window.parent.document;
            if (doc._rvShortcuts) return;
            doc._rvShortcuts = true;
            doc.addEventListener('keydown', function(e) {
                const tag = (e.target.tagName || '').toLowerCase();
                const inInput = (tag === 'input' || tag === 'textarea' || e.target.isContentEditable);
                // Number keys 1-9: switch tabs (only when not typing)
                if (!inInput && !e.ctrlKey && !e.metaKey && !e.altKey) {
                    const num = parseInt(e.key);
                    if (num >= 1 && num <= 9) {
                        const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
                        if (tabs.length >= num) {
                            e.preventDefault();
                            tabs[num - 1].click();
                        }
                        return;
                    }
                    // / key: focus search input
                    if (e.key === '/') {
                        const search = doc.querySelector('input[aria-label="Search"]')
                                     || doc.querySelector('input[placeholder*="Search"]');
                        if (search) {
                            e.preventDefault();
                            search.focus();
                        }
                        return;
                    }
                }
                // Esc: close dialogs / blur inputs
                if (e.key === 'Escape') {
                    if (inInput) {
                        e.target.blur();
                        return;
                    }
                    const closeBtn = doc.querySelector('[data-testid="stModal"] button[aria-label="Close"]');
                    if (closeBtn) closeBtn.click();
                }
            });
        })();
        </script>
    """, height=0)


if __name__ == "__main__":
    main()
