import mysql.connector

from db import db_cursor

DUPLICATE_ENTRY_ERROR = 1062


class DuplicateEmailError(Exception):
    pass


def get_by_id(user_id: int) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            'SELECT user_id, username, email, password_hash, is_admin '
            'FROM USERS WHERE user_id = %s',
            (user_id,)
        )
        return cursor.fetchone()

def get_by_email(email: str) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            'SELECT user_id, username, email, password_hash, is_admin '
            'FROM USERS WHERE email = %s',
            (email,)
        )
        return cursor.fetchone()

def create(
    username: str, email: str, password_hash: str, is_admin: bool = False
) -> int:
    try:
        with db_cursor() as cursor:
            cursor.execute(
                'INSERT INTO USERS (username, email, password_hash, is_admin) '
                'VALUES (%s, %s, %s, %s)',
                (username, email, password_hash, int(is_admin))
            )
            return cursor.lastrowid
    except mysql.connector.IntegrityError as error:
        if error.errno != DUPLICATE_ENTRY_ERROR:
            raise
        raise DuplicateEmailError(email) from error
