import pytest

import migrate
from db import db_cursor


def write_migration(directory, name: str, sql: str) -> None:
    (directory / name).write_text(sql, encoding='utf-8')


def table_names() -> set[str]:
    with db_cursor() as cursor:
        cursor.execute('SHOW TABLES')
        return {row[0] for row in cursor.fetchall()}


def recorded_migrations() -> list[tuple[int, str]]:
    with db_cursor() as cursor:
        cursor.execute('SELECT version, name FROM SCHEMA_MIGRATIONS ORDER BY version')
        return cursor.fetchall()


def test_migrations_create_the_schema_on_an_empty_database(empty_database):
    names = migrate.apply_pending()

    assert names == sorted(path.name for path in migrate.MIGRATIONS_DIR.glob('*.sql'))
    assert names[0] == '001_initial_schema.sql'
    assert {'USERS', 'ARTICLES', 'LIKES'} <= table_names()
    assert [name for _, name in recorded_migrations()] == names


def test_applying_again_changes_nothing(empty_database):
    migrate.apply_pending()
    recorded = recorded_migrations()

    assert migrate.apply_pending() == []
    assert recorded_migrations() == recorded


def test_database_created_before_migrations_keeps_its_data(empty_database, tmp_path):
    initial_schema = migrate.MIGRATIONS_DIR / '001_initial_schema.sql'
    write_migration(tmp_path, initial_schema.name, initial_schema.read_text('utf-8'))
    migrate.apply_pending(tmp_path)
    with db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO USERS (username, email, password_hash) VALUES (%s, %s, %s)',
            ('Ana', 'ana@example.com', 'hash'),
        )
        # The first tables without the history are what the old schema file left.
        cursor.execute('DROP TABLE SCHEMA_MIGRATIONS')

    names = migrate.apply_pending()

    assert names == sorted(path.name for path in migrate.MIGRATIONS_DIR.glob('*.sql'))
    with db_cursor() as cursor:
        cursor.execute('SELECT email FROM USERS')
        assert cursor.fetchall() == [('ana@example.com',)]


def test_only_pending_migrations_are_applied_in_order(empty_database, tmp_path):
    write_migration(
        tmp_path,
        '002_add_note_body.sql',
        "ALTER TABLE NOTES ADD COLUMN body VARCHAR(20) NOT NULL DEFAULT 'a;b';",
    )
    write_migration(
        tmp_path,
        '001_create_notes.sql',
        '-- Two statements; the comment has a semicolon too.\n'
        'CREATE TABLE NOTES (note_id INT PRIMARY KEY);\n'
        'INSERT INTO NOTES (note_id) VALUES (1);\n',
    )
    assert migrate.apply_pending(tmp_path) == [
        '001_create_notes.sql',
        '002_add_note_body.sql',
    ]

    write_migration(
        tmp_path,
        '003_add_second_note.sql',
        "INSERT INTO NOTES (note_id, body) VALUES (2, 'new');",
    )
    # Running 001 again would fail, because NOTES already exists.
    assert migrate.apply_pending(tmp_path) == ['003_add_second_note.sql']

    with db_cursor() as cursor:
        cursor.execute('SELECT note_id, body FROM NOTES ORDER BY note_id')
        assert cursor.fetchall() == [(1, 'a;b'), (2, 'new')]
    assert [version for version, _ in recorded_migrations()] == [1, 2, 3]


def test_failed_migration_is_not_recorded_and_stops_the_run(empty_database, tmp_path):
    write_migration(tmp_path, '001_create_notes.sql', 'CREATE TABLE NOTES (note_id INT);')
    write_migration(
        tmp_path,
        '002_broken.sql',
        'CREATE TABLE DRAFTS (draft_id INT);\nSELEC nonsense;',
    )
    write_migration(tmp_path, '003_create_tags.sql', 'CREATE TABLE TAGS (tag_id INT);')

    with pytest.raises(migrate.MigrationError, match='002_broken.sql failed'):
        migrate.apply_pending(tmp_path)

    assert recorded_migrations() == [(1, '001_create_notes.sql')]
    assert 'TAGS' not in table_names()


def test_fixed_migration_is_applied_on_the_next_run(empty_database, tmp_path):
    write_migration(tmp_path, '001_broken.sql', 'SELEC nonsense;')
    with pytest.raises(migrate.MigrationError):
        migrate.apply_pending(tmp_path)

    write_migration(tmp_path, '001_broken.sql', 'CREATE TABLE NOTES (note_id INT);')

    assert migrate.apply_pending(tmp_path) == ['001_broken.sql']
    assert 'NOTES' in table_names()


@pytest.mark.parametrize(
    'name', ['2_notes.sql', '002-notes.sql', '002_Notes.sql', 'notes.sql', '002_.sql']
)
def test_badly_named_file_is_rejected(tmp_path, name):
    write_migration(tmp_path, name, 'SELECT 1;')

    with pytest.raises(migrate.MigrationError, match='is not named like'):
        migrate.find_migrations(tmp_path)


def test_two_files_with_the_same_number_are_rejected(tmp_path):
    write_migration(tmp_path, '002_notes.sql', 'SELECT 1;')
    write_migration(tmp_path, '002_tags.sql', 'SELECT 1;')

    with pytest.raises(migrate.MigrationError, match='have the same number'):
        migrate.find_migrations(tmp_path)


def test_files_that_are_not_sql_are_ignored(tmp_path):
    write_migration(tmp_path, '001_notes.sql', 'SELECT 1;')
    write_migration(tmp_path, 'README.md', 'Notes about the migrations.')

    assert list(migrate.find_migrations(tmp_path)) == [1]
