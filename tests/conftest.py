import os
import re
import time
from pathlib import Path

import mysql.connector
import pytest

from db import get_db_connection
from helpers import ADMIN, READER, create_user, login

TEST_DATABASE_FLAG = 'BLOG_TEST_DATABASE'
SCHEMA_PATH = Path(__file__).resolve().parent.parent / 'sql-init' / 'schema.sql'
TABLES = ('LIKES', 'ARTICLES', 'USERS')
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


def schema_statements() -> list[str]:
    """The table definitions of the real schema, without the database selection."""
    sql = SCHEMA_PATH.read_text(encoding='utf-8')
    statements = [part.strip() for part in sql.split(';') if part.strip()]
    skipped = re.compile(r'^(SET NAMES|CREATE DATABASE|USE)\b', re.IGNORECASE)
    return [statement for statement in statements if not skipped.match(statement)]


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


@pytest.fixture(scope='session', autouse=True)
def schema():
    wait_for_database().close()
    run_sql(
        'SET FOREIGN_KEY_CHECKS = 0',
        *(f'DROP TABLE IF EXISTS {table}' for table in TABLES),
        'SET FOREIGN_KEY_CHECKS = 1',
        *schema_statements(),
    )


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

    flask_app.config.update(TESTING=True)
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
