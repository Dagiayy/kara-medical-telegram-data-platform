-- Idempotent schema bootstrap for the operational (raw) layer.
-- dbt owns everything downstream of `raw.*` (staging/marts in the
-- `staging`/`analytics` schemas); this script only creates the tables that
-- Python writes into directly, plus lightweight pipeline-run observability.
--
-- Mounted into /docker-entrypoint-initdb.d so the official postgres image
-- runs it automatically on first container start. Also safe to re-run by
-- hand (`psql -f docker/postgres/init.sql`) against an existing database.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS meta;

CREATE TABLE IF NOT EXISTS raw.telegram_messages (
    channel         TEXT NOT NULL,
    message_id      BIGINT NOT NULL,
    sent_at         TIMESTAMPTZ,
    sender_id       TEXT,
    message_text    TEXT,
    media_type      TEXT,
    media_url       TEXT,
    media_size_kb   REAL,
    width           INT,
    height          INT,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (channel, message_id)
);

CREATE INDEX IF NOT EXISTS idx_telegram_messages_sent_at
    ON raw.telegram_messages (sent_at);

CREATE TABLE IF NOT EXISTS raw.images (
    image_id        SERIAL PRIMARY KEY,
    channel         TEXT NOT NULL,
    message_id      BIGINT NOT NULL,
    image_path      TEXT NOT NULL,
    processed       BOOLEAN NOT NULL DEFAULT FALSE,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (channel, message_id, image_path),
    FOREIGN KEY (channel, message_id)
        REFERENCES raw.telegram_messages (channel, message_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_images_unprocessed
    ON raw.images (processed) WHERE processed = FALSE;

CREATE TABLE IF NOT EXISTS raw.image_detections (
    detection_id            SERIAL PRIMARY KEY,
    image_id                INT NOT NULL REFERENCES raw.images (image_id) ON DELETE CASCADE,
    channel                 TEXT NOT NULL,
    message_id              BIGINT NOT NULL,
    detected_object_class   TEXT NOT NULL,
    confidence_score        FLOAT NOT NULL,
    detected_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_image_detections_message
    ON raw.image_detections (channel, message_id);

-- Pipeline run ledger: what ran, when, on how much data, and whether it
-- succeeded -- the minimum needed to answer "did last night's run work?"
-- without standing up a full observability stack.
CREATE TABLE IF NOT EXISTS meta.pipeline_runs (
    run_id           SERIAL PRIMARY KEY,
    pipeline_stage   TEXT NOT NULL,
    started_at       TIMESTAMPTZ NOT NULL,
    finished_at      TIMESTAMPTZ,
    status           TEXT NOT NULL DEFAULT 'running'
                       CHECK (status IN ('running', 'success', 'failed')),
    rows_processed   INT,
    error_message    TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_stage_started
    ON meta.pipeline_runs (pipeline_stage, started_at DESC);
