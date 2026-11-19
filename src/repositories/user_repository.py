import mysql.connector

from db import db_cursor

DUPLICATE_ENTRY_ERROR = 1062
USERNAME_KEY = 'uq_users_username'
ACCOUNT_COLUMNS = 'user_id, username, display_name, email, password_hash, is_admin'


class DuplicateEmailError(Exception):
    pass


class DuplicateUsernameError(Exception):
    pass


def get_by_id(user_id: int) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(f'SELECT {ACCOUNT_COLUMNS} FROM USERS WHERE user_id = %s', (user_id,))
        return cursor.fetchone()

def get_by_email(email: str) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(f'SELECT {ACCOUNT_COLUMNS} FROM USERS WHERE email = %s', (email,))
        return cursor.fetchone()

def get_by_username(username: str) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(f'SELECT {ACCOUNT_COLUMNS} FROM USERS WHERE username = %s', (username,))
        return cursor.fetchone()

def get_by_login(login: str) -> dict | None:
    """Find a member by email or by username, as the login form accepts either one."""
    if '@' in login:
        return get_by_email(login)
    return get_by_username(login)

def create(
    display_name: str,
    username: str,
    email: str,
    password_hash: str,
    is_admin: bool = False,
) -> int:
    try:
        with db_cursor() as cursor:
            cursor.execute(
                'INSERT INTO USERS (display_name, username, email, password_hash, is_admin) '
                'VALUES (%s, %s, %s, %s, %s)',
                (display_name, username, email, password_hash, int(is_admin))
            )
            return cursor.lastrowid
    except mysql.connector.IntegrityError as error:
        if error.errno != DUPLICATE_ENTRY_ERROR:
            raise
        # The message names the unique key that refused the row.
        if USERNAME_KEY in (error.msg or ''):
            raise DuplicateUsernameError(username) from error
        raise DuplicateEmailError(email) from error
