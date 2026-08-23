# scripts/load_raw_to_pg.py
import os
import json
import psycopg2
from datetime import datetime

# DB credentials from .env or hardcoded (ideally use dotenv)
PG_CONN = {
    "dbname": "kara_db",
    "user": "karauser",
    "password": "karapass",
    "host": "localhost",
    "port": 5432
}

RAW_DIR = f"data_lake/raw/telegram_messages/{datetime.today().strftime('%Y-%m-%d')}"

def load_json_to_postgres():
    conn = psycopg2.connect(**PG_CONN)
    cursor = conn.cursor()

    # Create raw schema/table
    cursor.execute("""
    CREATE SCHEMA IF NOT EXISTS raw;
    CREATE TABLE IF NOT EXISTS raw.telegram_messages (
        id BIGINT,
        date TIMESTAMP,
        sender_id TEXT,
        text TEXT,
        media_type TEXT,
        media_url TEXT,
        media_size_kb REAL,
        width INT,
        height INT,
        channel TEXT
    );
    TRUNCATE raw.telegram_messages;
    """)

    for filename in os.listdir(RAW_DIR):
        channel = filename.replace(".json", "")
        with open(os.path.join(RAW_DIR, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
            for msg in data:
                cursor.execute("""
                    INSERT INTO raw.telegram_messages (
                        id, date, sender_id, text,
                        media_type, media_url, media_size_kb, width, height, channel
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    msg.get("id"),
                    msg.get("date"),
                    msg.get("sender_id"),
                    msg.get("text"),
                    msg.get("media_type"),
                    msg.get("media_url"),
                    msg.get("media_size_kb"),
                    msg.get("width"),
                    msg.get("height"),
                    channel
                ))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Raw messages loaded into PostgreSQL.")

if __name__ == "__main__":
    load_json_to_postgres()
