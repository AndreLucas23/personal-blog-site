"""Apply the pending database migrations: python src/migrate.py"""
import re
import sys
from pathlib import Path

from db import db_cursor

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / 'migrations'
FILE_NAME = re.compile(r'^(\d{3})_[a-z0-9_]+\.sql$')

CREATE_HISTORY_TABLE = """
    CREATE TABLE IF NOT EXISTS SCHEMA_MIGRATIONS (
        version INT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


class MigrationError(Exception):
    pass


def find_migrations(directory: Path) -> dict[int, Path]:
    migrations: dict[int, Path] = {}
    for path in sorted(directory.glob('*.sql')):
        match = FILE_NAME.match(path.name)
        if not match:
            raise MigrationError(
                f'{path.name} is not named like 002_short_description.sql.'
            )

        version = int(match.group(1))
        if version in migrations:
            raise MigrationError(
                f'{migrations[version].name} and {path.name} have the same number.'
            )
        migrations[version] = path

    return migrations


def applied_versions() -> set[int]:
    with db_cursor() as cursor:
        cursor.execute(CREATE_HISTORY_TABLE)
        cursor.execute('SELECT version FROM SCHEMA_MIGRATIONS')
        return {row[0] for row in cursor.fetchall()}


def run_script(cursor, sql: str) -> None:
    cursor.execute(sql)
    # A file holds several statements, and each result must be read before the next.
    while True:
        if cursor.with_rows:
            cursor.fetchall()
        if not cursor.nextset():
            break


def apply_migration(version: int, path: Path) -> None:
    try:
        with db_cursor() as cursor:
            run_script(cursor, path.read_text(encoding='utf-8'))
            cursor.execute(
                'INSERT INTO SCHEMA_MIGRATIONS (version, name) VALUES (%s, %s)',
                (version, path.name),
            )
    except Exception as error:
        raise MigrationError(f'{path.name} failed: {error}') from error


def apply_pending(directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply the migrations not recorded yet, in order, and return their names."""
    migrations = find_migrations(directory)
    applied = applied_versions()

    names = []
    for version in sorted(migrations):
        if version in applied:
            continue
        apply_migration(version, migrations[version])
        print(f'Applied {migrations[version].name}.')
        names.append(migrations[version].name)

    return names


def main() -> None:
    try:
        names = apply_pending()
    except MigrationError as error:
        sys.exit(str(error))

    if not names:
        print('The database is up to date.')


if __name__ == '__main__':
    main()
