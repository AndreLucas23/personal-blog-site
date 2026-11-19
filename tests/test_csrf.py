import re

import pytest

import csrf
from helpers import READER, create_article

TOKEN_META = re.compile(r'<meta name="csrf-token" content="([^"]+)">')
LOGIN_FORM = {'login': READER['email'], 'password': READER['password']}


@pytest.fixture(autouse=True)
def csrf_enabled(app, monkeypatch):
    monkeypatch.setitem(app.config, 'CSRF_ENABLED', True)


def page_token(client, path: str = '/auth/login') -> str:
    page = client.get(path).get_data(as_text=True)
    return TOKEN_META.search(page).group(1)


def sign_in(client) -> str:
    token = page_token(client)
    response = client.post('/auth/login', data={**LOGIN_FORM, 'csrf_token': token})
    assert response.status_code == 302
    return token


def is_signed_in(client) -> bool:
    return client.get('/auth/login').status_code == 302


def test_form_without_a_token_is_rejected(client, reader_id):
    page_token(client)

    response = client.post('/auth/login', data=LOGIN_FORM)

    assert response.status_code == 400
    assert csrf.PAGE_MESSAGE in response.get_data(as_text=True)
    assert not is_signed_in(client)


def test_form_with_the_token_of_its_page_is_accepted(client, reader_id):
    sign_in(client)

    assert is_signed_in(client)


def test_request_without_a_session_is_rejected(client, reader_id):
    response = client.post('/auth/login', data={**LOGIN_FORM, 'csrf_token': 'made-up'})

    assert response.status_code == 400


def test_token_of_another_session_is_rejected(app, client, reader_id):
    other_token = page_token(app.test_client())
    page_token(client)

    response = client.post(
        '/auth/login', data={**LOGIN_FORM, 'csrf_token': other_token}
    )

    assert response.status_code == 400
    assert not is_signed_in(client)


def test_token_stays_the_same_within_a_session(client):
    assert page_token(client) == page_token(client, '/')


def test_registration_requires_the_token(client):
    form = {
        'display_name': 'Leitora',
        'username': 'leitora',
        'email': 'leitora@example.com',
        'password': 'senha-1234',
    }
    token = page_token(client, '/auth/register')

    assert client.post('/auth/register', data=form).status_code == 400
    response = client.post('/auth/register', data={**form, 'csrf_token': token})
    assert response.status_code == 302


def test_api_without_a_token_answers_400_as_json(client, reader_id, admin_id):
    article_id = create_article(admin_id)
    sign_in(client)

    response = client.post(f'/api/articles/{article_id}/likes')

    assert response.status_code == 400
    assert response.get_json() == {'message': csrf.API_MESSAGE}


def test_api_accepts_the_token_in_a_header(client, reader_id, admin_id):
    article_id = create_article(admin_id)
    token = sign_in(client)

    response = client.post(
        f'/api/articles/{article_id}/likes', headers={csrf.HEADER: token}
    )

    assert response.status_code == 200
    assert response.get_json() == {'liked': True, 'likes': 1}


@pytest.mark.parametrize('method, path', [
    ('post', '/api/articles'),
    ('patch', '/api/articles/1'),
    ('delete', '/api/articles/1'),
])
def test_every_state_changing_method_requires_the_token(client, method, path):
    response = getattr(client, method)(path)

    assert response.status_code == 400


def test_reading_needs_no_token(client):
    assert client.get('/api/articles').status_code == 200
    assert client.get('/').status_code == 200


def test_visitor_with_a_token_is_still_asked_to_sign_in(client, admin_id):
    article_id = create_article(admin_id)
    token = page_token(client, '/')

    response = client.post(
        f'/api/articles/{article_id}/likes', headers={csrf.HEADER: token}
    )

    assert response.status_code == 401


def test_logout_without_a_token_keeps_the_session(client, reader_id):
    sign_in(client)

    assert client.post('/auth/logout').status_code == 400
    assert is_signed_in(client)


def test_logout_with_the_token_ends_the_session(client, reader_id):
    token = sign_in(client)

    response = client.post('/auth/logout', data={'csrf_token': token})

    assert response.status_code == 302
    assert not is_signed_in(client)


def test_logout_does_not_answer_get(client, reader_id):
    sign_in(client)

    assert client.get('/auth/logout').status_code == 405
    assert is_signed_in(client)


def test_forms_carry_the_token(client, reader_id, admin_id):
    article_id = create_article(admin_id)
    token = sign_in(client)
    field = f'<input type="hidden" name="csrf_token" value="{token}">'

    home = client.get('/').get_data(as_text=True)
    assert field in home
    assert 'action="/auth/logout"' in home
    assert page_token(client, f'/articles/{article_id}/titulo') == token

    client.post('/auth/logout', data={'csrf_token': token})
    assert field in client.get('/auth/login').get_data(as_text=True)
    assert field in client.get('/auth/register').get_data(as_text=True)


def test_requests_that_match_no_route_get_the_routing_error(client):
    wrong_method = client.put('/api/articles')
    missing_api = client.post('/api/nao-existe')
    missing_page = client.post('/nao-existe')

    assert wrong_method.status_code == 405
    assert wrong_method.get_json() == {'message': 'Method not allowed'}
    assert missing_api.status_code == 404
    assert missing_api.get_json() == {'message': 'Not found'}
    assert missing_page.status_code == 404
    assert 'Página não encontrada' in missing_page.get_data(as_text=True)


def test_api_requests_without_a_token_get_json_in_english(client, reader_id):
    response = client.post('/api/articles/1/likes')

    assert response.status_code == 400
    assert response.get_json() == {'message': csrf.API_MESSAGE}
