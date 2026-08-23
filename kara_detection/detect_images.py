"""Runs YOLOv8 object detection over unprocessed scraped images.

Reads pending rows from raw.images (populated by
app.scraper.load_raw_to_pg), writes results to raw.image_detections, and
marks each image processed -- idempotent, so a failed run can simply be
re-invoked.

`raw.image_detections` is intentionally an operational table owned by this
script, not a dbt model: dbt's `fct_image_detections` mart (in kara_dbt)
reads *from* it. Making the mart a plain SELECT keeps dbt in charge of the
analytical layer while this script owns writing detection results, instead
of the two fighting over who creates/owns the table.
"""
import argparse
import os

import psycopg2
from psycopg2.extras import execute_values
from ultralytics import YOLO

from app.config import get_settings
from app.logging_config import setup_logging
from app.observability import track_pipeline_run

settings = get_settings()
logger = setup_logging("detect_images", settings.log_level, settings.log_json)

_model = None


def get_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO(settings.yolo_model_path)
    return _model


def get_unprocessed_images(conn, limit: int) -> list[tuple[int, str, str, int]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT image_id, channel, message_id, image_path
            FROM raw.images
            WHERE processed = FALSE
            ORDER BY image_id
            LIMIT %s;
            """,
            (limit,),
        )
        return cur.fetchall()


def detect_objects(image_path: str, confidence_threshold: float) -> list[dict]:
    model = get_model()
    results = model(image_path, verbose=False)
    detections = []
    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf < confidence_threshold:
                continue
            cls_id = int(box.cls[0])
            detections.append({"class_name": model.names[cls_id], "confidence_score": conf})
    return detections


def save_detections(conn, image_id: int, channel: str, message_id: int, detections: list[dict]) -> None:
    if not detections:
        return
    rows = [
        (image_id, channel, message_id, d["class_name"], d["confidence_score"])
        for d in detections
    ]
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO raw.image_detections
                (image_id, channel, message_id, detected_object_class, confidence_score)
            VALUES %s;
            """,
            rows,
        )


def mark_image_processed(conn, image_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE raw.images SET processed = TRUE WHERE image_id = %s;", (image_id,))


def run(limit: int = 500) -> int:
    conn = psycopg2.connect(**settings.sync_dsn)
    processed_count = 0
    try:
        images = get_unprocessed_images(conn, limit)
        logger.info(f"Found {len(images)} unprocessed images.")

        for image_id, channel, message_id, image_path in images:
            # Scraper output stores a project-relative path with forward
            # slashes regardless of OS -- resolve it against the repo root.
            resolved_path = os.path.normpath(image_path)
            if not os.path.exists(resolved_path):
                logger.warning(f"Image {image_id} missing on disk, skipping: {resolved_path}")
                mark_image_processed(conn, image_id)  # don't retry a file that will never appear
                conn.commit()
                continue

            try:
                detections = detect_objects(resolved_path, settings.yolo_confidence_threshold)
                save_detections(conn, image_id, channel, message_id, detections)
                mark_image_processed(conn, image_id)
                conn.commit()
                processed_count += 1
                logger.info(f"image_id={image_id}: {len(detections)} detection(s) above threshold")
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to process image_id={image_id} ({resolved_path}): {e}")

        return processed_count
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run YOLOv8 detection over unprocessed images.")
    parser.add_argument("--limit", type=int, default=500, help="Max images to process this run")
    args = parser.parse_args()

    with track_pipeline_run("detect_images") as pipeline_run:
        count = run(limit=args.limit)
        pipeline_run.rows_processed = count
        logger.info(f"Processed {count} images.")


if __name__ == "__main__":
    main()
