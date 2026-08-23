"""Query layer for the analytical API.

All queries target the corrected `analytics` schema built by dbt
(kara_dbt/models/marts). The original version of this module queried
`fct_messages.product_name` (a column that was never created by anything --
"top products" could never have returned data) and joined on
`dim_channels.channel_id` / `fct_messages.timestamp`, neither of which
existed in the dbt models it was supposedly reading from.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def get_top_products(conn: Connection, limit: int, offset: int) -> list[dict]:
    rows = conn.execute(
        text(
            """
            SELECT product_name, category, COUNT(*) AS mention_count
            FROM analytics.fct_message_products
            GROUP BY product_name, category
            ORDER BY mention_count DESC, product_name
            LIMIT :limit OFFSET :offset;
            """
        ),
        {"limit": limit, "offset": offset},
    )
    return [dict(r._mapping) for r in rows]


def channel_exists(conn: Connection, channel_name: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM analytics.dim_channels WHERE channel_name = :channel LIMIT 1;"),
        {"channel": channel_name},
    ).first()
    return row is not None


def get_channel_activity(conn: Connection, channel_name: str, limit: int, offset: int) -> list[dict]:
    rows = conn.execute(
        text(
            """
            SELECT m.date_id AS date, COUNT(*) AS message_count
            FROM analytics.fct_messages m
            JOIN analytics.dim_channels c ON m.channel_id = c.channel_id
            WHERE c.channel_name = :channel
            GROUP BY m.date_id
            ORDER BY m.date_id DESC
            LIMIT :limit OFFSET :offset;
            """
        ),
        {"channel": channel_name, "limit": limit, "offset": offset},
    )
    return [dict(r._mapping) for r in rows]


def search_messages(conn: Connection, query: str, limit: int, offset: int) -> list[dict]:
    rows = conn.execute(
        text(
            """
            SELECT message_id, channel, message_text, sent_at
            FROM analytics.fct_messages
            WHERE message_text ILIKE :pattern
            ORDER BY sent_at DESC
            LIMIT :limit OFFSET :offset;
            """
        ),
        {"pattern": f"%{query}%", "limit": limit, "offset": offset},
    )
    return [dict(r._mapping) for r in rows]


def get_daily_message_trend(conn: Connection, channel_name: str | None, days: int) -> list[dict]:
    """Daily message counts with a rolling z-score, so spikes/dips are flagged
    without pulling in a forecasting library for a signal this simple."""
    rows = conn.execute(
        text(
            """
            with daily as (
                select
                    m.date_id as date,
                    count(*) as message_count
                from analytics.fct_messages m
                join analytics.dim_channels c on m.channel_id = c.channel_id
                where (:channel is null or c.channel_name = :channel)
                group by m.date_id
            ),
            stats as (
                select avg(message_count) as mean_count, stddev_pop(message_count) as stddev_count
                from daily
            )
            select
                daily.date,
                daily.message_count,
                case
                    when stats.stddev_count is null or stats.stddev_count = 0 then 0
                    else round(((daily.message_count - stats.mean_count) / stats.stddev_count)::numeric, 2)
                end as z_score
            from daily, stats
            order by daily.date desc
            limit :days;
            """
        ),
        {"channel": channel_name, "days": days},
    )
    return [dict(r._mapping) for r in rows]
