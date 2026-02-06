"""
Audiobookshelf API client.
Handles all communication with the Audiobookshelf server.
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AudiobookshelfAPI:
    """Client for interacting with Audiobookshelf API."""
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the Audiobookshelf server
            token: API authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make an API request with error handling.
        
        Args:
            endpoint: API endpoint (without base URL)
            method: HTTP method
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON or None on error
        """
        url = f"{self.base_url}/api{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test if the API connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = self._make_request('/me')
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_media_progress_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all user media progress keyed by libraryItemId.

        Returns:
            Dict mapping libraryItemId to progress data
        """
        result = self._make_request('/me')
        if not result:
            return {}
        progress_list = result.get('mediaProgress', [])
        progress_map: Dict[str, Dict[str, Any]] = {}
        for p in progress_list:
            lid = p.get('libraryItemId')
            if lid:
                progress_map[lid] = p
        return progress_map

    def get_libraries(self) -> List[Dict[str, Any]]:
        """
        Get all libraries.
        
        Returns:
            List of library objects
        """
        result = self._make_request('/libraries')
        return result.get('libraries', []) if result else []
    
    def get_library_items(self, library_id: str) -> List[Dict[str, Any]]:
        """
        Get all items in a library.
        
        Args:
            library_id: Library ID
            
        Returns:
            List of library items
        """
        result = self._make_request(f'/libraries/{library_id}/items')
        return result.get('results', []) if result else []
    
    def get_user_listening_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all user's listening sessions (handles pagination).

        Returns:
            List of listening session objects
        """
        all_sessions: List[Dict[str, Any]] = []
        page = 0
        items_per_page = 100

        while True:
            result = self._make_request(
                f'/me/listening-sessions?itemsPerPage={items_per_page}&page={page}'
            )
            if not result:
                break

            sessions = result.get('sessions', [])
            all_sessions.extend(sessions)

            total = result.get('total', 0)
            if len(all_sessions) >= total or not sessions:
                break
            page += 1

        return all_sessions
    
    def get_user_listening_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get user's listening statistics.
        
        Returns:
            Statistics object or None
        """
        return self._make_request('/me/listening-stats')
    
    def get_item_progress(self, library_item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get progress for a specific library item.
        
        Args:
            library_item_id: Library item ID
            
        Returns:
            Progress object or None
        """
        return self._make_request(f'/me/progress/{library_item_id}')
    
    def get_user_items_in_progress(self) -> List[Dict[str, Any]]:
        """
        Get all items currently in progress for the user.
        
        Returns:
            List of items with progress
        """
        result = self._make_request('/me/items-in-progress')
        return result.get('libraryItems', []) if result else []
    
    def get_audiobook_details(self, library_item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific audiobook.
        
        Args:
            library_item_id: Library item ID
            
        Returns:
            Audiobook details or None
        """
        return self._make_request(f'/items/{library_item_id}')
    
    def get_cover_url(self, library_item_id: str) -> str:
        """
        Get the URL for an audiobook's cover image.
        
        Args:
            library_item_id: Library item ID
            
        Returns:
            Cover image URL
        """
        return f"{self.base_url}/api/items/{library_item_id}/cover"


class AudiobookData:
    """Helper class to parse and structure audiobook data."""
    
    @staticmethod
    def extract_metadata(item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant metadata from a library item.
        
        Args:
            item: Library item object
            
        Returns:
            Cleaned metadata dictionary
        """
        media = item.get('media', {})
        metadata = media.get('metadata', {})
        
        return {
            'id': item.get('id', ''),
            'title': metadata.get('title', 'Unknown Title'),
            'author': metadata.get('authorName', 'Unknown Author'),
            'narrator': metadata.get('narratorName'),
            'duration': media.get('duration', 0),
            'cover_path': media.get('coverPath'),
            'genres': metadata.get('genres', []),
            'published_year': metadata.get('publishedYear'),
            'description': metadata.get('description'),
            'series': metadata.get('series', []),
            'isbn': metadata.get('isbn'),
            'asin': metadata.get('asin'),
        }
    
    @staticmethod
    def calculate_progress(progress_data: Optional[Dict[str, Any]], duration: float) -> Dict[str, Any]:
        """
        Calculate progress metrics for an audiobook.
        
        Args:
            progress_data: Progress object from API
            duration: Total duration in seconds
            
        Returns:
            Progress metrics dictionary
        """
        if not progress_data:
            return {
                'is_finished': False,
                'progress': 0.0,
                'current_time': 0,
                'time_remaining': duration,
                'started_at': None,
                'finished_at': None
            }
        
        current_time = progress_data.get('currentTime', 0)
        is_finished = progress_data.get('isFinished', False)
        progress = progress_data.get('progress', 0)
        
        return {
            'is_finished': is_finished,
            'progress': progress * 100,  # Convert to percentage
            'current_time': current_time,
            'time_remaining': max(0, duration - current_time),
            'started_at': progress_data.get('startedAt'),
            'finished_at': progress_data.get('finishedAt'),
            'last_update': progress_data.get('lastUpdate')
        }
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in seconds to human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string (e.g., "5h 23m")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
