import subprocess
import sys
from pathlib import Path

from werkzeug.security import check_password_hash

from helpers import create_user
from repositories import user_repository

SCRIPT = Path(__file__).resolve().parent.parent / 'src' / 'create_user.py'
PASSWORD = 'admin-password-1'


def run_command(*args: str, stdin: str = '') -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_creates_an_admin_with_a_hashed_password():
    result = run_command(
        '--name', 'Owner', '--username', 'owner', '--email', 'owner@example.com', '--admin',
        stdin=f'{PASSWORD}\n{PASSWORD}\n',
    )

    assert result.returncode == 0, result.stderr
    assert 'Created admin Owner (@owner)' in result.stdout
    user = user_repository.get_by_email('owner@example.com')
    assert user['is_admin'] == 1
    assert user['password_hash'] != PASSWORD
    assert check_password_hash(user['password_hash'], PASSWORD)


def test_creates_a_regular_user_without_the_admin_option():
    result = run_command(
        '--name', 'Reader', '--username', 'reader', '--email', 'reader@example.com',
        stdin=f'{PASSWORD}\n{PASSWORD}\n',
    )

    assert result.returncode == 0, result.stderr
    assert user_repository.get_by_email('reader@example.com')['is_admin'] == 0


def test_rejects_an_invalid_email_before_asking_for_the_password():
    result = run_command('--name', 'Owner', '--username', 'owner', '--email', 'not-an-email')

    assert result.returncode != 0
    assert 'A valid email is required.' in result.stderr
    assert 'Password' not in result.stderr
    assert user_repository.get_by_email('not-an-email') is None


def test_rejects_a_short_password():
    result = run_command(
        '--name', 'Owner', '--username', 'owner', '--email', 'owner@example.com',
        stdin='short\nshort\n',
    )

    assert result.returncode != 0
    assert 'at least 8 characters' in result.stderr
    assert user_repository.get_by_email('owner@example.com') is None


def test_rejects_passwords_that_do_not_match():
    result = run_command(
        '--name', 'Owner', '--username', 'owner', '--email', 'owner@example.com',
        stdin=f'{PASSWORD}\nanother-password\n',
    )

    assert result.returncode != 0
    assert 'do not match' in result.stderr
    assert user_repository.get_by_email('owner@example.com') is None


def test_reports_a_duplicated_email_without_a_traceback():
    create_user('Owner', 'owner', 'owner@example.com', PASSWORD)

    result = run_command(
        '--name', 'Other', '--username', 'other', '--email', 'owner@example.com',
        stdin=f'{PASSWORD}\n{PASSWORD}\n',
    )

    assert result.returncode != 0
    assert 'already exists' in result.stderr
    assert 'Traceback' not in result.stderr


def test_normalizes_and_checks_the_username():
    result = run_command(
        '--name', 'Ana', '--username', ' @Ana_Souza ', '--email', 'ana@example.com',
        stdin=f'{PASSWORD}\n{PASSWORD}\n',
    )

    assert result.returncode == 0, result.stderr
    assert user_repository.get_by_email('ana@example.com')['username'] == 'ana_souza'


def test_rejects_an_invalid_username_before_asking_for_the_password():
    result = run_command(
        '--name', 'Ana', '--username', 'ana souza', '--email', 'ana@example.com'
    )

    assert result.returncode != 0
    assert 'lowercase letters, digits and underscores' in result.stderr
    assert user_repository.get_by_email('ana@example.com') is None


def test_reports_a_taken_username_without_a_traceback():
    create_user('Owner', 'owner', 'owner@example.com', PASSWORD)

    result = run_command(
        '--name', 'Other', '--username', 'owner', '--email', 'other@example.com',
        stdin=f'{PASSWORD}\n{PASSWORD}\n',
    )

    assert result.returncode != 0
    assert 'already taken' in result.stderr
    assert 'Traceback' not in result.stderr
