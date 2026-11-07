from db import get_db_connection

def add(user_id: int, article_id: int) -> None:
    """Like an article. Liking it again keeps the single row the primary key allows."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO LIKES (user_id, article_id) VALUES (%s, %s) '
            'ON DUPLICATE KEY UPDATE user_id = user_id',
            (user_id, article_id)
        )
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def remove(user_id: int, article_id: int) -> None:
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM LIKES WHERE user_id = %s AND article_id = %s',
            (user_id, article_id)
        )
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def count(article_id: int) -> int:
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM LIKES WHERE article_id = %s',
            (article_id,)
        )
        return cursor.fetchone()[0]
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
