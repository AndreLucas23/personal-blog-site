from db import get_db_connection
from helpers import create_article
from repositories import user_repository

ARTICLE_PAYLOAD = {'title': 'Título', 'content': 'Conteúdo'}


def write_requests(article_id: int):
    """Every endpoint that changes articles, as (method, path, json)."""
    return [
        ('post', '/api/articles', ARTICLE_PAYLOAD),
        ('patch', f'/api/articles/{article_id}', {'title': 'Outro'}),
        ('delete', f'/api/articles/{article_id}', None),
    ]


def test_visitor_gets_401_with_the_login_url_on_write_endpoints(client, admin_id):
    article_id = create_article(admin_id)

    for method, path, payload in write_requests(article_id):
        response = getattr(client, method)(path, json=payload)

        assert response.status_code == 401, (method, path)
        assert response.get_json() == {
            'message': 'Authentication required',
            'login_url': '/auth/login',
        }


def test_visitor_gets_401_on_like_endpoints(client, admin_id):
    article_id = create_article(admin_id)

    assert client.post(f'/api/articles/{article_id}/likes').status_code == 401
    assert client.delete(f'/api/articles/{article_id}/likes').status_code == 401


def test_members_cannot_change_other_members_articles(reader_client, admin_id):
    article_id = create_article(admin_id)

    for method, path, payload in write_requests(article_id)[1:]:
        assert getattr(reader_client, method)(path, json=payload).status_code == 403, method

    article = reader_client.get(f'/api/articles/{article_id}').get_json()
    assert article['article_title'] == 'Título'


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


def test_revoking_the_admin_flag_applies_to_an_open_session(admin_client, admin_id, reader_id):
    article_id = create_article(reader_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE USERS SET is_admin = 0 WHERE user_id = %s', (admin_id,))
    conn.commit()
    conn.close()

    assert user_repository.get_by_id(admin_id)['is_admin'] == 0
    assert admin_client.get('/admin').status_code == 403
    assert admin_client.delete(f'/api/articles/{article_id}').status_code == 403


def test_public_reads_stay_open(client, admin_id):
    article_id = create_article(admin_id)

    assert client.get('/api/articles').status_code == 200
    assert client.get(f'/api/articles/{article_id}').status_code == 200
    assert client.get(f'/api/articles/id/{article_id}').status_code == 200
    assert client.get('/api/articles/title/T').status_code == 200
    assert client.get(f'/articles/{article_id}/titulo').status_code == 200
