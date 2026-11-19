import pytest

from db import db_cursor
from helpers import create_article
from repositories import article_repository


def draft_of(author_id: int, **fields) -> int:
    return create_article(author_id, status='draft', **fields)


def test_a_draft_needs_only_a_title(reader_client):
    response = reader_client.post('/api/articles', json={'title': 'Ideia', 'status': 'draft'})

    assert response.status_code == 201
    article = response.get_json()
    assert article['status'] == 'draft'
    assert article['publish_date'] is None
    assert article['article_content'] == ''


def test_articles_are_published_by_default(reader_client):
    article = reader_client.post('/api/articles', json={'title': 'T', 'content': 'C'}).get_json()

    assert article['status'] == 'published'
    assert article['publish_date'] is not None


def test_an_unknown_status_is_refused(reader_client, reader_id):
    article_id = draft_of(reader_id)

    created = reader_client.post('/api/articles', json={'title': 'T', 'content': 'C', 'status': 'live'})
    updated = reader_client.patch(f'/api/articles/{article_id}', json={'status': 3})

    assert created.status_code == 400
    assert created.get_json()['errors'] == {'status': 'invalid'}
    assert updated.status_code == 400
    assert updated.get_json()['errors'] == {'status': 'invalid'}


def test_drafts_stay_out_of_every_list(client, reader_client, reader_id):
    draft_of(reader_id, title='Rascunho secreto')
    create_article(reader_id, title='Publicado')

    for viewer in (client, reader_client):
        titles = [a['article_title'] for a in viewer.get('/api/articles').get_json()]
        assert titles == ['Publicado']
        by_author = viewer.get('/api/articles?author=reader').get_json()
        assert [a['article_title'] for a in by_author] == ['Publicado']
        assert viewer.get('/api/articles/title/secreto').get_json() == []


def test_drafts_are_found_by_id_only_by_their_author(client, admin_client, reader_client, reader_id):
    article_id = draft_of(reader_id)

    assert reader_client.get(f'/api/articles/{article_id}').status_code == 200
    assert client.get(f'/api/articles/{article_id}').status_code == 404
    assert admin_client.get(f'/api/articles/{article_id}').status_code == 404
    assert admin_client.get(f'/api/articles/id/{article_id}').get_json() == []


def test_draft_pages_open_only_for_their_author(client, admin_client, reader_client, reader_id):
    article_id = draft_of(reader_id, title='Meu rascunho')

    assert reader_client.get(f'/articles/{article_id}/meu-rascunho').status_code == 200
    assert client.get(f'/articles/{article_id}/meu-rascunho').status_code == 404
    assert admin_client.get(f'/articles/{article_id}/meu-rascunho').status_code == 404
    assert client.get(f'/open/{article_id}').status_code == 404


def test_others_cannot_change_or_remove_a_draft(admin_client, reader_id):
    article_id = draft_of(reader_id)

    assert admin_client.patch(f'/api/articles/{article_id}', json={'title': 'x'}).status_code == 404
    assert admin_client.delete(f'/api/articles/{article_id}').status_code == 404
    assert article_repository.get_by_id(article_id, reader_id) is not None


def test_publishing_a_draft_dates_it_and_lists_it(client, reader_client, reader_id):
    article_id = draft_of(reader_id, content='Pronto')

    response = reader_client.patch(f'/api/articles/{article_id}', json={'status': 'published'})

    assert response.status_code == 200
    assert response.get_json()['publish_date'] is not None
    assert [a['article_id'] for a in client.get('/api/articles').get_json()] == [article_id]


def test_publishing_needs_content(reader_client, reader_id):
    article_id = draft_of(reader_id, content='')

    response = reader_client.patch(f'/api/articles/{article_id}', json={'status': 'published'})

    assert response.status_code == 400
    assert response.get_json()['errors'] == {'content': 'content_required'}
    assert article_repository.get_by_id(article_id, reader_id)['status'] == 'draft'


def test_a_published_article_goes_back_to_drafts_and_keeps_its_date(client, reader_client, reader_id):
    article_id = create_article(reader_id)
    first_date = article_repository.get_by_id(article_id)['publish_date']

    reader_client.patch(f'/api/articles/{article_id}', json={'status': 'draft'})
    hidden = client.get('/api/articles').get_json()
    reader_client.patch(f'/api/articles/{article_id}', json={'status': 'published'})

    assert hidden == []
    assert article_repository.get_by_id(article_id)['publish_date'] == first_date


def test_edits_record_when_they_happened(reader_client, reader_id):
    article_id = create_article(reader_id)
    assert article_repository.get_by_id(article_id)['updated_at'] is None

    reader_client.patch(f'/api/articles/{article_id}', json={'title': 'Novo'})

    assert article_repository.get_by_id(article_id)['updated_at'] is not None


def test_own_drafts_list(reader_client, reader_id, admin_id):
    first = draft_of(reader_id, title='Primeiro')
    second = draft_of(reader_id, title='Segundo')
    draft_of(admin_id, title='Do admin')
    create_article(reader_id, title='Publicado')
    # Timestamps have whole seconds, so the drafts are made older than the edit.
    with db_cursor() as cursor:
        cursor.execute('UPDATE ARTICLES SET created_at = NOW() - INTERVAL 1 HOUR')
    reader_client.patch(f'/api/articles/{first}', json={'summary': 'editado agora'})

    drafts = reader_client.get('/api/users/me/drafts').get_json()

    assert [d['article_id'] for d in drafts] == [first, second]
    assert all(d['status'] == 'draft' for d in drafts)


def test_drafts_list_needs_a_session(client):
    assert client.get('/api/users/me/drafts').status_code == 401


@pytest.mark.parametrize('method', ['post', 'delete'])
def test_drafts_cannot_be_liked(reader_client, reader_id, method):
    article_id = draft_of(reader_id)

    assert getattr(reader_client, method)(f'/api/articles/{article_id}/likes').status_code == 404


def test_the_editor_of_another_members_draft_is_not_found(admin_client, reader_id):
    assert admin_client.get(f'/write/{draft_of(reader_id)}').status_code == 404
