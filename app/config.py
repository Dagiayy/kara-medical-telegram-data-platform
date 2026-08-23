"""Centralized configuration for the whole platform.

Every component (scraper, loader, detector, API, orchestrator) imports its
settings from here instead of hard-coding credentials or re-parsing the
environment. Values come from environment variables / a local `.env` file
(see `.env.example`).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Telegram ---
    telegram_api_id: int = Field(..., description="Telegram API ID from my.telegram.org")
    telegram_api_hash: str = Field(..., description="Telegram API hash from my.telegram.org")
    telegram_session_name: str = "kara_session"
    # If set, Telethon logs in non-interactively using a StringSession instead
    # of prompting for a phone number. Required for Docker/orchestrated runs.
    telegram_session_string: str | None = None
    scrape_message_limit: int = 200

    # --- Postgres ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "kara_db"
    postgres_user: str = "karauser"
    postgres_password: str = "karapass"

    # --- Data lake ---
    data_lake_root: str = "data_lake/raw"

    # --- Object detection ---
    yolo_model_path: str = "yolov8n.pt"
    yolo_confidence_threshold: float = 0.35
    yolo_batch_size: int = 16

    # --- Observability ---
    log_level: str = "INFO"
    log_json: bool = False

    # --- API ---
    api_default_page_size: int = 20
    api_max_page_size: int = 200
    api_cors_origins: str = "*"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_dsn(self) -> dict[str, object]:
        """Kwargs suitable for psycopg2.connect(**settings.sync_dsn)."""
        return {
            "host": self.postgres_host,
            "port": self.postgres_port,
            "dbname": self.postgres_db,
            "user": self.postgres_user,
            "password": self.postgres_password,
        }


# Channels tracked by the scraper. Kept as code (not env vars) since it's
# structured, versioned data the team edits deliberately, not a secret.
CHANNELS: dict[str, str] = {
    "lobelia4cosmetics": "https://t.me/lobelia4cosmetics",
    "tikvahpharma": "https://t.me/tikvahpharma",
    "bethelmedstore": "https://t.me/bethelmedstore",
    "manekapharma": "https://t.me/manekapharma",
    "zapharmaofficial": "https://t.me/zapharmaofficial",
    "addispharma": "https://t.me/addispharma",
}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton -- import this, not Settings() directly."""
    return Settings()
