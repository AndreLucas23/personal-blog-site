import pytest

from db import get_db_connection
from helpers import create_article
from repositories import user_repository

ARTICLE_PAYLOAD = {'new-title': 'Título', 'new-content': 'Conteúdo'}


def write_requests(article_id: int):
    """Every endpoint that changes articles, as (method, path, json)."""
    return [
        ('post', '/api/articles', ARTICLE_PAYLOAD),
        ('patch', f'/api/articles/{article_id}', {'title': 'Outro'}),
        ('delete', f'/api/articles/{article_id}', None),
    ]


@pytest.fixture
def article_id(admin_id):
    return create_article(admin_id)


def test_visitor_gets_401_with_the_login_url_on_write_endpoints(client, article_id):
    for method, path, payload in write_requests(article_id):
        response = getattr(client, method)(path, json=payload)

        assert response.status_code == 401, (method, path)
        assert response.get_json() == {
            'message': 'Authentication required',
            'login_url': '/auth/login',
        }


def test_visitor_gets_401_on_like_endpoints(client, article_id):
    assert client.post(f'/api/articles/{article_id}/likes').status_code == 401
    assert client.delete(f'/api/articles/{article_id}/likes').status_code == 401


def test_regular_user_gets_403_on_write_endpoints(reader_client, article_id):
    for method, path, payload in write_requests(article_id):
        response = getattr(reader_client, method)(path, json=payload)

        assert response.status_code == 403, (method, path)
        assert response.get_json() == {'message': 'Admin privileges required'}


def test_regular_user_cannot_change_articles(reader_client, article_id):
    for method, path, payload in write_requests(article_id):
        getattr(reader_client, method)(path, json=payload)

    articles = reader_client.get('/api/articles').get_json()
    assert [article['article_title'] for article in articles] == ['Título']


def test_admin_panel_redirects_visitors_to_login(client):
    response = client.get('/admin')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_admin_panel_is_forbidden_for_regular_users(reader_client):
    assert reader_client.get('/admin').status_code == 403


def test_admin_panel_opens_for_admins(admin_client):
    response = admin_client.get('/admin')

    assert response.status_code == 200
    assert 'Olá, Owner' in response.get_data(as_text=True)


def test_revoking_the_admin_flag_applies_to_an_open_session(admin_client, admin_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE USERS SET is_admin = 0 WHERE user_id = %s', (admin_id,))
    conn.commit()
    conn.close()

    assert user_repository.get_by_id(admin_id)['is_admin'] == 0
    assert admin_client.get('/admin').status_code == 403
    assert admin_client.post('/api/articles', json=ARTICLE_PAYLOAD).status_code == 403


def test_public_reads_stay_open(client, article_id):
    assert client.get('/api/articles').status_code == 200
    assert client.get(f'/api/articles/id/{article_id}').status_code == 200
    assert client.get('/api/articles/title/T').status_code == 200
    assert client.get(f'/open/{article_id}').status_code == 200
