
# 🏥 Kara Medical Telegram Data Platform

A production-grade data platform that **scrapes medical-related messages from Telegram**, enriches media with **YOLOv8 object detection**, stores data in **PostgreSQL**, transforms it with **dbt**, serves insights via a **FastAPI Analytical API**, and orchestrates the entire pipeline using **Dagster**.

Ideal for monitoring pharmaceutical promotions, tracking product trends, and deriving public health insights in Ethiopia.

---

## 📁 Project Structure

```

kara-medical-telegram-data-platform/
├── .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt

├── app/
│   ├── **init**.py
│   └── scraper/
│       ├── config.py
│       ├── scrape\_telegram.py
│       └── load\_raw\_to\_pg.py

├── data\_lake/
│   └── raw/
│       └── telegram\_messages/
│           └── YYYY-MM-DD/
│               └── channel.json

├── kara\_detection/             # YOLOv8 object detection pipeline
│   └── detect\_images.py


├── api/                        # FastAPI analytical API
│   ├── main.py
│   ├── crud.py
│   ├── database.py
│   └── schemas.py

├── kara\_dbt/                   # dbt transformation project
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

├── orchestrator/               # Dagster orchestration
│   ├── **init**.py
│   ├── pipeline.py
│   ├── repository.py
│   └── schedules.py

└── README.md

````

---

## 🚀 Features

✅ **Telegram Message Scraper** – Collects public medical messages/media  
✅ **Data Lake Storage** – Raw messages organized by date  
✅ **PostgreSQL Integration** – Raw → structured tables  
✅ **YOLOv8 Object Detection** – Media intelligence from images  
✅ **DBT Transformations** – Clean, testable analytical models  
✅ **FastAPI Analytical API** – RESTful endpoints for reporting  
✅ **Dagster Orchestration** – Schedule, monitor, and manage pipeline  
✅ **Dockerized Deployment** – For reproducibility and portability

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Dagiayy/kara-medical-telegram-data-platform.git
cd kara-medical-telegram-data-platform
````

### 2. Configure `.env`

```ini
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

POSTGRES_DB=kara_db
POSTGRES_USER=karauser
POSTGRES_PASSWORD=karapass
```

---

## 🐳 Run with Docker

```bash
docker compose up --build
```

---

## 🧪 Manual Workflow

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Scrape Telegram messages

```bash
python app/scraper/scrape_telegram.py
```

### 3. Load raw data into PostgreSQL

```bash
python app/scraper/load_raw_to_pg.py
```

### 4. Detect objects in images (YOLOv8)

```bash
python kara_detection/detect_images.py
```

### 5. Run dbt transformations

```bash
cd kara_dbt
dbt run
```

### 6. Test data models

```bash
dbt test
```

### 7. Start FastAPI server

```bash
uvicorn api.main:app --reload
```

Visit:

* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* Example: [http://localhost:8000/api/reports/top-products?limit=5](http://localhost:8000/api/reports/top-products?limit=5)

### 8. Run Dagster orchestration UI

```bash
dagster dev -f orchestrator/repository.py
```

Open Dagster UI: [http://localhost:3000](http://localhost:3000)

---

## 📊 DBT Models Overview

**Staging:**

* `stg_telegram_messages`: Cleans and prepares raw Telegram data

**Data Marts:**

* `dim_channels`: Channel metadata
* `dim_dates`: Time dimension
* `fct_messages`: Cleaned message-level data
* `fct_image_detections`: Object detection results linked to messages

---

## 🔌 API Endpoints

| Endpoint                                 | Description                     |
| ---------------------------------------- | ------------------------------- |
| `/api/reports/top-products?limit=10`     | Most frequently mentioned drugs |
| `/api/channels/{channel_name}/activity`  | Posting activity per channel    |
| `/api/search/messages?query=paracetamol` | Search messages by keyword      |

---

## ⏱️ Orchestration: Dagster Pipeline

**Ops:**

* `scrape_telegram_data()`
* `load_raw_to_postgres()`
* `run_dbt_transformations()`
* `run_yolo_enrichment()`

**Schedule:** Daily at 6:00 AM (configurable)

```bash
dagster dev
```

---

## ✅ Data Quality Checks

* `not_null`, `unique` constraints
* Custom expression:

```sql
expression_is_true: message_length > 0
```

Docs:

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

* 📡 Real-time alerts for emerging drugs/products
* 📊 BI dashboards (Metabase, Grafana)
* 🧬 NER for medicine/brand extraction
* 📦 Media classification with AI
* 📈 Time-based object detection trend analytics

---

## 📄 License

MIT License – See [`LICENSE`](./LICENSE)

---

## 👤 Author

**Dagmawi Ayenew**
🔗 [GitHub](https://github.com/Dagiayy)

````

---

