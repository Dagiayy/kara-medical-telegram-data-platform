
# 🏥 Kara Medical Telegram Data Platform

A scalable data pipeline that **scrapes medical-related messages from Telegram**, stores them in **PostgreSQL**, and transforms the raw data into **clean, analytics-ready tables** using **dbt**. Ideal for monitoring pharmaceutical promotions, product trends, or public health insights in Ethiopia.

---

## 📁 Project Structure

```

kara-medical-telegram-data-platform/
├── .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── app/
│   ├── **init**.py
│   └── scraper/
│       ├── config.py
│       ├── scrape\_telegram.py
│       └── load\_raw\_to\_pg.py
│
├── data\_lake/
│   └── raw/
│       └── telegram\_messages/
│           └── YYYY-MM-DD/
│               └── channel.json
│
├── kara\_detection/             # 🧠 YOLOv8-based object detection pipeline
│   └── detect\_images.py
│
├── api/                        # 🆕 FastAPI Analytical API
│   ├── main.py
│   ├── crud.py
│   ├── database.py
│   └── schemas.py
│
├── kara\_dbt/
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg\_telegram\_messages.sql
│   │   ├── marts/
│   │   │   ├── fct\_messages.sql
│   │   │   ├── dim\_channels.sql
│   │   │   ├── dim\_dates.sql
│   │   │   └── fct\_image\_detections.sql
│   │   └── schema.yml
│   └── dbt\_project.yml
└── README.md

````

---

## 🚀 Features

* 🔍 Scrape public messages and media from **Telegram channels**
* 📁 Store raw data in a **date-partitioned folder structure**
* 🐘 Load raw JSON into a **PostgreSQL raw schema**
* 🧹 Transform and validate data using **dbt**
* 🧠 Enrich media with **YOLOv8 object detection**
* 📊 Serve insights via a **FastAPI-based analytical API** (🆕 Task 4)
* ✅ Built-in and custom **data quality tests**
* 📦 Fully containerized with **Docker & Docker Compose**

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Dagiayy/kara-medical-telegram-data-platform.git
cd kara-medical-telegram-data-platform
````

### 2. Create a `.env` File

```ini
# .env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

POSTGRES_DB=kara_db
POSTGRES_USER=karauser
POSTGRES_PASSWORD=karapass
```

---

## 🐳 Run via Docker (Optional but recommended)

```bash
docker compose up --build
```

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

### 4. Run YOLOv8 Object Detection (Task 3)

```bash
python kara_detection/detect_images.py
```

### 5. Run dbt transformations

```bash
cd kara_dbt
dbt run
```

### 6. Run dbt tests

```bash
dbt test
```

### 7. Start FastAPI Analytical API (🆕 Task 4)

```bash
uvicorn api.main:app --reload
```

Then visit:

* Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* Example: [http://localhost:8000/api/reports/top-products?limit=5](http://localhost:8000/api/reports/top-products?limit=5)

---

## 📊 DBT Models Overview

* **Staging**

  * `stg_telegram_messages.sql`: Cleans raw JSON data

* **Data Marts**

  * `dim_channels`: Telegram channel metadata
  * `dim_dates`: Date dimension for time-series
  * `fct_messages`: Fact table with message text, media, and metadata
  * `fct_image_detections`: Detected objects from media images linked to messages

---

## 🔌 Analytical API Endpoints

| Endpoint                                     | Description                |
| -------------------------------------------- | -------------------------- |
| `GET /api/reports/top-products?limit=10`     | Top mentioned products     |
| `GET /api/channels/{channel_name}/activity`  | Daily activity per channel |
| `GET /api/search/messages?query=paracetamol` | Search messages by keyword |

---

## ✅ Tests & Validation

* `unique`, `not_null` on primary keys
* Custom test:

```sql
expression_is_true: message_length > 0
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

* 🔔 Real-time alerts for new products
* 📊 BI Dashboard (Metabase / Grafana)
* 🧼 Anomaly detection and NER (drug names, brands)
* 🎯 Object-specific trends from YOLOv8 detections
* 🧠 **Extend API with more endpoints (e.g., drugs by sentiment, top emerging products)** (🆕)

---

## 📄 License

MIT License. See [`LICENSE`](./LICENSE) file for details.

---

## 👤 Author

**Dagmawi Ayenew**
🔗 [GitHub](https://github.com/Dagiayy)

````

---

