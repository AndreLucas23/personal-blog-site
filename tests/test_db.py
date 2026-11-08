import pytest

from db import db_cursor


class Boom(Exception):
    pass


def count_users() -> int:
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM USERS')
        return cursor.fetchone()[0]


def insert_user(cursor, email: str) -> None:
    cursor.execute(
        'INSERT INTO USERS (username, email, password_hash) VALUES (%s, %s, %s)',
        ('Ana', email, 'hash'),
    )


def test_db_cursor_commits_when_the_block_succeeds():
    with db_cursor() as cursor:
        insert_user(cursor, 'ana@example.com')

    assert count_users() == 1


def test_db_cursor_rolls_back_and_reraises_when_the_block_fails():
    with pytest.raises(Boom):
        with db_cursor() as cursor:
            insert_user(cursor, 'ana@example.com')
            raise Boom

    assert count_users() == 0


def test_db_cursor_returns_dictionaries_on_request():
    with db_cursor(dictionary=True) as cursor:
        cursor.execute('SELECT 1 AS one')
        assert cursor.fetchone() == {'one': 1}
