import os
import time

import mysql.connector
import pytest

import migrate
from db import get_db_connection
from helpers import ADMIN, READER, create_user, login

TEST_DATABASE_FLAG = 'BLOG_TEST_DATABASE'
TABLES = ('LIKES', 'ARTICLES', 'USERS', 'FAILED_LOGINS')
DB_WAIT_SECONDS = 60


def pytest_configure(config):
    # The suite wipes every table, so it only runs against a database set up for it.
    if os.environ.get(TEST_DATABASE_FLAG) != '1':
        pytest.exit(
            f'Refusing to run: set {TEST_DATABASE_FLAG}=1 and point DB_* at a '
            'disposable test database. '
            'Use "docker compose --profile test run --rm tests".',
            returncode=2,
        )
    os.environ.setdefault('SECRET_KEY', 'test-secret-key')


def wait_for_database():
    deadline = time.monotonic() + DB_WAIT_SECONDS
    while True:
        try:
            return get_db_connection()
        except mysql.connector.Error:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)


def run_sql(*statements: str) -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for statement in statements:
            cursor.execute(statement)
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def drop_all_tables() -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SHOW TABLES')
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
    finally:
        conn.close()

    run_sql(
        'SET FOREIGN_KEY_CHECKS = 0',
        *(f'DROP TABLE `{table}`' for table in tables),
        'SET FOREIGN_KEY_CHECKS = 1',
    )


@pytest.fixture(scope='session', autouse=True)
def schema():
    wait_for_database().close()
    drop_all_tables()
    migrate.apply_pending()


@pytest.fixture
def empty_database(schema):
    """A database without tables, which gets the real schema back afterwards."""
    drop_all_tables()
    yield
    drop_all_tables()
    migrate.apply_pending()


@pytest.fixture(autouse=True)
def clean_tables(schema):
    run_sql(
        'SET FOREIGN_KEY_CHECKS = 0',
        *(f'TRUNCATE TABLE {table}' for table in TABLES),
        'SET FOREIGN_KEY_CHECKS = 1',
    )


@pytest.fixture
def app():
    from app import app as flask_app

    # Most tests post without a token. tests/test_csrf.py switches the check on.
    flask_app.config.update(TESTING=True, CSRF_ENABLED=False)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_id() -> int:
    return create_user(
        ADMIN['username'], ADMIN['email'], ADMIN['password'], is_admin=True
    )


@pytest.fixture
def reader_id() -> int:
    return create_user(READER['username'], READER['email'], READER['password'])


@pytest.fixture
def admin_client(app, admin_id):
    client = app.test_client()
    login(client, ADMIN['email'], ADMIN['password'])
    return client


@pytest.fixture
def reader_client(app, reader_id):
    client = app.test_client()
    login(client, READER['email'], READER['password'])
    return client
