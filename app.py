"""
ReadingView - Audiobook Statistics Dashboard
Main application entry point.
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from config import config
from api.audiobookshelf import AudiobookshelfAPI
from components.library import render_library_view, render_in_progress_view, trigger_library_dialogs
from components.statistics import render_statistics_view
from components.release_tracker import render_release_tracker_view
from components.authors import render_authors_view
from components.notifications import render_notification_settings, render_notification_status_badge
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
        </style>
    """, unsafe_allow_html=True)


def show_configuration_guide():
    """Display configuration guide when app is not configured."""
    st.title("⚙️ Configuration Required")
    
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
    
    st.info("💡 After creating the `.env` file, restart the application.")


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
        except Exception as e:
            st.warning(f"⚠️ Release tracker unavailable: {e}")

    # Notification status badge in sidebar
    if db:
        render_notification_status_badge()

    # Trigger recommender dialogs once (before tabs to avoid duplicate IDs)
    trigger_library_dialogs()

    # Build tab list dynamically
    tab_names = ["📚 Library", "📖 In Progress", "📊 Statistics", "👤 Authors", "📖 Series"]
    if config.ENABLE_RELEASE_TRACKER and db:
        tab_names.append("📅 Release Tracker")
        tab_names.append("🔔 Notifications")
    if config.has_book_recommender():
        tab_names.append("💡 Recommendations")

    tabs = st.tabs(tab_names)
    tab_index = 0

    with tabs[tab_index]:
        render_library_view(api)
    tab_index += 1

    with tabs[tab_index]:
        render_in_progress_view(api)
    tab_index += 1

    with tabs[tab_index]:
        render_statistics_view(api)
    tab_index += 1

    with tabs[tab_index]:
        if config.ENABLE_RELEASE_TRACKER and db:
            render_authors_view(api, db)
        else:
            render_authors_view(api)
    tab_index += 1

    with tabs[tab_index]:
        render_series_tracker(api)
    tab_index += 1

    if config.ENABLE_RELEASE_TRACKER and db:
        with tabs[tab_index]:
            render_release_tracker_view(api, db)
        tab_index += 1
        with tabs[tab_index]:
            render_notification_settings(db)
        tab_index += 1

    if config.has_book_recommender():
        with tabs[tab_index]:
            render_recommendations_view()
        tab_index += 1

    # Switch to Authors tab when navigating from Library (Authors is at index 3)
    if st.session_state.pop("navigate_to_authors", False):
        components.html("""
            <script>
                const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs.length > 3) tabs[3].click();
            </script>
        """, height=0)


if __name__ == "__main__":
    main()
