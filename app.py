"""
ReadingView - Audiobook Statistics Dashboard
Main application entry point.
"""

import streamlit as st
from config import config
from api.audiobookshelf import AudiobookshelfAPI
from components.library import render_library_view
from components.statistics import render_statistics_view
from utils.helpers import display_error


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
    
    ### Required Environment Variables
    
    Set the following environment variables:
    """)
    
    st.code("""
export ABS_URL=https://your-audiobookshelf-url
export ABS_TOKEN=your_api_token
    """, language="bash")
    
    st.markdown("""
    ### Getting Your API Token
    
    1. Log into your Audiobookshelf instance
    2. Go to **Settings** → **Users**
    3. Click on your user
    4. Generate a new **API token**
    5. Copy the token
    
    ### Docker Example
    
    If running in Docker, pass environment variables like this:
    """)
    
    st.code("""
docker run -d \\
  --name shelf \\
  -p 8501:8501 \\
  -e ABS_URL=https://your-audiobookshelf-url \\
  -e ABS_TOKEN=your_api_token \\
  shelf:latest
    """, language="bash")
    
    st.markdown("""
    ### Docker Compose Example
    """)
    
    st.code("""
version: '3.8'
services:
  shelf:
    image: shelf:latest
    container_name: shelf
    ports:
      - "8501:8501"
    environment:
      - ABS_URL=https://your-audiobookshelf-url
      - ABS_TOKEN=your_api_token
    restart: unless-stopped
    """, language="yaml")
    
    st.info("After setting environment variables, restart the application.")


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
    
    # Navigation tabs
    tab1, tab2 = st.tabs(["📚 Library", "📊 Statistics"])
    
    with tab1:
        render_library_view(api)
    
    with tab2:
        render_statistics_view(api)


if __name__ == "__main__":
    main()
