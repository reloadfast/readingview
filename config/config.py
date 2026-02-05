import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Audiobookshelf Configuration
    ABS_URL: str = os.getenv("ABS_URL", "")
    ABS_TOKEN: str = os.getenv("ABS_TOKEN", "")

    # Application Settings
    APP_TITLE: str = os.getenv("APP_TITLE", "ReadingView")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))

    # UI Configuration
    ITEMS_PER_ROW: int = int(os.getenv("ITEMS_PER_ROW", "5"))
    THEME: str = os.getenv("THEME", "dark")

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        if not cls.ABS_URL:
            return False, "ABS_URL environment variable is required"
        if not cls.ABS_TOKEN:
            return False, "ABS_TOKEN environment variable is required"
        if not cls.ABS_URL.startswith(("http://", "https://")):
            return False, "ABS_URL must start with http:// or https://"
        return True, None

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.ABS_URL and cls.ABS_TOKEN)


config = Config()
