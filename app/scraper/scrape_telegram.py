"""Scrapes public medical Telegram channels into the raw data lake.

Design notes
------------
- Non-interactive by default: if TELEGRAM_SESSION_STRING is set, Telethon
  logs in with a StringSession and never touches stdin, so this runs
  unattended in Docker / Dagster. If it isn't set, falls back to an
  interactive phone-number login (first-time local setup) and prints the
  resulting session string so it can be saved to `.env`.
- Incremental: remembers the highest message id seen per channel
  (`data_lake/.scrape_state.json`) and only fetches newer messages on
  subsequent runs, via Telethon's `min_id`. `--full` forces a full
  `scrape_message_limit`-message backfill.
- Resilient: retries transient Telegram/network errors with backoff and
  respects FloodWaitError instead of hammering the API.
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

from PIL import Image
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import CHANNELS, get_settings
from app.logging_config import setup_logging

settings = get_settings()
logger = setup_logging("scraper", settings.log_level, settings.log_json)

STATE_FILE = os.path.join(settings.data_lake_root, "..", ".scrape_state.json")


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_state() -> dict[str, int]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read scrape state, starting fresh: {e}")
    return {}


def save_state(state: dict[str, int]) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError, OSError)),
)
async def _download_media(client, msg, media_dir):
    return await client.download_media(msg, file=media_dir)


async def scrape_channel(
    client: TelegramClient,
    channel_name: str,
    channel_url: str,
    msg_root: str,
    media_root: str,
    min_id: int = 0,
    limit: int = 200,
) -> int | None:
    """Scrapes one channel; returns the highest message id seen, or None on failure."""
    logger.info(f"Scraping channel: {channel_name} (min_id={min_id})")
    messages = []
    media_dir = os.path.join(media_root, channel_name)
    os.makedirs(media_dir, exist_ok=True)

    media_count = 0
    max_id_seen = min_id

    try:
        async for msg in client.iter_messages(channel_url, limit=limit, min_id=min_id):
            max_id_seen = max(max_id_seen, msg.id)
            item = {
                "id": msg.id,
                "date": str(msg.date),
                "sender_id": getattr(msg.sender_id, "user_id", msg.sender_id),
                "text": msg.text,
                "media_type": None,
                "media_url": None,
                "media_size_kb": None,
                "width": None,
                "height": None,
            }

            if isinstance(msg.media, MessageMediaPhoto):
                try:
                    file_path = await _download_media(client, msg, media_dir)
                    item["media_type"] = "photo"
                    # Store a platform-independent path: this file may be
                    # scraped on Windows and later read inside a Linux
                    # container, where backslashes wouldn't resolve.
                    item["media_url"] = file_path.replace(os.sep, "/")

                    with Image.open(file_path) as img:
                        item["media_size_kb"] = round(os.path.getsize(file_path) / 1024, 2)
                        item["width"], item["height"] = img.size

                    media_count += 1
                except errors.FloodWaitError:
                    raise
                except Exception as e:
                    logger.warning(f"Could not download/read image from {channel_name}: {e}")

            messages.append(item)

        if messages:
            output_file = os.path.join(msg_root, f"{channel_name}.json")
            os.makedirs(msg_root, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)

        logger.info(f"{channel_name}: {len(messages)} new messages, {media_count} with images")
        return max_id_seen

    except errors.FloodWaitError as e:
        logger.error(f"Flood wait for {channel_name}: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return min_id
    except Exception as e:
        logger.error(f"Error scraping {channel_name}: {e}")
        return None


async def run(full: bool = False, limit: int | None = None) -> None:
    today_str = _today_str()
    msg_root = os.path.join(settings.data_lake_root, "telegram_messages", today_str)
    media_root = os.path.join(settings.data_lake_root, "media", today_str)
    fetch_limit = limit or settings.scrape_message_limit

    state = {} if full else load_state()

    if settings.telegram_session_string:
        session = StringSession(settings.telegram_session_string)
    else:
        session = settings.telegram_session_name

    client = TelegramClient(session, settings.telegram_api_id, settings.telegram_api_hash)

    if settings.telegram_session_string:
        await client.connect()
        if not await client.is_user_authorized():
            logger.error(
                "TELEGRAM_SESSION_STRING is set but not authorized. "
                "Regenerate it with an interactive login."
            )
            sys.exit(1)
    else:
        try:
            phone = input("Please enter your phone (with country code, e.g., +2519xxxxxxx): ").strip()
            await client.start(phone=phone)
            print(
                "\nSave this string as TELEGRAM_SESSION_STRING in your .env to run "
                "non-interactively next time:\n"
                f"{client.session.save()}\n"
            )
        except errors.SessionPasswordNeededError:
            password = input("Two-factor authentication enabled. Please enter your password: ")
            await client.sign_in(password=password)
        except errors.PhoneNumberBannedError:
            logger.error("Phone number is banned.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            sys.exit(1)

    start_time = asyncio.get_event_loop().time()

    for name, url in CHANNELS.items():
        max_id = await scrape_channel(
            client, name, url, msg_root, media_root,
            min_id=state.get(name, 0), limit=fetch_limit,
        )
        if max_id is not None:
            state[name] = max_id
        save_state(state)  # persist progress after every channel, not just at the end

    await client.disconnect()
    elapsed = round(asyncio.get_event_loop().time() - start_time, 2)
    logger.info(f"All channels scraped in {elapsed} seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape configured Telegram channels.")
    parser.add_argument("--full", action="store_true", help="Ignore incremental state, backfill scrape_message_limit messages")
    parser.add_argument("--limit", type=int, default=None, help="Override scrape_message_limit for this run")
    args = parser.parse_args()
    asyncio.run(run(full=args.full, limit=args.limit))


if __name__ == "__main__":
    main()
