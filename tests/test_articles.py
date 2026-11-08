import pytest

from helpers import create_article
from repositories import article_repository

ARTICLE_FIELDS = {
    'article_id', 'article_title', 'article_content', 'publish_date',
    'author', 'likes', 'liked',
}


def test_listing_returns_every_article_with_its_details(client, admin_id):
    create_article(admin_id, title='Primeiro')
    create_article(admin_id, title='Segundo')

    articles = client.get('/api/articles').get_json()

    assert [article['article_title'] for article in articles] == ['Primeiro', 'Segundo']
    assert set(articles[0]) == ARTICLE_FIELDS
    assert articles[0]['author'] == 'Owner'
    assert articles[0]['likes'] == 0
    assert articles[0]['liked'] is False


def test_admin_creates_an_article_as_its_author(admin_client):
    response = admin_client.post(
        '/api/articles', json={'new-title': 'Olá', 'new-content': 'Primeiro post'}
    )

    assert response.status_code == 201
    articles = admin_client.get('/api/articles').get_json()
    assert len(articles) == 1
    assert articles[0]['article_content'] == 'Primeiro post'
    assert articles[0]['author'] == 'Owner'


@pytest.mark.parametrize(
    'payload',
    [
        {'new-title': '', 'new-content': 'Conteúdo'},
        {'new-title': 'x' * 31, 'new-content': 'Conteúdo'},
        {'new-title': 'Título'},
        {'new-title': 'Título', 'new-content': ''},
        {'new-title': '   ', 'new-content': 'Conteúdo'},
        {'new-title': 'Título', 'new-content': '   '},
        {'new-title': 123, 'new-content': 'Conteúdo'},
        {'new-title': 'Título', 'new-content': 123},
        {},
    ],
)
def test_creation_rejects_invalid_data(admin_client, payload):
    response = admin_client.post('/api/articles', json=payload)

    assert response.status_code == 400
    assert admin_client.get('/api/articles').get_json() == []


def test_admin_updates_title_and_content(admin_client, admin_id):
    article_id = create_article(admin_id)

    response = admin_client.patch(
        f'/api/articles/{article_id}', json={'title': 'Novo', 'content': 'Texto novo'}
    )

    assert response.status_code == 200
    article = article_repository.get_by_id(article_id)
    assert article['article_title'] == 'Novo'
    assert article['article_content'] == 'Texto novo'


def test_saving_an_unchanged_article_succeeds(admin_client, admin_id):
    """Regression for #24: MySQL reported 0 changed rows and the API answered 404."""
    article_id = create_article(admin_id, title='Mesmo', content='Igual')

    response = admin_client.patch(
        f'/api/articles/{article_id}', json={'title': 'Mesmo', 'content': 'Igual'}
    )

    assert response.status_code == 200


def test_update_of_a_missing_article_answers_404(admin_client, admin_id):
    response = admin_client.patch('/api/articles/999', json={'title': 'x'})

    assert response.status_code == 404


def test_update_without_fields_answers_400(admin_client, admin_id):
    article_id = create_article(admin_id)

    assert admin_client.patch(f'/api/articles/{article_id}', json={}).status_code == 400


def test_update_rejects_a_title_that_is_too_long(admin_client, admin_id):
    article_id = create_article(admin_id, title='Original')

    response = admin_client.patch(
        f'/api/articles/{article_id}', json={'title': 'x' * 31}
    )

    assert response.status_code == 400
    assert article_repository.get_by_id(article_id)['article_title'] == 'Original'


def test_update_rejects_an_empty_title(admin_client, admin_id):
    article_id = create_article(admin_id, title='Original')

    response = admin_client.patch(f'/api/articles/{article_id}', json={'title': ''})

    assert response.status_code == 400
    assert article_repository.get_by_id(article_id)['article_title'] == 'Original'


def test_update_rejects_empty_content(admin_client, admin_id):
    article_id = create_article(admin_id, content='Original')

    response = admin_client.patch(f'/api/articles/{article_id}', json={'content': ''})

    assert response.status_code == 400
    assert article_repository.get_by_id(article_id)['article_content'] == 'Original'


def test_update_rejects_a_title_that_is_not_text(admin_client, admin_id):
    article_id = create_article(admin_id)

    response = admin_client.patch(f'/api/articles/{article_id}', json={'title': 123})

    assert response.status_code == 400


def test_update_rejects_a_blank_title(admin_client, admin_id):
    article_id = create_article(admin_id, title='Original')

    response = admin_client.patch(f'/api/articles/{article_id}', json={'title': '   '})

    assert response.status_code == 400
    assert article_repository.get_by_id(article_id)['article_title'] == 'Original'


def test_update_rejects_content_that_is_not_text(admin_client, admin_id):
    article_id = create_article(admin_id, content='Original')

    response = admin_client.patch(
        f'/api/articles/{article_id}', json={'content': 123}
    )

    assert response.status_code == 400
    assert article_repository.get_by_id(article_id)['article_content'] == 'Original'


def test_write_endpoints_reject_a_body_that_is_not_an_object(admin_client, admin_id):
    article_id = create_article(admin_id)

    assert admin_client.post('/api/articles', json=['Título']).status_code == 400
    response = admin_client.patch(f'/api/articles/{article_id}', json=['x'])

    assert response.status_code == 400


def test_admin_removes_an_article(admin_client, admin_id):
    article_id = create_article(admin_id)

    response = admin_client.delete(f'/api/articles/{article_id}')

    assert response.status_code == 200
    assert article_repository.get_by_id(article_id) is None


def test_removing_a_missing_article_answers_404(admin_client, admin_id):
    assert admin_client.delete('/api/articles/999').status_code == 404


def test_search_by_title_matches_part_of_the_title(client, admin_id):
    create_article(admin_id, title='Notas de Flask')
    create_article(admin_id, title='Ideias soltas')

    results = client.get('/api/articles/title/Flask').get_json()

    assert [article['article_title'] for article in results] == ['Notas de Flask']


def test_search_by_id_returns_the_article_with_its_details(client, admin_id):
    article_id = create_article(admin_id, title='Alvo')

    results = client.get(f'/api/articles/id/{article_id}').get_json()

    assert results[0]['article_title'] == 'Alvo'
    assert set(results[0]) == ARTICLE_FIELDS


def test_search_without_matches_returns_an_empty_list(client):
    assert client.get('/api/articles/title/nada').get_json() == []
