from werkzeug.security import check_password_hash

from helpers import ADMIN, READER, login
from repositories import user_repository

NEW_USER = {
    'display_name': 'Leitora',
    'username': 'leitora',
    'email': 'leitora@example.com',
    'password': 'senha-segura-1',
}


def register(client, **overrides):
    return client.post('/auth/register', data={**NEW_USER, **overrides})


def test_login_with_valid_credentials_starts_a_session(client, reader_id):
    response = login(client, READER['email'], READER['password'])

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')
    assert client.get('/auth/login').status_code == 302


def test_session_cookie_is_http_only_and_same_site_lax(client, reader_id):
    response = login(client, READER['email'], READER['password'])

    cookie = response.headers['Set-Cookie']
    assert 'HttpOnly' in cookie
    assert 'SameSite=Lax' in cookie


def test_session_cookie_is_not_secure_by_default(client, reader_id):
    response = login(client, READER['email'], READER['password'])

    assert 'Secure' not in response.headers['Set-Cookie']


def test_session_cookie_is_secure_when_configured(app, client, reader_id, monkeypatch):
    monkeypatch.setitem(app.config, 'SESSION_COOKIE_SECURE', True)

    response = login(client, READER['email'], READER['password'])

    assert 'Secure' in response.headers['Set-Cookie']


def test_login_with_wrong_password_keeps_the_email(client, reader_id):
    response = login(client, READER['email'], 'wrong-password')

    assert response.status_code == 401
    page = response.get_data(as_text=True)
    assert 'E-mail ou senha inválidos.' in page
    assert f'value="{READER["email"]}"' in page


def test_login_with_unknown_email_fails(client):
    assert login(client, 'ghost@example.com', ADMIN['password']).status_code == 401


def test_logout_ends_the_session(reader_client):
    response = reader_client.post('/auth/logout')

    assert response.status_code == 302
    assert reader_client.get('/auth/login').status_code == 200


def test_logout_without_a_session_redirects_to_login(client):
    response = client.post('/auth/logout')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_registration_creates_a_regular_user_and_signs_in(client):
    response = register(client, display_name='  Leitora  ', username=' @Leitora ')

    assert response.status_code == 302
    user = user_repository.get_by_email(NEW_USER['email'])
    assert user['display_name'] == 'Leitora'
    assert user['username'] == 'leitora'
    assert user['is_admin'] == 0
    assert check_password_hash(user['password_hash'], NEW_USER['password'])
    assert client.get('/auth/register').status_code == 302


def test_registration_ignores_an_admin_flag_in_the_form(client):
    register(client, is_admin='1', role='admin')

    assert user_repository.get_by_email(NEW_USER['email'])['is_admin'] == 0


def test_registration_rejects_a_duplicated_email_in_any_letter_case(app, client):
    register(client)
    another_visitor = app.test_client()

    response = register(
        another_visitor, display_name='Outra', username='outra',
        email=NEW_USER['email'].upper(),
    )

    assert response.status_code == 409
    page = response.get_data(as_text=True)
    assert 'Este e-mail já está cadastrado.' in page
    assert 'value="Outra"' in page
    assert 'value="outra"' in page


def test_registration_rejects_a_taken_username(app, client):
    register(client)
    another_visitor = app.test_client()

    response = register(another_visitor, username='Leitora', email='outra@example.com')

    assert response.status_code == 409
    assert 'Este nome de usuário já está em uso.' in response.get_data(as_text=True)
    assert user_repository.get_by_email('outra@example.com') is None


def test_registration_rejects_invalid_data_and_stores_nothing(client):
    invalid_forms = [
        {'display_name': ''},
        {'display_name': 'x' * 51},
        {'username': ''},
        {'username': 'ab'},
        {'username': 'x' * 31},
        {'username': 'leitora souza'},
        {'username': 'admin'},
        {'email': 'not-an-email'},
        {'password': '1234567'},
        {'password': 'x' * 129},
    ]

    for overrides in invalid_forms:
        assert register(client, **overrides).status_code == 400, overrides

    assert user_repository.get_by_email(NEW_USER['email']) is None


def test_registration_error_message_is_in_portuguese(client):
    response = register(client, password='1234567')

    page = response.get_data(as_text=True)
    assert 'A senha deve ter pelo menos 8 caracteres.' in page


def test_registration_explains_the_username_rules_in_portuguese(client):
    response = register(client, username='leitora souza')

    page = response.get_data(as_text=True)
    assert 'Use só letras minúsculas sem acento, números e _ no nome de usuário.' in page
