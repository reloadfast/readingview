# API Documentation

This document describes the internal API structure of Shelf and how to extend it with new data sources.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Audiobookshelf API Client](#audiobookshelf-api-client)
- [Adding New Data Sources](#adding-new-data-sources)
- [Data Models](#data-models)
- [Utilities](#utilities)

## Architecture Overview

Shelf follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           app.py (Main App)             │
│  - Streamlit configuration              │
│  - Navigation and routing               │
│  - Error handling                       │
└────────────────┬────────────────────────┘
                 │
     ┌───────────┴────────────┐
     │                        │
┌────▼─────────┐      ┌──────▼────────┐
│ Components   │      │     API       │
│              │      │   Clients     │
│ - library.py │◄─────┤               │
│ - stats.py   │      │ - audiobooksh │
└──────────────┘      │   elf.py      │
                      └───────────────┘
```

## Audiobookshelf API Client

Location: `api/audiobookshelf.py`

### AudiobookshelfAPI Class

Main client for interacting with Audiobookshelf.

#### Initialization

```python
from api.audiobookshelf import AudiobookshelfAPI

api = AudiobookshelfAPI(
    base_url="https://your-server.com",
    token="your_api_token"
)
```

#### Methods

##### Connection Testing

```python
is_connected = api.test_connection()
# Returns: bool
```

##### Get Libraries

```python
libraries = api.get_libraries()
# Returns: List[Dict[str, Any]]
# Each library contains: id, name, folders, mediaType, etc.
```

##### Get Library Items

```python
items = api.get_library_items(library_id="lib_xxxxx")
# Returns: List[Dict[str, Any]]
# Each item contains full audiobook metadata
```

##### Get User's In-Progress Items

```python
in_progress = api.get_user_items_in_progress()
# Returns: List[Dict[str, Any]]
# Items with active progress tracking
```

##### Get Listening Sessions

```python
sessions = api.get_user_listening_sessions()
# Returns: List[Dict[str, Any]]
# Historical listening session data
```

##### Get Listening Stats

```python
stats = api.get_user_listening_stats()
# Returns: Dict[str, Any]
# Aggregate statistics from server
```

##### Get Item Progress

```python
progress = api.get_item_progress(library_item_id="li_xxxxx")
# Returns: Dict[str, Any] or None
# Progress data for a specific item
```

##### Get Audiobook Details

```python
details = api.get_audiobook_details(library_item_id="li_xxxxx")
# Returns: Dict[str, Any] or None
# Full metadata for a specific audiobook
```

##### Get Cover URL

```python
cover_url = api.get_cover_url(library_item_id="li_xxxxx")
# Returns: str
# Direct URL to cover image
```

### AudiobookData Helper Class

Static methods for data extraction and formatting.

#### Extract Metadata

```python
from api.audiobookshelf import AudiobookData

metadata = AudiobookData.extract_metadata(library_item)
# Returns: Dict with keys:
# - id: str
# - title: str
# - author: str
# - narrator: str (optional)
# - duration: float (seconds)
# - cover_path: str (optional)
# - genres: List[str]
# - published_year: str (optional)
# - description: str (optional)
# - series: List[Dict] (optional)
```

#### Calculate Progress

```python
progress_metrics = AudiobookData.calculate_progress(
    progress_data=progress_obj,
    duration=total_seconds
)
# Returns: Dict with keys:
# - is_finished: bool
# - progress: float (0-100)
# - current_time: float (seconds)
# - time_remaining: float (seconds)
# - started_at: int (timestamp) or None
# - finished_at: int (timestamp) or None
# - last_update: int (timestamp) or None
```

#### Format Duration

```python
formatted = AudiobookData.format_duration(3723)
# Returns: "1h 2m"
```

## Adding New Data Sources

To add support for a new data source (e.g., Calibre, manual entries):

### Step 1: Create API Client

Create a new file in `api/` directory:

```python
# api/calibre.py

import requests
from typing import List, Dict, Any, Optional

class CalibreAPI:
    """Client for Calibre Content Server API."""
    
    def __init__(self, base_url: str, username: str = None, password: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
    
    def test_connection(self) -> bool:
        """Test if connection is working."""
        try:
            response = self.session.get(f"{self.base_url}/ajax/library-info")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_books(self) -> List[Dict[str, Any]]:
        """Get all books from Calibre."""
        # Implementation here
        pass
    
    # Additional methods...
```

### Step 2: Create Data Adapter

Adapt the data source to Shelf's internal format:

```python
class CalibreDataAdapter:
    """Adapter to convert Calibre data to Shelf format."""
    
    @staticmethod
    def to_audiobook_metadata(calibre_book: Dict) -> Dict[str, Any]:
        """Convert Calibre book to standard metadata format."""
        return {
            'id': str(calibre_book['id']),
            'title': calibre_book['title'],
            'author': ', '.join(calibre_book.get('authors', [])),
            'narrator': None,  # Not available in Calibre
            'duration': 0,  # Calculate if possible
            'cover_path': calibre_book.get('cover'),
            'genres': calibre_book.get('tags', []),
            'published_year': calibre_book.get('pubdate', '')[:4],
            'description': calibre_book.get('comments'),
            'series': calibre_book.get('series'),
        }
```

### Step 3: Update Configuration

Add new configuration options to `config.py`:

```python
class Config:
    # ... existing config ...
    
    # Calibre Configuration
    CALIBRE_URL: str = os.getenv("CALIBRE_URL", "")
    CALIBRE_USERNAME: str = os.getenv("CALIBRE_USERNAME", "")
    CALIBRE_PASSWORD: str = os.getenv("CALIBRE_PASSWORD", "")
    
    @classmethod
    def has_calibre(cls) -> bool:
        """Check if Calibre is configured."""
        return bool(cls.CALIBRE_URL)
```

### Step 4: Update Components

Modify components to support multiple sources:

```python
# In components/library.py

def render_library_view(abs_api: AudiobookshelfAPI, calibre_api: Optional[CalibreAPI] = None):
    """Render library view with support for multiple sources."""
    
    # Fetch from Audiobookshelf
    abs_items = abs_api.get_user_items_in_progress()
    
    # Fetch from Calibre if configured
    calibre_items = []
    if calibre_api:
        calibre_books = calibre_api.get_books()
        calibre_items = [
            CalibreDataAdapter.to_audiobook_metadata(book)
            for book in calibre_books
        ]
    
    # Merge and display
    all_items = merge_items(abs_items, calibre_items)
    display_items(all_items)
```

## Data Models

### Audiobook Metadata

Standard format for audiobook metadata across all sources:

```python
{
    'id': str,              # Unique identifier
    'title': str,           # Book title
    'author': str,          # Author name(s)
    'narrator': str | None, # Narrator name(s)
    'duration': float,      # Total duration in seconds
    'cover_path': str | None, # Path or URL to cover
    'genres': List[str],    # Genre tags
    'published_year': str | None, # Publication year
    'description': str | None,    # Book description
    'series': List[Dict] | None,  # Series information
}
```

### Progress Data

Standard format for tracking progress:

```python
{
    'is_finished': bool,      # Completion status
    'progress': float,        # Percentage (0-100)
    'current_time': float,    # Current position (seconds)
    'time_remaining': float,  # Remaining time (seconds)
    'started_at': int | None, # Unix timestamp (ms)
    'finished_at': int | None, # Unix timestamp (ms)
    'last_update': int | None, # Unix timestamp (ms)
}
```

### Session Data

Format for listening sessions:

```python
{
    'id': str,               # Session identifier
    'libraryItemId': str,    # Book identifier
    'timeListening': float,  # Duration (seconds)
    'startedAt': int,        # Unix timestamp (ms)
    'updatedAt': int,        # Unix timestamp (ms)
    'mediaProgress': {       # Progress at session end
        'isFinished': bool,
        'progress': float,
        'currentTime': float,
    }
}
```

## Utilities

Location: `utils/helpers.py`

### Date Formatting

```python
from utils.helpers import format_date, format_date_short

# Full format: "February 02, 2026"
full_date = format_date(timestamp_ms)

# Short format: "Feb 02, 2026"
short_date = format_date_short(timestamp_ms)
```

### Statistics Calculation

```python
from utils.helpers import (
    calculate_completion_stats,
    get_monthly_completion_counts,
    get_yearly_completion_counts
)

# Overall stats
stats = calculate_completion_stats(sessions)
# Returns: {'total_completed': int, 'total_time_seconds': float, 'total_time_hours': float}

# Monthly breakdown
monthly = get_monthly_completion_counts(sessions)
# Returns: {'2026-01': 5, '2026-02': 3, ...}

# Yearly breakdown
yearly = get_yearly_completion_counts(sessions)
# Returns: {'2025': 45, '2026': 8, ...}
```

### Session Grouping

```python
from utils.helpers import group_sessions_by_month

grouped = group_sessions_by_month(sessions)
# Returns: {'2026-01': [session1, session2, ...], '2026-02': [...], ...}
```

### Caching

```python
from utils.helpers import cached_api_call

# Automatically cache API results
@cached_api_call
def expensive_operation():
    return api.get_large_dataset()
```

### Error Display

```python
from utils.helpers import display_error, display_info

# Show error with optional details
display_error("Connection failed", details="Timeout after 30 seconds")

# Show info message
display_info("No data available yet")
```

## Best Practices

### Error Handling

Always handle API errors gracefully:

```python
try:
    items = api.get_library_items(library_id)
except Exception as e:
    logger.error(f"Failed to fetch items: {e}")
    display_error("Could not load library items")
    return []
```

### Caching

Use caching to reduce API load:

```python
@st.cache_data(ttl=300)  # 5 minutes
def get_expensive_data():
    return api.fetch_large_dataset()
```

### Type Hints

Always use type hints for clarity:

```python
def process_books(books: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process book data."""
    return [transform(book) for book in books]
```

### Documentation

Document all public functions:

```python
def calculate_stats(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics from listening sessions.
    
    Args:
        sessions: List of session objects from API
        
    Returns:
        Dictionary containing calculated statistics
        
    Example:
        >>> stats = calculate_stats(my_sessions)
        >>> print(stats['total_hours'])
        42.5
    """
    pass
```

## Testing

When extending Shelf, test thoroughly:

1. **Unit tests** for data transformations
2. **Integration tests** for API clients
3. **Manual testing** with real data
4. **Edge cases**: empty data, network failures, invalid responses

## Questions?

Refer to the [CONTRIBUTING.md](CONTRIBUTING.md) guide or open an issue on GitHub.
