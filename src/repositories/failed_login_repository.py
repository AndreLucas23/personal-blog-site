from db import db_cursor

MAX_LOGIN_LENGTH = 255


def _key(login: str, ip_address: str) -> tuple[str, str]:
    # The form accepts any text, and a longer value would not fit the column.
    return login[:MAX_LOGIN_LENGTH], ip_address


def count_recent(login: str, ip_address: str, window_minutes: int) -> int:
    with db_cursor() as cursor:
        cursor.execute(
            'SELECT COUNT(*) FROM FAILED_LOGINS '
            'WHERE login = %s AND ip_address = %s '
            'AND attempted_at > NOW() - INTERVAL %s MINUTE',
            (*_key(login, ip_address), window_minutes)
        )
        return cursor.fetchone()[0]

def add(login: str, ip_address: str, window_minutes: int) -> None:
    with db_cursor() as cursor:
        # Attempts outside the window no longer count, for any account.
        cursor.execute(
            'DELETE FROM FAILED_LOGINS '
            'WHERE attempted_at <= NOW() - INTERVAL %s MINUTE',
            (window_minutes,)
        )
        cursor.execute(
            'INSERT INTO FAILED_LOGINS (login, ip_address) VALUES (%s, %s)',
            _key(login, ip_address)
        )

def clear(login: str, ip_address: str) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            'DELETE FROM FAILED_LOGINS WHERE login = %s AND ip_address = %s',
            _key(login, ip_address)
        )
