import logging

import mysql.connector
import pytest
from werkzeug.exceptions import BadRequest, BadRequestKeyError, UnsupportedMediaType

import db

DATABASE_HOST_ERROR = "Unknown MySQL server host 'db'"


def fail_to_connect():
    raise mysql.connector.errors.InterfaceError(msg=DATABASE_HOST_ERROR, errno=2005)


def test_database_errors_hide_internal_details(client, monkeypatch):
    """Regression for #11: the response exposed the MySQL error and the host."""
    monkeypatch.setattr(db, 'get_db_connection', fail_to_connect)

    response = client.get('/api/articles')

    assert response.status_code == 500
    assert response.get_json() == {
        'status': 'error',
        'message': 'An internal error occurred while accessing the database',
    }
    assert DATABASE_HOST_ERROR not in response.get_data(as_text=True)


def test_database_errors_are_logged_with_the_request(client, monkeypatch, caplog):
    monkeypatch.setattr(db, 'get_db_connection', fail_to_connect)

    with caplog.at_level(logging.ERROR):
        client.get('/api/articles')

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        'GET /api/articles' in message and '2005' in message
        and DATABASE_HOST_ERROR in message
        for message in messages
    ), messages


SECRET_DETAIL = 'secret detail from the stack'


def explode(*args, **kwargs):
    raise RuntimeError(SECRET_DETAIL)


@pytest.fixture
def unhandled_errors_answer_500(app, monkeypatch):
    # Under TESTING Flask re-raises exceptions; production answers with the 500 handler.
    monkeypatch.setitem(app.config, 'PROPAGATE_EXCEPTIONS', False)


def test_missing_page_shows_the_not_found_page(client):
    response = client.get('/nao-existe')

    assert response.status_code == 404
    assert response.mimetype == 'text/html'
    page = response.get_data(as_text=True)
    assert 'Página não encontrada' in page
    assert 'Voltar para o início' in page
    assert 'Social Blog' in page


def test_missing_api_route_answers_json(client):
    response = client.get('/api/nao-existe')

    assert response.status_code == 404
    assert response.get_json() == {'message': 'Not found'}


def test_wrong_method_answers_405_on_pages_and_api(client):
    page = client.put('/auth/login')
    api = client.put('/api/articles')

    assert page.status_code == 405
    assert 'Ação não permitida' in page.get_data(as_text=True)
    assert api.status_code == 405
    assert api.get_json() == {'message': 'Method not allowed'}


def test_405_lists_the_allowed_methods(client):
    page = client.put('/auth/login')
    api = client.put('/api/articles')

    assert {'GET', 'POST'} <= set(page.headers['Allow'].split(', '))
    assert {'GET', 'POST'} <= set(api.headers['Allow'].split(', '))
    assert page.mimetype == 'text/html'
    assert api.mimetype == 'application/json'


def test_forbidden_page_is_in_portuguese(reader_client):
    response = reader_client.get('/admin')

    assert response.status_code == 403
    page = response.get_data(as_text=True)
    assert 'Acesso negado' in page
    assert 'Admin privileges required' not in page


def test_unexpected_page_error_hides_the_details(
    client, admin_id, monkeypatch, unhandled_errors_answer_500, caplog
):
    from repositories import article_repository
    monkeypatch.setattr(article_repository, 'get_by_id', explode)

    with caplog.at_level(logging.ERROR):
        response = client.get('/open/1')

    assert response.status_code == 500
    page = response.get_data(as_text=True)
    assert 'Algo deu errado' in page
    assert SECRET_DETAIL not in page
    assert any(SECRET_DETAIL in (record.exc_text or '') or SECRET_DETAIL in str(record.exc_info)
               for record in caplog.records)


def test_unexpected_api_error_answers_json(client, monkeypatch, unhandled_errors_answer_500):
    from repositories import article_repository
    monkeypatch.setattr(article_repository, 'get_page', explode)

    response = client.get('/api/articles')

    assert response.status_code == 500
    assert response.get_json() == {'message': 'Internal server error'}


def test_database_error_on_a_page_shows_the_error_page(client, monkeypatch):
    monkeypatch.setattr(db, 'get_db_connection', fail_to_connect)

    response = client.get('/open/1')

    assert response.status_code == 500
    assert response.mimetype == 'text/html'
    page = response.get_data(as_text=True)
    assert 'Algo deu errado' in page
    assert DATABASE_HOST_ERROR not in page


def test_database_error_page_skips_the_account_of_a_signed_in_member(reader_client, monkeypatch):
    monkeypatch.setattr(db, 'get_db_connection', fail_to_connect)

    response = reader_client.get('/open/1')

    assert response.status_code == 500
    assert response.mimetype == 'text/html'
    page = response.get_data(as_text=True)
    assert 'class="topbar"' in page
    assert 'Algo deu errado' in page
    assert 'id="account-menu"' not in page
    assert 'topnav__guest' not in page


def test_library_error_details_never_reach_the_api(client, monkeypatch):
    from repositories import article_repository

    def missing_field(*args, **kwargs):
        raise BadRequestKeyError('secret_field')

    monkeypatch.setattr(article_repository, 'get_page', missing_field)

    response = client.get('/api/articles')

    assert response.status_code == 400
    assert response.get_json() == {'message': 'Bad request'}
    assert 'secret_field' not in response.get_data(as_text=True)


def test_library_error_details_never_reach_the_pages(client, monkeypatch):
    from repositories import article_repository

    def bad_body(*args, **kwargs):
        raise BadRequest('Failed to decode JSON object: internal detail')

    monkeypatch.setattr(article_repository, 'get_by_id', bad_body)

    response = client.get('/open/1')

    assert response.status_code == 400
    page = response.get_data(as_text=True)
    assert 'Requisição inválida' in page
    assert 'internal detail' not in page


def test_error_page_drops_the_account_menu_when_the_database_fails(reader_client, monkeypatch):
    monkeypatch.setattr(db, 'get_db_connection', fail_to_connect)

    response = reader_client.get('/nao-existe')

    assert response.status_code == 404
    assert response.mimetype == 'text/html'
    page = response.get_data(as_text=True)
    assert 'class="topbar"' in page
    assert 'Página não encontrada' in page
    assert 'id="account-menu"' not in page


def test_unexpected_error_keeps_the_account_menu_when_the_database_works(
    reader_client, monkeypatch, unhandled_errors_answer_500
):
    from repositories import article_repository
    monkeypatch.setattr(article_repository, 'get_by_id', explode)

    response = reader_client.get('/open/1')

    assert response.status_code == 500
    assert 'id="account-menu"' in response.get_data(as_text=True)


def test_other_client_errors_read_as_an_invalid_request(client, monkeypatch):
    from repositories import article_repository

    def unsupported(*args, **kwargs):
        raise UnsupportedMediaType()

    monkeypatch.setattr(article_repository, 'get_by_id', unsupported)
    monkeypatch.setattr(article_repository, 'get_page', unsupported)

    page = client.get('/open/1')
    api = client.get('/api/articles')

    assert page.status_code == 415
    assert 'Requisição inválida' in page.get_data(as_text=True)
    assert api.status_code == 415
    assert api.get_json() == {'message': 'Unsupported Media Type'}
