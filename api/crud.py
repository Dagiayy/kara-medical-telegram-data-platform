# api/crud.py
from .database import get_db_connection

def get_top_products(limit: int = 10):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT product_name, COUNT(*) AS mention_count
        FROM fct_messages
        WHERE product_name IS NOT NULL
        GROUP BY product_name
        ORDER BY mention_count DESC
        LIMIT %s;
    """, (limit,))
    result = cur.fetchall()
    conn.close()
    return result

def get_channel_activity(channel_name: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(timestamp) AS date, COUNT(*) AS message_count
        FROM fct_messages m
        JOIN dim_channels c ON m.channel_id = c.channel_id
        WHERE c.channel_name = %s
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp);
    """, (channel_name,))
    result = cur.fetchall()
    conn.close()
    return result

def search_messages(query: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT message_id, message_text, timestamp
        FROM fct_messages
        WHERE message_text ILIKE %s
        ORDER BY timestamp DESC
        LIMIT 50;
    """, (f"%{query}%",))
    result = cur.fetchall()
    conn.close()
    return result
