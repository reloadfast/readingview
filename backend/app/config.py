from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:////data/readingview.db"
    SECRET_KEY: str
    PORT: int = 8000
    GIT_SHA: str = "dev"
    BACKUP_TOKEN: str | None = None
    BACKUP_MAX_RESTORE_BYTES: int = 1024 * 1024 * 1024  # 1 GiB


settings = Settings()  # type: ignore[call-arg]
