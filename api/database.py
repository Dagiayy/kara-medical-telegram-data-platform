# api/database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="kara_db",
        user="karauser",
        password="karapass",
        cursor_factory=RealDictCursor
    )
