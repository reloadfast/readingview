from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Settings(Base):
    # Encrypted fields use their natural column name (no _enc suffix); see api/settings.py
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Audiobookshelf
    abs_url: Mapped[str | None] = mapped_column(String, nullable=True)
    abs_token: Mapped[str | None] = mapped_column(String, nullable=True)  # encrypted

    # Book recommender
    recommender_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    recommender_vector_backend: Mapped[str] = mapped_column(String, default="python")
    recommender_embed_model: Mapped[str] = mapped_column(String, default="nomic-embed-text")
    recommender_top_k: Mapped[int] = mapped_column(Integer, default=10)
    recommender_min_similarity: Mapped[float] = mapped_column(Float, default=0.2)
    recommender_explanations_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # LLM
    llm_type: Mapped[str] = mapped_column(String, default="ollama")
    llm_endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_api_key: Mapped[str | None] = mapped_column(String, nullable=True)  # encrypted

    # Recommender config fingerprint — shared across workers; stale on settings change
    recommender_config_hash: Mapped[str | None] = mapped_column(String, nullable=True)

    # Notifications
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    apprise_url: Mapped[str | None] = mapped_column(String, nullable=True)  # encrypted
    notify_days_before: Mapped[int] = mapped_column(Integer, default=7)
    notify_time: Mapped[str] = mapped_column(String, default="09:00")
    timezone: Mapped[str] = mapped_column(String, default="UTC")

    # Release auto-refresh
    releases_refresh_cron: Mapped[str] = mapped_column(String, default="0 6 * * *")
