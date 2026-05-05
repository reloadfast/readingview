from pydantic import BaseModel, ConfigDict


class SettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Audiobookshelf
    abs_url: str | None
    abs_token: str | None  # "" if set, None if not configured

    # Book recommender
    recommender_enabled: bool
    recommender_vector_backend: str
    recommender_embed_model: str
    recommender_top_k: int
    recommender_min_similarity: float

    # LLM
    llm_type: str
    llm_endpoint: str | None
    llm_model: str | None
    llm_api_key: str | None  # "" if set, None if not configured

    # Notifications
    notifications_enabled: bool
    apprise_url: str | None  # "" if set, None if not configured
    notify_days_before: int
    notify_time: str
    timezone: str


class SettingsPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Audiobookshelf
    abs_url: str | None = None
    abs_token: str | None = None  # plaintext; will be encrypted

    # Book recommender
    recommender_enabled: bool | None = None
    recommender_vector_backend: str | None = None
    recommender_embed_model: str | None = None
    recommender_top_k: int | None = None
    recommender_min_similarity: float | None = None

    # LLM
    llm_type: str | None = None
    llm_endpoint: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None  # plaintext; will be encrypted

    # Notifications
    notifications_enabled: bool | None = None
    apprise_url: str | None = None  # plaintext; will be encrypted
    notify_days_before: int | None = None
    notify_time: str | None = None
    timezone: str | None = None


class LLMTestRequest(BaseModel):
    endpoint: str
    llm_type: str = "ollama"
    api_key: str | None = None


class ABSTestRequest(BaseModel):
    url: str
    token: str


class TestConnectionResponse(BaseModel):
    ok: bool
    models: list[str] | None = None
    error: str | None = None
