from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:////data/readingview.db"
    SECRET_KEY: str
    PORT: int = 8000
    GIT_SHA: str = "dev"


settings = Settings()  # type: ignore[call-arg]
