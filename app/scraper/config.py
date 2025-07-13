import os
from dotenv import load_dotenv

load_dotenv()

def get_env_var(name: str, required=True):
    value = os.getenv(name)
    if required and not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value

TELEGRAM_API_ID = int(get_env_var("TELEGRAM_API_ID"))
TELEGRAM_API_HASH = get_env_var("TELEGRAM_API_HASH")

POSTGRES_USER = get_env_var("POSTGRES_USER")
POSTGRES_PASSWORD = get_env_var("POSTGRES_PASSWORD")
POSTGRES_DB = get_env_var("POSTGRES_DB")

CHANNELS = {
    "lobelia4cosmetics": "https://t.me/lobelia4cosmetics",
    "tikvahpharma": "https://t.me/tikvahpharma",
    "bethelmedstore": "https://t.me/bethelmedstore",
    "manekapharma": "https://t.me/manekapharma",
    "zapharmaofficial": "https://t.me/zapharmaofficial",
    "addispharma": "https://t.me/addispharma"
}
