"""Data-quality and EDA report over the analytics schema.

Deliberately not another API endpoint: this is an operator-facing report
(run ad hoc or on a schedule) answering "is the data healthy and what does
it look like", not a request/response query. Prints Markdown to stdout by
default so it's easy to pipe into a file, Slack message, or CI artifact.

    python -m analytics.report --out reports/latest.md
"""
import argparse
import sys
from datetime import datetime, timezone
from io import StringIO

import pandas as pd
from sqlalchemy import create_engine, text

from app.config import get_settings

settings = get_settings()


def _fetch(engine, sql: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


def data_quality_section(engine) -> str:
    messages = _fetch(engine, "select * from analytics.fct_messages")
    buf = StringIO()
    buf.write("## Data Quality\n\n")

    if messages.empty:
        buf.write("No rows in `analytics.fct_messages` -- run the ingestion pipeline first.\n\n")
        return buf.getvalue()

    total = len(messages)
    null_text = messages["message_text"].isna().sum()
    dupes = messages.duplicated(subset=["message_id"]).sum()
    by_channel = messages.groupby("channel").size().sort_values(ascending=False)

    buf.write(f"- Total messages: **{total}**\n")
    buf.write(f"- Null message text: **{null_text}** ({null_text / total:.1%})\n")
    buf.write(f"- Duplicate `message_id` (should always be 0): **{dupes}**\n")
    buf.write(f"- Date range: **{messages['sent_at'].min()}** to **{messages['sent_at'].max()}**\n\n")
    buf.write("### Messages per channel\n\n")
    buf.write(by_channel.to_frame("messages").to_markdown() + "\n\n")
    return buf.getvalue()


def product_mentions_section(engine) -> str:
    products = _fetch(
        engine,
        "select product_name, category, count(*) as mentions "
        "from analytics.fct_message_products group by 1, 2 order by mentions desc limit 15",
    )
    buf = StringIO()
    buf.write("## Top Product/Drug Mentions\n\n")
    if products.empty:
        buf.write("No product mentions found (check kara_dbt/seeds/product_dictionary.csv coverage).\n\n")
    else:
        buf.write(products.to_markdown(index=False) + "\n\n")
    return buf.getvalue()


def detection_section(engine) -> str:
    detections = _fetch(
        engine,
        "select detected_object_class, count(*) as detections, avg(confidence_score) as avg_confidence "
        "from analytics.fct_image_detections group by 1 order by detections desc limit 15",
    )
    buf = StringIO()
    buf.write("## Top Detected Objects (YOLOv8)\n\n")
    if detections.empty:
        buf.write("No image detections found -- run kara_detection.detect_images.\n\n")
    else:
        detections["avg_confidence"] = detections["avg_confidence"].round(3)
        buf.write(detections.to_markdown(index=False) + "\n\n")
    return buf.getvalue()


def trend_section(engine) -> str:
    trend = _fetch(
        engine,
        """
        with daily as (
            select date_id as date, count(*) as message_count
            from analytics.fct_messages group by 1
        ),
        stats as (select avg(message_count) as mean, stddev_pop(message_count) as sd from daily)
        select daily.*, (daily.message_count - stats.mean) / nullif(stats.sd, 0) as z_score
        from daily, stats order by date desc limit 14
        """,
    )
    buf = StringIO()
    buf.write("## Daily Volume (last 14 days) -- anomaly z-score\n\n")
    if trend.empty:
        buf.write("Not enough data to compute a trend.\n\n")
    else:
        trend["z_score"] = trend["z_score"].round(2)
        anomalies = trend[trend["z_score"].abs() >= 2]
        buf.write(trend.to_markdown(index=False) + "\n\n")
        if not anomalies.empty:
            buf.write(f"**{len(anomalies)} day(s) flagged as anomalous (|z| >= 2).**\n\n")
    return buf.getvalue()


def build_report() -> str:
    engine = create_engine(settings.database_url)
    generated_at = datetime.now(timezone.utc).isoformat()
    sections = [
        f"# Kara Medical Data Platform -- Report\n\n_Generated {generated_at}_\n\n",
        data_quality_section(engine),
        product_mentions_section(engine),
        detection_section(engine),
        trend_section(engine),
    ]
    return "".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a data-quality & EDA report.")
    parser.add_argument("--out", type=str, default=None, help="Write to this file instead of stdout")
    args = parser.parse_args()

    report = build_report()
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.out}")
    else:
        sys.stdout.write(report)


if __name__ == "__main__":
    main()
