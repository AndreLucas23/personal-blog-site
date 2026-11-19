import mysql.connector

from db import db_cursor

DUPLICATE_ENTRY_ERROR = 1062
USERNAME_KEY = 'uq_users_username'
ACCOUNT_COLUMNS = 'user_id, username, display_name, email, password_hash, is_admin, avatar_path'
PROFILE_QUERY = (
    'SELECT u.user_id, u.username, u.display_name, u.email, u.headline, u.bio, '
    'u.location, u.website, u.avatar_path, u.created_at, '
    '(SELECT COUNT(*) FROM ARTICLES a WHERE a.author_id = u.user_id) AS article_count '
    'FROM USERS u'
)
# The only columns members change through their profile, in the order of the form.
PROFILE_COLUMNS = ('display_name', 'username', 'headline', 'bio', 'location', 'website')


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

def get_profile(username: str) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(PROFILE_QUERY + ' WHERE u.username = %s', (username,))
        return cursor.fetchone()

def get_profile_by_id(user_id: int) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(PROFILE_QUERY + ' WHERE u.user_id = %s', (user_id,))
        return cursor.fetchone()

def update_profile(user_id: int, changes: dict[str, str | None]) -> None:
    columns = [column for column in PROFILE_COLUMNS if column in changes]
    if not columns:
        return

    assignments = ', '.join(f'{column} = %s' for column in columns)
    try:
        with db_cursor() as cursor:
            cursor.execute(
                f'UPDATE USERS SET {assignments} WHERE user_id = %s',
                (*(changes[column] for column in columns), user_id)
            )
    except mysql.connector.IntegrityError as error:
        if error.errno != DUPLICATE_ENTRY_ERROR:
            raise
        raise DuplicateUsernameError(changes.get('username')) from error

def set_avatar(user_id: int, avatar_path: str | None) -> str | None:
    """Store the new avatar and return the previous one, so its file can be removed."""
    with db_cursor() as cursor:
        # The lock keeps two uploads at once from losing track of a file.
        cursor.execute('SELECT avatar_path FROM USERS WHERE user_id = %s FOR UPDATE', (user_id,))
        row = cursor.fetchone()
        cursor.execute(
            'UPDATE USERS SET avatar_path = %s WHERE user_id = %s', (avatar_path, user_id)
        )
        return row[0] if row else None

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
