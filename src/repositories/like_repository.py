from db import db_cursor

def add(user_id: int, article_id: int) -> None:
    """Like an article. Liking it again keeps the single row the primary key allows."""
    with db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO LIKES (user_id, article_id) VALUES (%s, %s) '
            'ON DUPLICATE KEY UPDATE user_id = user_id',
            (user_id, article_id)
        )

def remove(user_id: int, article_id: int) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            'DELETE FROM LIKES WHERE user_id = %s AND article_id = %s',
            (user_id, article_id)
        )

def count(article_id: int) -> int:
    with db_cursor() as cursor:
        cursor.execute(
            'SELECT COUNT(*) FROM LIKES WHERE article_id = %s',
            (article_id,)
        )
        return cursor.fetchone()[0]
