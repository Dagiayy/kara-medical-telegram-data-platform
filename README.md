
# Kara Medical Telegram Data Platform

A scalable data pipeline that scrapes messages from Ethiopian Telegram medical-related channels using Python, loads them into PostgreSQL, and transforms them using **dbt** for clean, trusted analytics-ready data.

---

## 📦 Project Structure

```

kara-medical-telegram-data-platform/
├── .env.example                # Template for environment variables
├── data\_lake/                 # Stores raw scraped Telegram data as JSON
│   └── raw/
├── kara\_dbt/                  # dbt project folder for modeling & transformation
│   ├── models/
│   │   ├── staging/
│   │   ├── marts/
│   │   └── example/
│   └── dbt\_project.yml
├── app/
│   └── scraper/
│       ├── config.py          # Loads credentials & settings from .env
│       ├── scrape\_telegram.py # Collects raw messages from Telegram
│       └── load\_raw\_to\_pg.py  # Loads raw JSON into Postgres raw\.telegram\_messages
├── requirements.txt
└── README.md

````

---

## 🚀 Features

- 🔍 Scrape messages from curated Telegram channels
- 💾 Save scraped messages locally in a structured JSON format
- 🐘 Load raw data into a PostgreSQL `raw.telegram_messages` table
- 🔄 Use **dbt** to transform raw data into analytics-friendly star schema models
- ✅ Test your models with built-in and custom dbt tests
- 📊 Future-ready for dashboards, APIs, and alerts

---

## 🛠️ Setup & Usage

### 1. Clone the repository

```bash
git clone https://github.com/Dagiayy/kara-medical-telegram-data-platform.git
cd kara-medical-telegram-data-platform
````

---

### 2. Create a `.env` file

Create a file named `.env` in the root directory based on `.env.example`:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

POSTGRES_USER=karauser
POSTGRES_PASSWORD=karapass
POSTGRES_DB=kara_db
```

---

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Run Telegram Scraper

```bash
python app/scraper/scrape_telegram.py
```

This saves JSON files to:
`data_lake/raw/telegram_messages/YYYY-MM-DD/*.json`

---

### 5. Load raw JSON into PostgreSQL

```bash
python app/scraper/load_raw_to_pg.py
```

This script loads Telegram messages into the `raw.telegram_messages` table.

---

### 6. Initialize & run dbt models

```bash
cd kara_dbt
dbt run
```

This creates `analytics.fct_messages`, `dim_channels`, and `dim_dates` using transformations on the raw data.

---

### 7. Run dbt tests

```bash
dbt test
```

This will run:

* Built-in tests: `unique`, `not_null`
* Custom expression tests (e.g., message length > 0)
* Business logic validations (e.g., message must have text or media)

---

## 📊 dbt Star Schema

* **`dim_channels`** – Unique list of Telegram channels
* **`dim_dates`** – Calendar table for analysis
* **`fct_messages`** – Fact table with detailed metrics per message (text length, media presence, etc.)

---

## 🧪 Test Coverage

* `unique` and `not_null` for all primary keys
* Expression test: `message_length > 0`
* Custom test: ensure no empty messages (no text AND no media)

---

## 📥 Dependencies

* Python: `telethon`, `psycopg2`, `tesserocr`, `Pillow`, `python-dotenv`
* PostgreSQL
* dbt (`pip install dbt-postgres`)
* Optional: Docker (coming soon)

---

## 🛤 Future Enhancements

* 🔁 Add scheduler (e.g., Airflow or cron)
* 📊 Add dashboard (e.g., Metabase, Superset)
* ⚙️ REST API for accessing structured data
* 🧹 Add advanced NLP cleaning and deduplication

---

## 📄 License

MIT License. See `LICENSE` for details.

---

## 👨‍💻 Author

**Dagmawi Ayenew**
GitHub: [Dagiayy](https://github.com/Dagiayy)

```
