import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# Load secrets
load_dotenv()
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")

# Telegram usernames
channels = {
    "chemed": "https://t.me/lobelia4cosmetics",   # Replace with real Chemed handle if known
    "lobelia4cosmetics": "https://t.me/lobelia4cosmetics",
    "tikvahpharma": "https://t.me/tikvahpharma"
}

# Logger setup
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=f"{log_dir}/scrape_{datetime.today().date()}.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

# Output directory
today = datetime.today().strftime("%Y-%m-%d")
base_path = f"data_lake/raw/telegram_messages/{today}/"
os.makedirs(base_path, exist_ok=True)

# Main scraping function
def scrape_channel(channel_name, channel_url):
    logging.info(f"Scraping {channel_name} from {channel_url}")
    output_file = os.path.join(base_path, f"{channel_name}.json")
    try:
        with TelegramClient('anon', api_id, api_hash) as client:
            all_messages = []
            for message in client.iter_messages(channel_url, limit=200):  # You can change limit
                msg_data = {
                    "id": message.id,
                    "date": str(message.date),
                    "text": message.text,
                    "media_type": None,
                    "media_url": None,
                    "sender_id": getattr(message.sender_id, 'user_id', None)
                }

                # If media is image
                if isinstance(message.media, MessageMediaPhoto):
                    media_path = f"data_lake/raw/media/{today}/{channel_name}"
                    os.makedirs(media_path, exist_ok=True)
                    file_path = client.download_media(message, file=media_path)
                    msg_data["media_type"] = "photo"
                    msg_data["media_url"] = file_path

                all_messages.append(msg_data)

            # Save to JSON
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_messages, f, ensure_ascii=False, indent=2)

            logging.info(f"Saved {len(all_messages)} messages to {output_file}")

    except Exception as e:
        logging.error(f"Failed to scrape {channel_name}: {str(e)}")

# Run for all channels
if __name__ == "__main__":
    for name, url in channels.items():
        scrape_channel(name, url)
