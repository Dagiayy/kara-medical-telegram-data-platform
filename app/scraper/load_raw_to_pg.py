"""Loads scraped JSON out of the data lake into the raw Postgres layer.

Replaces the original TRUNCATE-and-reload approach (which silently threw
away history on every run and couldn't be run twice a day) with an
idempotent upsert keyed on (channel, message_id): safe to re-run, safe to
run incrementally, and it never loses previously-loaded history.

Also fans image references out into `raw.images` so `kara_detection` has
something to query -- in the original project nothing ever populated that
table.
"""
import argparse
import json
import os
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import execute_values

from app.config import get_settings
from app.logging_config import setup_logging
from app.observability import track_pipeline_run

settings = get_settings()
logger = setup_logging("load_raw_to_pg", settings.log_level, settings.log_json)


def parse_message_record(raw: dict, channel: str) -> tuple | None:
    """Validates and normalizes one scraped message. Returns None (and logs) if invalid."""
    msg_id = raw.get("id")
    if msg_id is None:
        logger.warning(f"Skipping record with no id in channel={channel}: {raw}")
        return None

    sent_at = raw.get("date")
    try:
        sent_at = datetime.fromisoformat(sent_at) if sent_at else None
    except ValueError:
        logger.warning(f"Skipping message {channel}/{msg_id}: unparseable date {sent_at!r}")
        return None

    return (
        channel,
        msg_id,
        sent_at,
        str(raw.get("sender_id")) if raw.get("sender_id") is not None else None,
        raw.get("text"),
        raw.get("media_type"),
        raw.get("media_url"),
        raw.get("media_size_kb"),
        raw.get("width"),
        raw.get("height"),
    )


def load_channel_file(path: str, channel: str) -> list[tuple]:
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Skipping unreadable file {path}: {e}")
            return []

    records = [parse_message_record(item, channel) for item in data]
    return [r for r in records if r is not None]


def upsert_messages(conn, records: list[tuple]) -> int:
    if not records:
        return 0
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO raw.telegram_messages (
                channel, message_id, sent_at, sender_id, message_text,
                media_type, media_url, media_size_kb, width, height
            ) VALUES %s
            ON CONFLICT (channel, message_id) DO UPDATE SET
                sent_at = EXCLUDED.sent_at,
                message_text = EXCLUDED.message_text,
                media_type = EXCLUDED.media_type,
                media_url = EXCLUDED.media_url,
                media_size_kb = EXCLUDED.media_size_kb,
                width = EXCLUDED.width,
                height = EXCLUDED.height;
            """,
            records,
        )
    return len(records)


def upsert_images(conn, records: list[tuple]) -> int:
    """Registers photo messages in raw.images so detect_images.py has work to do."""
    image_rows = [
        (channel, msg_id, media_url)
        for (channel, msg_id, _sent_at, _sender, _text, media_type, media_url, *_rest) in records
        if media_type == "photo" and media_url
    ]
    if not image_rows:
        return 0
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO raw.images (channel, message_id, image_path)
            VALUES %s
            ON CONFLICT (channel, message_id, image_path) DO NOTHING;
            """,
            image_rows,
        )
    return len(image_rows)


def load_json_to_postgres(date_str: str | None = None) -> None:
    date_str = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw_dir = os.path.join(settings.data_lake_root, "telegram_messages", date_str)

    if not os.path.isdir(raw_dir):
        logger.warning(f"No scraped data found for {date_str} at {raw_dir}; nothing to load.")
        return

    with track_pipeline_run("load_raw_to_pg") as run:
        conn = psycopg2.connect(**settings.sync_dsn)
        total_messages = 0
        total_images = 0
        try:
            for filename in sorted(os.listdir(raw_dir)):
                if not filename.endswith(".json"):
                    continue
                channel = filename[: -len(".json")]
                records = load_channel_file(os.path.join(raw_dir, filename), channel)
                if not records:
                    continue
                total_messages += upsert_messages(conn, records)
                total_images += upsert_images(conn, records)
                conn.commit()
                logger.info(f"{channel}: upserted {len(records)} messages")
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        run.rows_processed = total_messages
        logger.info(
            f"Loaded {total_messages} messages and registered {total_images} images "
            f"for {date_str} into PostgreSQL."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Load raw scraped Telegram data into Postgres.")
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD folder to load (default: today)")
    args = parser.parse_args()
    load_json_to_postgres(args.date)


if __name__ == "__main__":
    main()
