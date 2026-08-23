import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, errors
from telethon.tl.types import MessageMediaPhoto
from PIL import Image  # Added for image metadata
from .config import TELEGRAM_API_ID, TELEGRAM_API_HASH, CHANNELS

# Load .env
load_dotenv()

# Setup logging
today_str = datetime.today().strftime("%Y-%m-%d")
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=f"logs/scrape_{today_str}.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Data Lake Paths
DATA_ROOT = "data_lake/raw"
MSG_PATH = os.path.join(DATA_ROOT, "telegram_messages", today_str)
MEDIA_PATH = os.path.join(DATA_ROOT, "media", today_str)
os.makedirs(MSG_PATH, exist_ok=True)
os.makedirs(MEDIA_PATH, exist_ok=True)

# Async scraping function
async def scrape_channel(client, channel_name, channel_url):
    logging.info(f"🔍 Scraping channel: {channel_name}")
    messages = []
    media_dir = os.path.join(MEDIA_PATH, channel_name)
    os.makedirs(media_dir, exist_ok=True)

    media_count = 0

    try:
        async for msg in client.iter_messages(channel_url, limit=200):
            item = {
                "id": msg.id,
                "date": str(msg.date),
                "sender_id": getattr(msg.sender_id, "user_id", msg.sender_id),
                "text": msg.text,
                "media_type": None,
                "media_url": None,
                "media_size_kb": None,
                "width": None,
                "height": None
            }

            if isinstance(msg.media, MessageMediaPhoto):
                try:
                    file_path = await client.download_media(msg, file=media_dir)
                    item["media_type"] = "photo"
                    item["media_url"] = file_path

                    # Extract image metadata
                    with Image.open(file_path) as img:
                        item["media_size_kb"] = round(os.path.getsize(file_path) / 1024, 2)
                        item["width"], item["height"] = img.size

                    media_count += 1

                except Exception as e:
                    logging.warning(f"⚠️ Could not download or read image from {channel_name}: {e}")

            messages.append(item)

        # Save all messages as JSON
        output_file = os.path.join(MSG_PATH, f"{channel_name}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

        logging.info(f"✅ {channel_name}: {len(messages)} messages scraped, {media_count} with images")

    except Exception as e:
        logging.error(f"❌ Error scraping {channel_name}: {str(e)}")


# Entry point
async def main():
    from time import time
    start_time = time()

    phone = input("Please enter your phone (with country code, e.g., +2519xxxxxxx): ").strip()

    client = TelegramClient("session", TELEGRAM_API_ID, TELEGRAM_API_HASH)

    try:
        await client.start(phone=phone)
    except errors.SessionPasswordNeededError:
        password = input("Two-factor authentication enabled. Please enter your password: ")
        await client.sign_in(password=password)
    except errors.PhoneNumberBannedError:
        logging.error("❌ Phone number is banned.")
        print("❌ Your phone number is banned from Telegram.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Unexpected error during login: {e}")
        print(f"Login failed: {e}")
        sys.exit(1)

    for name, url in CHANNELS.items():
        await scrape_channel(client, name, url)

    await client.disconnect()

    logging.info(f"🚀 All channels scraped in {round(time() - start_time, 2)} seconds")


# Run script
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
