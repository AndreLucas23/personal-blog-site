import auth
from db import db_cursor
from helpers import READER, login

WRONG_PASSWORD = 'wrong-password'
OTHER_ADDRESS = {'REMOTE_ADDR': '203.0.113.9'}


def fail_logins(client, email: str, times: int = auth.MAX_FAILED_LOGINS) -> None:
    for _ in range(times):
        assert login(client, email, WRONG_PASSWORD).status_code == 401


def age_failed_logins(minutes: int) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            'UPDATE FAILED_LOGINS SET attempted_at = NOW() - INTERVAL %s MINUTE',
            (minutes,),
        )


def count_failed_logins() -> int:
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM FAILED_LOGINS')
        return cursor.fetchone()[0]


def test_login_is_blocked_after_too_many_failures(client, reader_id):
    fail_logins(client, READER['email'])

    response = login(client, READER['email'], WRONG_PASSWORD)

    assert response.status_code == 429
    page = response.get_data(as_text=True)
    assert auth.TOO_MANY_LOGINS_MESSAGE in page
    assert f'value="{READER["email"]}"' in page


def test_blocked_login_refuses_the_right_password(client, reader_id):
    fail_logins(client, READER['email'])

    response = login(client, READER['email'], READER['password'])

    assert response.status_code == 429
    assert client.get('/auth/login').status_code == 200


def test_login_works_while_under_the_limit(client, reader_id):
    fail_logins(client, READER['email'], auth.MAX_FAILED_LOGINS - 1)

    assert login(client, READER['email'], READER['password']).status_code == 302


def test_successful_login_clears_the_failures(client, reader_id):
    fail_logins(client, READER['email'], auth.MAX_FAILED_LOGINS - 1)
    login(client, READER['email'], READER['password'])

    assert count_failed_logins() == 0


def test_block_ends_when_the_window_passes(client, reader_id):
    fail_logins(client, READER['email'])
    age_failed_logins(auth.FAILED_LOGIN_WINDOW_MINUTES + 1)

    assert login(client, READER['email'], READER['password']).status_code == 302


def test_old_failures_are_removed_on_the_next_failure(client, reader_id):
    fail_logins(client, 'someone@example.com', 3)
    age_failed_logins(auth.FAILED_LOGIN_WINDOW_MINUTES + 1)

    fail_logins(client, READER['email'], 1)

    assert count_failed_logins() == 1


def test_block_does_not_reach_other_accounts(client, reader_id, admin_id):
    fail_logins(client, READER['email'])

    assert login(client, 'owner@example.com', WRONG_PASSWORD).status_code == 401


def test_block_does_not_reach_other_addresses(app, client, reader_id):
    fail_logins(client, READER['email'])
    other_client = app.test_client()

    response = other_client.post(
        '/auth/login',
        data={'email': READER['email'], 'password': READER['password']},
        environ_base=OTHER_ADDRESS,
    )

    assert response.status_code == 302


def test_unknown_accounts_are_limited_too(client):
    fail_logins(client, 'nobody@example.com')

    assert login(client, 'nobody@example.com', WRONG_PASSWORD).status_code == 429


def test_email_longer_than_the_column_is_still_limited(client):
    long_email = 'a' * 300 + '@example.com'
    fail_logins(client, long_email)

    assert login(client, long_email, WRONG_PASSWORD).status_code == 429
