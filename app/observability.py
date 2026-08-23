"""Lightweight pipeline-run tracking against meta.pipeline_runs.

Answers "what ran, when, on how much data, did it succeed" for every stage
without standing up a metrics/tracing stack the project doesn't need yet.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg2

from app.config import get_settings

settings = get_settings()


class PipelineRun:
    def __init__(self):
        self.rows_processed: int = 0


@contextmanager
def track_pipeline_run(stage_name: str) -> Iterator[PipelineRun]:
    """Records a row in meta.pipeline_runs spanning the `with` block.

    Usage:
        with track_pipeline_run("load_raw_to_pg") as run:
            ...
            run.rows_processed = 123
    """
    started_at = datetime.now(timezone.utc)
    run = PipelineRun()
    run_id: int | None = None

    try:
        conn = psycopg2.connect(**settings.sync_dsn)
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO meta.pipeline_runs (pipeline_stage, started_at, status)
                VALUES (%s, %s, 'running')
                RETURNING run_id;
                """,
                (stage_name, started_at),
            )
            run_id = cur.fetchone()[0]
    except Exception:
        conn = None  # DB not reachable (e.g. running a unit test) -- degrade silently

    try:
        yield run
        status, error_message = "success", None
    except Exception as e:
        status, error_message = "failed", str(e)
        raise
    finally:
        if run_id is not None:
            try:
                with psycopg2.connect(**settings.sync_dsn) as conn2, conn2.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE meta.pipeline_runs
                        SET finished_at = %s, status = %s, rows_processed = %s, error_message = %s
                        WHERE run_id = %s;
                        """,
                        (datetime.now(timezone.utc), status, run.rows_processed, error_message, run_id),
                    )
            except Exception:
                pass  # never let observability plumbing mask the real pipeline error
