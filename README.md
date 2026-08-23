# Kara Medical Telegram Data Platform

A data platform that scrapes public medical/pharma Telegram channels operating
in Ethiopia, enriches attached images with YOLOv8 object detection, models
the result with dbt, tags drug/product mentions in message text, and serves
it all through a FastAPI analytical API -- orchestrated end-to-end with
Dagster.

## Why

Ethiopian pharmaceutical wholesalers, cosmetics resellers, and pharmacies
coordinate almost entirely over public Telegram channels: stock
availability, pricing, and job postings all move through channels like
`@tikvahpharma` or `@lobelia4cosmetics` rather than a website or API. That
data is public but unstructured and impossible to query. This platform turns
it into something a public-health researcher, a market analyst, or a
pharmacy ops team could actually use: "which drugs are being advertised most
this month," "is a channel's posting volume spiking," "search all mentions
of paracetamol."

## Architecture

```
Telegram channels
      │  Telethon (scrape_telegram.py)
      ▼
data_lake/raw/  ─────────────────────────────┐  JSON per channel/day,
  telegram_messages/YYYY-MM-DD/*.json         │  downloaded images
  media/YYYY-MM-DD/<channel>/*.jpg            │
      │  load_raw_to_pg.py (validate, dedupe, upsert)
      ▼
Postgres: raw.telegram_messages, raw.images ──┐
      │                                       │  kara_detection.detect_images
      │  dbt (staging → marts)                │  (YOLOv8) writes
      ▼                                       ▼
Postgres: analytics.fct_messages,        raw.image_detections
  dim_channels, dim_dates,                    │
  fct_message_products  ◄── seeds/product_dictionary.csv (keyword tagging)
  fct_image_detections  ◄─────────────────────┘
      │
      ▼
FastAPI (api/) ── /api/reports, /api/search, /api/analytics/trends, /health
      │
      ▼
analytics/report.py ── Markdown data-quality & EDA report (pandas)

Dagster (orchestrator/) schedules: scrape → load → detect → dbt seed/run/test
meta.pipeline_runs records start/end/status/row-count for every stage
```

**Why these tools and not others:** dbt for transformation because the
project is small-to-medium analytical SQL over one Postgres instance -- no
justification for Spark/Airflow-scale infrastructure. Keyword-dictionary
matching (not an LLM) for product tagging because it's a well-defined
string-match problem where a reviewable, free, deterministic dictionary
beats a nondeterministic model call. No vector DB/RAG: there's no
unstructured-document Q&A use case here, `ILIKE` search already answers "find
messages mentioning X."

## Tech stack

| Layer | Tool |
|---|---|
| Ingestion | Telethon (Telegram API client) |
| Storage | PostgreSQL (`raw` operational schema, `analytics` dbt-built schema, `meta` pipeline observability) |
| Transformation | dbt-core / dbt-postgres |
| Object detection | YOLOv8 (Ultralytics), pretrained `yolov8n.pt` |
| API | FastAPI + SQLAlchemy (pooled connections) |
| Orchestration | Dagster |
| Analysis/reporting | pandas |
| Testing | pytest |
| CI | GitHub Actions (lint, unit tests, dbt build against a real Postgres service) |

## Project structure

```
app/
  config.py              # centralized Settings (env-var driven)
  logging_config.py       # shared structured logging
  observability.py        # meta.pipeline_runs tracking (context manager)
  scraper/
    scrape_telegram.py    # incremental, non-interactive-capable Telegram scraper
    load_raw_to_pg.py     # validates + upserts JSON into raw.* tables
api/
  main.py, crud.py, database.py, schemas.py   # FastAPI analytical API
kara_detection/
  detect_images.py        # YOLOv8 batch inference over raw.images
kara_dbt/
  models/staging/         # raw.telegram_messages -> stg_telegram_messages
  models/marts/           # dims, facts, product-mention bridge table
  seeds/product_dictionary.csv
  tests/                  # singular dbt data tests
analytics/
  report.py                # data-quality + EDA Markdown report generator
orchestrator/
  pipeline.py              # Dagster job wiring every stage together
tests/                     # pytest unit tests (mocked DB/YOLO -- no live services needed)
docker/postgres/init.sql   # idempotent raw/meta schema bootstrap
```

## Setup

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 15 (or Docker)
- A Telegram API ID/hash from <https://my.telegram.org>

### 2. Configure environment

```bash
cp .env.example .env
# fill in TELEGRAM_API_ID, TELEGRAM_API_HASH, and a real POSTGRES_PASSWORD
```

### 3a. Run with Docker (recommended)

```bash
docker compose up --build
```

This starts Postgres (schema bootstrapped automatically from
`docker/postgres/init.sql`), the FastAPI service on :8000, and the Dagster
webserver on :3000. The API and Dagster containers wait for Postgres's
healthcheck before starting.

Docker does **not** run the scraper automatically -- it needs either an
interactive Telegram login or `TELEGRAM_SESSION_STRING` set (see below), so
scraping/loading/detection/dbt runs happen through the Dagster UI or CLI
(`docker compose exec dagster dagster job launch -f orchestrator/repository.py -j kara_pipeline`).

### 3b. Run manually

```bash
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements-dev.txt

# start Postgres and apply the schema once:
psql -h localhost -U karauser -d kara_db -f docker/postgres/init.sql

python -m app.scraper.scrape_telegram          # first run: interactive phone login,
                                                # prints a TELEGRAM_SESSION_STRING to save to .env
python -m app.scraper.load_raw_to_pg
python -m kara_detection.detect_images

cd kara_dbt && cp profiles.yml.example profiles.yml
export DBT_PROFILES_DIR=.        # from inside kara_dbt/
dbt deps && dbt seed && dbt run && dbt test
cd ..

uvicorn api.main:app --reload
```

Visit <http://localhost:8000/docs> for interactive API docs.

### Running the orchestrated pipeline

```bash
dagster dev -f orchestrator/repository.py
```

Open <http://localhost:3000>, launch `kara_pipeline`. Runs
scrape → load → detect → dbt seed → dbt run → dbt test in order, failing
fast (via Dagster `Failure`) if any stage's subprocess exits non-zero.
**Requires `TELEGRAM_SESSION_STRING`** in the environment since this runs
unattended.

### Non-interactive Telegram login

Telethon needs a phone-verified session. Run
`python -m app.scraper.scrape_telegram` once interactively; it prints a
session string. Save it as `TELEGRAM_SESSION_STRING` in `.env` and every
subsequent run (including Docker/Dagster) logs in without a prompt.

### Tests

```bash
pytest --cov=app --cov=api --cov=kara_detection
```

Unit tests mock the database and YOLO model, so they run without any live
service. dbt's own tests (`dbt test`) need a real Postgres instance; CI runs
them against a disposable Postgres service container.

### Generating the analytics report

```bash
python -m analytics.report --out reports/latest.md
```

## API

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness + DB connectivity check |
| `GET /api/reports/top-products?limit=&offset=` | Most-mentioned drugs/products (via `fct_message_products`) |
| `GET /api/channels/{channel_name}/activity` | Daily message counts for one channel (404 if unknown) |
| `GET /api/search/messages?query=paracetamol` | Full-text `ILIKE` search over message text |
| `GET /api/analytics/trends?channel=&days=30` | Daily message volume with a z-score, flags spikes/dips |

All list endpoints are paginated (`limit`/`offset`, bounded by
`API_MAX_PAGE_SIZE`) and return typed Pydantic response models.

## dbt models

See [`kara_dbt/README.md`](kara_dbt/README.md) for the staging/marts layout
and how to extend the tracked-product dictionary.

## Data quality & observability

- `raw.telegram_messages` is upserted on `(channel, message_id)` -- reruns
  are idempotent and never lose history (the original loader `TRUNCATE`d the
  table on every run).
- dbt source freshness (`kara_dbt/models/staging/sources.yml`) flags stale
  ingestion.
- `dbt test` enforces not-null/uniqueness/referential-integrity constraints
  and one custom "no message without text or media" check.
- `meta.pipeline_runs` records every stage's start/end time, row count, and
  status/error, queryable directly in Postgres for "did last night's run
  succeed" without a separate observability stack.
- `analytics/report.py` produces a data-quality + EDA snapshot (null rates,
  duplicate check, per-channel volume, top products, top detected objects,
  a 14-day volume trend with anomaly flags).

## Security notes

- All credentials come from environment variables via `app.config.Settings`
  (pydantic-settings); nothing is hard-coded. Copy `.env.example` to `.env`
  and never commit the latter.
- `.dockerignore` keeps `.env`, `.git`, and raw scraped data out of built
  images.
- `data_lake/raw/` (scraped message text can contain phone numbers) is
  gitignored, not versioned.
- If you're setting this up from the original version of this repo: rotate
  any Telegram API credentials that may have been committed previously.

## Limitations & future improvements

- Product/drug tagging is dictionary-based; it will miss misspellings and
  transliterations. A fuzzy-matching or fine-tuned NER pass would improve
  recall, at the cost of reproducibility -- deliberately deferred until the
  dictionary approach's precision is validated against real usage.
- No BI dashboard (Metabase/Grafana) is included; `analytics/report.py` and
  the `/api/analytics/trends` endpoint cover the current reporting need
  without adding another service to operate.
- Dagster schedule assumes a single-tenant deployment; no multi-tenant
  channel-list configuration yet.

## License

MIT -- see [`LICENSE`](./LICENSE).

## Author

**Dagmawi Ayenew** -- [GitHub](https://github.com/Dagiayy)
