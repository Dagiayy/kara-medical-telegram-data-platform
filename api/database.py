"""SQLAlchemy engine + pooled connections for the analytical API.

Replaces the original per-request `psycopg2.connect(host="localhost", ...)`
(a new TCP connection on every single request, hard-coded credentials, and
a host that doesn't resolve inside the Docker network) with a pooled engine
configured from centralized settings.
"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)


def get_db() -> Iterator[Connection]:
    """FastAPI dependency yielding a pooled connection, closed after the request."""
    with engine.connect() as conn:
        yield conn
