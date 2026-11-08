import os
from collections.abc import Generator
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv
from mysql.connector.constants import ClientFlag

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset='utf8mb4',
        # Count matched rows on UPDATE, so unchanged values are not a missing row.
        client_flags=[ClientFlag.FOUND_ROWS],
    )

@contextmanager
def db_cursor(dictionary: bool = False) -> Generator:
    """Yield a cursor, commit when the block succeeds and roll back when it raises."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conn.close()
