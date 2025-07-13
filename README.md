
# 🏥 Kara Medical Telegram Data Platform

A scalable data pipeline that **scrapes medical-related messages from Telegram**, stores them in **PostgreSQL**, and transforms the raw data into **clean, analytics-ready tables** using **dbt**. Ideal for monitoring pharmaceutical promotions, product trends, or public health insights in Ethiopia.

---

## 📁 Project Structure

```
kara-medical-telegram-data-platform/
├── .env                         # Environment variables (API keys, DB credentials)
├── .gitignore
├── Dockerfile                   # Container definition for scraper app
├── docker-compose.yml           # Services orchestration: scraper, PostgreSQL
├── requirements.txt             # Python dependencies
│
├── app/
│   ├── __init__.py
│   └── scraper/
│       ├── config.py            # Loads environment variables
│       ├── scrape_telegram.py   # Telegram scraping logic
│       └── load_raw_to_pg.py    # Loads raw JSON to PostgreSQL
│
├── data_lake/
│   └── raw/
│       └── telegram_messages/
│           └── YYYY-MM-DD/
│               └── channel.json
│
├── kara_dbt/                    # DBT project for transforming raw data
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg_telegram_messages.sql
│   │   ├── marts/
│   │   │   ├── fct_messages.sql
│   │   │   ├── dim_channels.sql
│   │   │   └── dim_dates.sql
│   │   └── schema.yml
│   └── dbt_project.yml
└── README.md
```

---

## 🚀 Features

* 🔍 Scrape public messages and media from **Telegram channels**
* 📁 Store raw data in a **date-partitioned folder structure**
* 🐘 Load raw JSON into a **PostgreSQL raw schema**
* 🧹 Transform and validate data using **dbt**
* ✅ Built-in and custom **data quality tests**
* 📦 Fully containerized with **Docker & Docker Compose**

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Dagiayy/kara-medical-telegram-data-platform.git
cd kara-medical-telegram-data-platform
```

### 2. Create a `.env` File

```ini
# .env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

POSTGRES_DB=kara_db
POSTGRES_USER=karauser
POSTGRES_PASSWORD=karapass
```

> ✅ Make sure `.env` is listed in `.gitignore`.

---

## 🐳 Run via Docker (Optional but recommended)

```bash
docker compose up --build
```

This will:

* Build the scraper app container
* Spin up PostgreSQL
* Automatically run the scraping process (with cron or manual trigger)

---

## 🧪 Manual Workflow (For Local Testing)

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Scrape Telegram messages

```bash
python app/scraper/scrape_telegram.py
```

### 3. Load raw data to PostgreSQL

```bash
python app/scraper/load_raw_to_pg.py
```

### 4. Run dbt transformations

```bash
cd kara_dbt
dbt run
```

### 5. Run dbt tests

```bash
dbt test
```

---

## 📊 DBT Models Overview

* **Staging**

  * `stg_telegram_messages.sql`: Cleans raw JSON data
* **Data Marts**

  * `dim_channels`: Telegram channel metadata
  * `dim_dates`: Date dimension for time-series
  * `fct_messages`: Fact table with message text, media, and metadata

### ✅ Tests & Validation

* `unique`, `not_null` on primary keys
* Custom test:

  ```sql
  expression_is_true: message_length > 0
  ```
* Docs:

  ```bash
  dbt docs generate
  dbt docs serve
  ```

---

## 🔍 Example Telegram Channels Tracked

* `@lobelia4cosmetics`
* `@tikvahpharma`
* `@zapharmaofficial`
* `@manekapharma`
* `@addispharma`

---

## 🧠 Future Enhancements

* 🔔 Add real-time alerts (e.g., new product promotion)
* 📊 Add BI dashboard (Metabase / Grafana)
* 🧼 Add anomaly detection and entity recognition (e.g., drugs mentioned)

---

## 📄 License

MIT License. See [`LICENSE`](./LICENSE) file for details.

---

## 👤 Author

**Dagmawi Ayenew**
🔗 [GitHub](https://github.com/Dagiayy)

---

