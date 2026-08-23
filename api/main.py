"""Kara Medical Analytical API.

Serves read-only analytics over the dbt-built `analytics` schema: top
product/drug mentions, per-channel activity, full-text search, and a simple
trend/anomaly view over daily message volume.
"""

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.logging_config import setup_logging

from . import crud, schemas
from .database import engine, get_db

settings = get_settings()
logger = setup_logging("api", settings.log_level, settings.log_json)

app = FastAPI(
    title="Kara Medical Analytical API",
    version="1.0.0",
    description="Analytics over medical-related Telegram channel activity.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.api_cors_origins.split(",")],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def pagination(
    limit: int = Query(settings.api_default_page_size, ge=1, le=settings.api_max_page_size),
    offset: int = Query(0, ge=0),
) -> dict:
    return {"limit": limit, "offset": offset}


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(_request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    raise HTTPException(status_code=503, detail="Database temporarily unavailable")


@app.get("/health", response_model=schemas.HealthStatus, tags=["ops"])
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except SQLAlchemyError:
        return {"status": "degraded", "database": "unreachable"}


@app.get("/api/reports/top-products", response_model=list[schemas.TopProduct], tags=["reports"])
def top_products(page: dict = Depends(pagination), conn: Connection = Depends(get_db)):
    """Most frequently mentioned drugs/products, matched via the curated
    product dictionary (kara_dbt/seeds/product_dictionary.csv)."""
    return crud.get_top_products(conn, **page)


@app.get("/api/channels/{channel_name}/activity", response_model=list[schemas.ChannelActivity], tags=["reports"])
def channel_activity(channel_name: str, page: dict = Depends(pagination), conn: Connection = Depends(get_db)):
    if not crud.channel_exists(conn, channel_name):
        raise HTTPException(status_code=404, detail=f"Unknown channel: {channel_name}")
    return crud.get_channel_activity(conn, channel_name, **page)


@app.get("/api/search/messages", response_model=list[schemas.SearchResult], tags=["reports"])
def search_messages(
    query: str = Query(..., min_length=2),
    page: dict = Depends(pagination),
    conn: Connection = Depends(get_db),
):
    return crud.search_messages(conn, query, **page)


@app.get("/api/analytics/trends", response_model=list[schemas.TrendPoint], tags=["analytics"])
def message_trends(
    channel: str | None = Query(None, description="Restrict to one channel; omit for all channels"),
    days: int = Query(30, ge=1, le=365),
    conn: Connection = Depends(get_db),
):
    """Daily message volume with a z-score, so callers can flag spikes/dips
    (e.g. a sudden surge in postings for a channel) without a forecasting
    dependency."""
    if channel and not crud.channel_exists(conn, channel):
        raise HTTPException(status_code=404, detail=f"Unknown channel: {channel}")
    return crud.get_daily_message_trend(conn, channel, days)
