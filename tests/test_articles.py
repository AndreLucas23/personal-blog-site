import pytest

import article_validation
from helpers import create_article
from repositories import article_repository

ARTICLE_FIELDS = {
    'article_id', 'url', 'article_title', 'summary', 'excerpt', 'reading_time', 'status',
    'publish_date', 'created_at', 'updated_at', 'author', 'author_username', 'author_avatar_url',
    'likes', 'liked',
}
NEW_ARTICLE = {'title': 'Olá', 'summary': 'Um resumo', 'content': '# Oi\n\nPrimeiro post'}


def test_listing_returns_every_article_with_its_details(client, admin_id):
    create_article(admin_id, title='Primeiro')
    create_article(admin_id, title='Segundo')

    articles = client.get('/api/articles').get_json()

    assert [article['article_title'] for article in articles] == ['Primeiro', 'Segundo']
    assert set(articles[0]) == ARTICLE_FIELDS
    assert articles[0]['author'] == 'Owner'
    assert articles[0]['author_username'] == 'owner'
    assert articles[0]['author_avatar_url'] is None
    assert articles[0]['likes'] == 0
    assert articles[0]['liked'] is False


def test_listing_shows_the_summary_or_an_excerpt(client, admin_id):
    create_article(admin_id, title='Com resumo', summary='Resumo escrito')
    create_article(admin_id, title='Sem resumo', content='**Texto** com _formato_.')

    articles = {a['article_title']: a for a in client.get('/api/articles').get_json()}

    assert articles['Com resumo']['excerpt'] == 'Resumo escrito'
    assert articles['Sem resumo']['excerpt'] == 'Texto com formato.'
    assert articles['Sem resumo']['reading_time'] == 1


def test_any_member_creates_an_article_as_its_author(reader_client):
    response = reader_client.post('/api/articles', json=NEW_ARTICLE)

    assert response.status_code == 201
    article = response.get_json()
    assert article['article_title'] == 'Olá'
    assert article['summary'] == 'Um resumo'
    assert article['article_content'] == '# Oi\n\nPrimeiro post'
    assert article['author_username'] == 'reader'


def test_creation_normalizes_the_fields(reader_client):
    article = reader_client.post('/api/articles', json={
        'title': '  Um   título\n',
        'summary': '',
        'content': '\r\n    código\r\nfim  \r\n\r\n',
    }).get_json()

    assert article['article_title'] == 'Um título'
    assert article['summary'] is None
    assert article['article_content'] == '    código\nfim'


def test_visitors_cannot_create_articles(client):
    assert client.post('/api/articles', json=NEW_ARTICLE).status_code == 401


@pytest.mark.parametrize(('payload', 'errors'), [
    ({'title': '', 'content': 'x'}, {'title': 'title_required'}),
    ({'title': '   ', 'content': 'x'}, {'title': 'title_required'}),
    ({'title': 'x' * 151, 'content': 'x'}, {'title': 'title_too_long'}),
    ({'title': 'Título'}, {'content': 'content_required'}),
    ({'title': 'Título', 'content': '  \n '}, {'content': 'content_required'}),
    ({'title': 'Título', 'content': 'x' * 50_001}, {'content': 'content_too_long'}),
    ({'title': 'Título', 'content': 'x', 'summary': 'x' * 301}, {'summary': 'summary_too_long'}),
    ({'title': 123, 'content': 'x'}, {'title': 'invalid'}),
    ({'title': 'Título', 'content': ['x']}, {'content': 'invalid'}),
    ({}, {'title': 'title_required', 'content': 'content_required'}),
])
def test_creation_rejects_invalid_data(reader_client, payload, errors):
    response = reader_client.post('/api/articles', json=payload)

    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid article', 'errors': errors}
    assert reader_client.get('/api/articles').get_json() == []


def test_limits_match_the_rules():
    assert article_validation.MAX_TITLE_LENGTH == 150
    assert article_validation.MAX_CONTENT_LENGTH == 50_000


def test_reading_one_article_includes_its_content(client, admin_id):
    article_id = create_article(admin_id, content='Texto inteiro')

    article = client.get(f'/api/articles/{article_id}').get_json()

    assert article['article_content'] == 'Texto inteiro'


def test_reading_a_missing_article_answers_404(client):
    assert client.get('/api/articles/999').status_code == 404


def test_author_updates_the_fields(reader_client, reader_id):
    article_id = create_article(reader_id)

    response = reader_client.patch(f'/api/articles/{article_id}', json={
        'title': 'Novo', 'summary': 'Novo resumo', 'content': 'Texto novo',
    })

    assert response.status_code == 200
    article = article_repository.get_by_id(article_id)
    assert article['article_title'] == 'Novo'
    assert article['summary'] == 'Novo resumo'
    assert article['article_content'] == 'Texto novo'


def test_author_clears_the_summary(reader_client, reader_id):
    article_id = create_article(reader_id, summary='Antigo')

    reader_client.patch(f'/api/articles/{article_id}', json={'summary': None})

    assert article_repository.get_by_id(article_id)['summary'] is None


def test_saving_an_unchanged_article_succeeds(reader_client, reader_id):
    """Regression for #24: MySQL reported 0 changed rows and the API answered 404."""
    article_id = create_article(reader_id, title='Mesmo', content='Igual')

    response = reader_client.patch(
        f'/api/articles/{article_id}', json={'title': 'Mesmo', 'content': 'Igual'}
    )

    assert response.status_code == 200


def test_only_the_author_edits_an_article(admin_client, reader_client, admin_id):
    article_id = create_article(admin_id, title='Original')

    reader = reader_client.patch(f'/api/articles/{article_id}', json={'title': 'Outro'})
    admin_of_another = create_article(admin_id)

    assert reader.status_code == 403
    assert reader.get_json() == {'message': 'Only the author can edit this article'}
    assert article_repository.get_by_id(article_id)['article_title'] == 'Original'
    assert admin_client.patch(f'/api/articles/{admin_of_another}', json={'title': 'x'}).status_code == 200


def test_admins_do_not_edit_other_members_articles(admin_client, reader_id):
    article_id = create_article(reader_id, title='Da leitora')

    response = admin_client.patch(f'/api/articles/{article_id}', json={'title': 'Do admin'})

    assert response.status_code == 403
    assert article_repository.get_by_id(article_id)['article_title'] == 'Da leitora'


def test_update_of_a_missing_article_answers_404(reader_client):
    assert reader_client.patch('/api/articles/999', json={'title': 'x'}).status_code == 404


def test_update_without_fields_answers_400(reader_client, reader_id):
    article_id = create_article(reader_id)

    response = reader_client.patch(f'/api/articles/{article_id}', json={'author_id': 1})

    assert response.status_code == 400
    assert response.get_json() == {'message': 'No fields to update'}


@pytest.mark.parametrize(('payload', 'errors'), [
    ({'title': ''}, {'title': 'title_required'}),
    ({'title': '   '}, {'title': 'title_required'}),
    ({'title': 'x' * 151}, {'title': 'title_too_long'}),
    ({'content': ''}, {'content': 'content_required'}),
    ({'title': 123}, {'title': 'invalid'}),
    ({'content': 123}, {'content': 'invalid'}),
])
def test_update_rejects_invalid_fields_and_changes_nothing(reader_client, reader_id, payload, errors):
    article_id = create_article(reader_id, title='Original', content='Original')

    response = reader_client.patch(f'/api/articles/{article_id}', json=payload)

    assert response.status_code == 400
    assert response.get_json()['errors'] == errors
    article = article_repository.get_by_id(article_id)
    assert article['article_title'] == 'Original'
    assert article['article_content'] == 'Original'


def test_write_endpoints_reject_a_body_that_is_not_an_object(reader_client, reader_id):
    article_id = create_article(reader_id)

    assert reader_client.post('/api/articles', json=['Título']).status_code == 400
    assert reader_client.patch(f'/api/articles/{article_id}', json=['x']).status_code == 400


def test_author_removes_their_article(reader_client, reader_id):
    article_id = create_article(reader_id)

    response = reader_client.delete(f'/api/articles/{article_id}')

    assert response.status_code == 200
    assert article_repository.get_by_id(article_id) is None


def test_admin_removes_any_article(admin_client, reader_id):
    article_id = create_article(reader_id)

    assert admin_client.delete(f'/api/articles/{article_id}').status_code == 200
    assert article_repository.get_by_id(article_id) is None


def test_members_cannot_remove_other_members_articles(reader_client, admin_id):
    article_id = create_article(admin_id)

    response = reader_client.delete(f'/api/articles/{article_id}')

    assert response.status_code == 403
    assert response.get_json() == {'message': 'Only the author or an admin can remove this article'}
    assert article_repository.get_by_id(article_id) is not None


def test_removing_a_missing_article_answers_404(admin_client):
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


def test_listing_filters_by_author(client, admin_id, reader_id):
    create_article(admin_id, title='Do admin')
    create_article(reader_id, title='Da leitora')

    response = client.get('/api/articles?author=@Reader')

    assert response.status_code == 200
    assert [article['article_title'] for article in response.get_json()] == ['Da leitora']
    assert client.get('/api/articles?author=owner').get_json()[0]['article_title'] == 'Do admin'


def test_listing_by_an_unknown_author_answers_404(client):
    response = client.get('/api/articles?author=ghost')

    assert response.status_code == 404
    assert response.get_json() == {'message': 'User not found'}


def test_member_without_articles_gets_an_empty_list(client, reader_id):
    assert client.get('/api/articles?author=reader').get_json() == []


def test_search_results_carry_the_author_fields(client, admin_id):
    create_article(admin_id, title='Busca')

    result = client.get('/api/articles/title/Bus').get_json()[0]

    assert result['author_username'] == 'owner'
    assert 'author_avatar_path' not in result


def test_articles_carry_their_readable_address(client, admin_id):
    article_id = create_article(admin_id, title='Olá, mundo!')

    article = client.get(f'/api/articles/{article_id}').get_json()

    assert article['url'] == f'/articles/{article_id}/ola-mundo'


def test_saving_an_article_removed_meanwhile_answers_404(reader_client, reader_id, monkeypatch):
    article_id = create_article(reader_id)
    remove_before_saving = article_repository.update

    def removed_by_a_moderator(*args, **kwargs):
        article_repository.delete(article_id)
        return remove_before_saving(*args, **kwargs)

    monkeypatch.setattr(article_repository, 'update', removed_by_a_moderator)

    response = reader_client.patch(f'/api/articles/{article_id}', json={'title': 'Novo'})

    assert response.status_code == 404
    assert response.get_json() == {'message': 'Article not found'}
