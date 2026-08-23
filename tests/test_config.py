import os

from app.config import CHANNELS, get_settings


def test_settings_load_from_env():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.telegram_api_id == int(os.getenv("TELEGRAM_API_ID", "12345"))
    assert settings.telegram_api_hash == os.getenv("TELEGRAM_API_HASH", "test_hash")


def test_database_url_contains_all_parts():
    settings = get_settings()
    url = settings.database_url
    assert settings.postgres_user in url
    assert settings.postgres_db in url
    assert "postgresql+psycopg2://" in url


def test_channels_are_all_https_telegram_links():
    assert len(CHANNELS) > 0
    assert all(url.startswith("https://t.me/") for url in CHANNELS.values())
