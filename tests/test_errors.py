import logging

import mysql.connector

from repositories import article_repository

DATABASE_HOST_ERROR = "Unknown MySQL server host 'db'"


def fail_to_connect():
    raise mysql.connector.errors.InterfaceError(msg=DATABASE_HOST_ERROR, errno=2005)


def test_database_errors_hide_internal_details(client, monkeypatch):
    """Regression for #11: the response exposed the MySQL error and the host."""
    monkeypatch.setattr(article_repository, 'get_db_connection', fail_to_connect)

    response = client.get('/api/articles')

    assert response.status_code == 500
    assert response.get_json() == {
        'status': 'error',
        'message': 'An internal error occurred while accessing the database',
    }
    assert DATABASE_HOST_ERROR not in response.get_data(as_text=True)


def test_database_errors_are_logged_with_the_request(client, monkeypatch, caplog):
    monkeypatch.setattr(article_repository, 'get_db_connection', fail_to_connect)

    with caplog.at_level(logging.ERROR):
        client.get('/api/articles')

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        'GET /api/articles' in message and '2005' in message
        and DATABASE_HOST_ERROR in message
        for message in messages
    ), messages
