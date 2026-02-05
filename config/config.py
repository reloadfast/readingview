"""
Configuration management for ReadingView application.
All sensitive data is loaded from environment variables using python-dotenv.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration loaded from environment variables."""

    # Audiobookshelf Configuration
    ABS_URL: str = os.getenv("ABS_URL", "")
    ABS_TOKEN: str = os.getenv("ABS_TOKEN", "")

    # Application Settings
    APP_TITLE: str = os.getenv("APP_TITLE", "ReadingView")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default

    # UI Configuration
    ITEMS_PER_ROW: int = int(os.getenv("ITEMS_PER_ROW", "5"))
    THEME: str = os.getenv("THEME", "dark")  # dark or light

    # Release Tracker Configuration
    ENABLE_RELEASE_TRACKER: bool = (
        os.getenv("ENABLE_RELEASE_TRACKER", "true").lower() == "true"
    )
    GOODREADS_API_KEY: str = os.getenv("GOODREADS_API_KEY", "")  # Optional

    # Notification Configuration (Future use)
    APPRISE_API_URL: str = os.getenv("APPRISE_API_URL", "")  # Your Apprise API endpoint
    APPRISE_NOTIFICATION_KEY: str = os.getenv("APPRISE_NOTIFICATION_KEY", "")
    ENABLE_NOTIFICATIONS: bool = (
        os.getenv("ENABLE_NOTIFICATIONS", "false").lower() == "true"
    )

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validate required configuration.
        Returns (is_valid, error_message)
        """
        if not cls.ABS_URL:
            return False, "ABS_URL environment variable is required"

        if not cls.ABS_TOKEN:
            return False, "ABS_TOKEN environment variable is required"

        # Validate URL format
        if not cls.ABS_URL.startswith(("http://", "https://")):
            return False, "ABS_URL must start with http:// or https://"

        return True, None

    @classmethod
    def is_configured(cls) -> bool:
        """Check if minimum configuration is present."""
        return bool(cls.ABS_URL and cls.ABS_TOKEN)

    @classmethod
    def has_apprise(cls) -> bool:
        """Check if Apprise notifications are configured."""
        return bool(cls.APPRISE_API_URL and cls.ENABLE_NOTIFICATIONS)

    @classmethod
    def reload(cls):
        """Reload configuration from .env file."""
        load_dotenv(dotenv_path=env_path, override=True)
        # Re-read all values
        cls.ABS_URL = os.getenv("ABS_URL", "")
        cls.ABS_TOKEN = os.getenv("ABS_TOKEN", "")
        cls.APP_TITLE = os.getenv("APP_TITLE", "ReadingView")
        cls.CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
        cls.ITEMS_PER_ROW = int(os.getenv("ITEMS_PER_ROW", "5"))
        cls.THEME = os.getenv("THEME", "dark")
        cls.ENABLE_RELEASE_TRACKER = (
            os.getenv("ENABLE_RELEASE_TRACKER", "true").lower() == "true"
        )
        cls.GOODREADS_API_KEY = os.getenv("GOODREADS_API_KEY", "")
        cls.APPRISE_API_URL = os.getenv("APPRISE_API_URL", "")
        cls.APPRISE_NOTIFICATION_KEY = os.getenv("APPRISE_NOTIFICATION_KEY", "")
        cls.ENABLE_NOTIFICATIONS = (
            os.getenv("ENABLE_NOTIFICATIONS", "false").lower() == "true"
        )


# Create a singleton instance
config = Config()
