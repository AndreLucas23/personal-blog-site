import mysql.connector
import pytest

import article_validation
from db import db_cursor
from helpers import create_article
from repositories import article_repository


def tag_count() -> int:
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM TAGS')
        return cursor.fetchone()[0]


@pytest.mark.parametrize(('raw', 'tag'), [
    ('Python', 'python'),
    ('  Banco de Dados ', 'banco-de-dados'),
    ('#carreira', 'carreira'),
    ('front_end', 'front-end'),
    ('Educação', 'educação'),
    ('Cafe\u0301', 'café'),
    ('हिंदी', 'हिंदी'),
    ('\u0301\u0301python', 'python'),
    ('c++', 'c'),
    ('--a--b--', 'a-b'),
])
def test_normalize_tag(raw, tag):
    assert article_validation.normalize_tag(raw) == tag


def test_normalize_tags_drops_blanks_and_repeats_in_order():
    assert article_validation.normalize_tags(['Python', ' ', 'SQL', 'python', '#sql']) == ['python', 'sql']


def test_articles_are_created_with_their_tags(reader_client):
    article = reader_client.post('/api/articles', json={
        'title': 'T', 'content': 'C', 'tags': ['  Banco de Dados ', '#Python', 'python'],
    }).get_json()

    assert article['tags'] == ['banco-de-dados', 'python']


def test_tags_show_in_lists_in_the_authors_order(client, reader_client):
    reader_client.post('/api/articles', json={'title': 'T', 'content': 'C', 'tags': ['zeta', 'alfa']})

    assert client.get('/api/articles').get_json()[0]['tags'] == ['zeta', 'alfa']


def test_articles_without_tags_have_an_empty_list(client, admin_id):
    create_article(admin_id)

    assert client.get('/api/articles').get_json()[0]['tags'] == []


def test_patch_replaces_and_clears_the_tags(reader_client, reader_id):
    article_id = create_article(reader_id)

    replaced = reader_client.patch(f'/api/articles/{article_id}', json={'tags': ['sql', 'mysql']})
    cleared = reader_client.patch(f'/api/articles/{article_id}', json={'tags': []})

    assert replaced.get_json()['tags'] == ['sql', 'mysql']
    assert cleared.get_json()['tags'] == []


def test_changing_tags_counts_as_an_edit(reader_client, reader_id):
    article_id = create_article(reader_id)

    article = reader_client.patch(f'/api/articles/{article_id}', json={'tags': ['sql']}).get_json()

    assert article['updated_at'] is not None


@pytest.mark.parametrize(('tags', 'code'), [
    (['um', 'dois', 'tres', 'quatro', 'cinco', 'seis'], 'tags_too_many'),
    (['x'], 'tag_too_short'),
    (['x' * 31], 'tag_too_long'),
    ('python', 'invalid'),
    (['python', 3], 'invalid'),
])
def test_invalid_tags_are_refused(reader_client, tags, code):
    response = reader_client.post('/api/articles', json={'title': 'T', 'content': 'C', 'tags': tags})

    assert response.status_code == 400
    assert response.get_json()['errors'] == {'tags': code}


def test_variants_with_and_without_accents_are_one_tag(reader_client):
    first = reader_client.post('/api/articles', json={'title': 'A', 'content': 'C', 'tags': ['programação']})
    second = reader_client.post('/api/articles', json={'title': 'B', 'content': 'C', 'tags': ['programacao', 'Programação']})

    assert first.get_json()['tags'] == ['programação']
    assert second.get_json()['tags'] == ['programação']
    assert tag_count() == 1


def test_removing_an_article_removes_its_tags_but_keeps_the_topic(reader_client, reader_id):
    article_id = create_article(reader_id)
    reader_client.patch(f'/api/articles/{article_id}', json={'tags': ['sql']})

    reader_client.delete(f'/api/articles/{article_id}')

    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM ARTICLE_TAGS')
        assert cursor.fetchone()[0] == 0
    assert tag_count() == 1


# A tag longer than its column fails in the database, after the article row is written.
TOO_LONG_FOR_THE_COLUMN = ['x' * 31]


def test_an_article_is_not_created_when_its_tags_fail(reader_id):
    with pytest.raises(mysql.connector.Error):
        article_repository.create('Com tags', None, 'Conteúdo', reader_id, tags=TOO_LONG_FOR_THE_COLUMN)

    assert article_repository.get_all() == []


def test_an_article_keeps_its_fields_when_its_tags_fail(reader_id):
    article_id = create_article(reader_id, title='Antes')

    with pytest.raises(mysql.connector.Error):
        article_repository.update(article_id, {'title': 'Depois'}, TOO_LONG_FOR_THE_COLUMN)

    assert article_repository.get_by_id(article_id)['article_title'] == 'Antes'
