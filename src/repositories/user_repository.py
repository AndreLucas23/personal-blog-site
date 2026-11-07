import mysql.connector

from db import get_db_connection

DUPLICATE_ENTRY_ERROR = 1062


class DuplicateEmailError(Exception):
    pass


def get_by_id(user_id: int) -> dict | None:
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT user_id, username, email, password_hash, is_admin '
            'FROM USERS WHERE user_id = %s',
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_by_email(email: str) -> dict | None:
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT user_id, username, email, password_hash, is_admin '
            'FROM USERS WHERE email = %s',
            (email,)
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create(
    username: str, email: str, password_hash: str, is_admin: bool = False
) -> int:
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO USERS (username, email, password_hash, is_admin) '
            'VALUES (%s, %s, %s, %s)',
            (username, email, password_hash, int(is_admin))
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.IntegrityError as error:
        if error.errno != DUPLICATE_ENTRY_ERROR:
            raise
        raise DuplicateEmailError(email) from error
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
