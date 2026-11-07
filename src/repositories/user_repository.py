from db import get_db_connection

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
