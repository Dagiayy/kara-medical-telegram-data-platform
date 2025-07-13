
# Kara Medical Telegram Data Platform

A scalable, containerized data pipeline that scrapes messages from Telegram using Python, stores the data in PostgreSQL, and prepares it for downstream analytics or monitoring.

---

## 📦 Project Structure

```

kara-medical-telegram-data-platform/
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app/
│   ├── **init**.py
│   └── scraper/
│       └── main.py
└── docker/
└── postgres

````

---

## 🚀 Features

- 🔍 Scrapes messages from Telegram channels or groups
- 🐘 Stores structured data in PostgreSQL
- 🐳 Fully containerized with Docker and Docker Compose
- 🔐 Environment variables managed securely via `.env` file
- 🔄 Easily extendable for ETL, alerts, or dashboards

---

## 🛠️ Setup & Usage

### 1. Clone the repository
```bash
git clone https://github.com/Dagiayy/kara-medical-telegram-data-platform.git
cd kara-medical-telegram-data-platform
````

### 2. Add your `.env` file

Create a `.env` file in the project root with the following:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
POSTGRES_DB=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

### 3. Build and Run with Docker

```bash
docker compose up --build
```

### 4. Run the Scraper Manually (Optional)

```bash
docker exec -it <app_container_name> python app/scraper/main.py
```

---

## 📥 Dependencies

* Python (requests, telethon, psycopg2, etc.)
* PostgreSQL
* Docker & Docker Compose

Install manually (if running outside Docker):

```bash
pip install -r requirements.txt
```

---

## 📊 Future Enhancements

* Add data cleaning and transformation layer using dbt or Pandas
* Add visualization dashboard (e.g., Metabase, Grafana)
* Build an API for accessing the stored Telegram data
* Implement data validation and logging

---

## 📄 License

MIT License. See `LICENSE` file for details.

---

## 👨‍💻 Author

* **Dagmawi Ayenew**
  [GitHub](https://https://github.com/Dagiayy/creditrust-complaint-ra) 

```

