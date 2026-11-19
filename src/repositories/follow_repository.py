import mysql.connector

from db import db_cursor

MISSING_REFERENCE_ERROR = 1452


def follow(follower_id: int, followed_id: int) -> bool:
    """Follow a member. Following again keeps the single row the primary key allows.

    False when the member no longer exists, such as an account removed during the request.
    """
    try:
        with db_cursor() as cursor:
            cursor.execute(
                'INSERT INTO FOLLOWS (follower_id, followed_id) VALUES (%s, %s) '
                'ON DUPLICATE KEY UPDATE follower_id = follower_id',
                (follower_id, followed_id)
            )
    except mysql.connector.IntegrityError as error:
        if error.errno != MISSING_REFERENCE_ERROR:
            raise
        return False
    return True


def unfollow(follower_id: int, followed_id: int) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            'DELETE FROM FOLLOWS WHERE follower_id = %s AND followed_id = %s',
            (follower_id, followed_id)
        )


def is_following(follower_id: int, followed_id: int) -> bool:
    with db_cursor() as cursor:
        cursor.execute(
            'SELECT 1 FROM FOLLOWS WHERE follower_id = %s AND followed_id = %s',
            (follower_id, followed_id)
        )
        return cursor.fetchone() is not None


def count_followers(user_id: int) -> int:
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM FOLLOWS WHERE followed_id = %s', (user_id,))
        return cursor.fetchone()[0]
