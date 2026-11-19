from datetime import datetime, timedelta

import pytest

import pagination
from db import db_cursor
from helpers import create_article


def publish_at(article_id: int, published: datetime) -> None:
    with db_cursor() as cursor:
        cursor.execute('UPDATE ARTICLES SET publish_date = %s WHERE article_id = %s', (published, article_id))


def titles(page: dict) -> list[str]:
    return [article['article_title'] for article in page['articles']]


def create_dated(author_id: int, count: int, start: datetime = datetime(2026, 3, 1, 12, 0)) -> None:
    """Articles 1 to count, one day apart, so article count is the newest."""
    for number in range(1, count + 1):
        publish_at(create_article(author_id, title=f'Artigo {number}'), start + timedelta(days=number))


def test_pages_go_newest_first_until_the_last(client, admin_id):
    create_dated(admin_id, 5)

    first = client.get('/api/articles?limit=2').get_json()
    second = client.get(f"/api/articles?limit=2&cursor={first['next_cursor']}").get_json()
    last = client.get(f"/api/articles?limit=2&cursor={second['next_cursor']}").get_json()

    assert titles(first) == ['Artigo 5', 'Artigo 4']
    assert titles(second) == ['Artigo 3', 'Artigo 2']
    assert titles(last) == ['Artigo 1']
    assert last['next_cursor'] is None


def test_a_full_last_page_has_no_next_cursor(client, admin_id):
    create_dated(admin_id, 2)

    page = client.get('/api/articles?limit=2').get_json()

    assert titles(page) == ['Artigo 2', 'Artigo 1']
    assert page['next_cursor'] is None


def test_articles_of_the_same_second_are_neither_lost_nor_repeated(client, admin_id):
    same_second = datetime(2026, 3, 1, 12, 0)
    for number in range(1, 4):
        publish_at(create_article(admin_id, title=f'Artigo {number}'), same_second)

    first = client.get('/api/articles?limit=2').get_json()
    rest = client.get(f"/api/articles?limit=2&cursor={first['next_cursor']}").get_json()

    assert titles(first) + titles(rest) == ['Artigo 3', 'Artigo 2', 'Artigo 1']


def test_pages_hold_twenty_articles_by_default(client, admin_id):
    create_dated(admin_id, pagination.PAGE_SIZE + 1)

    page = client.get('/api/articles').get_json()

    assert len(page['articles']) == pagination.PAGE_SIZE
    assert page['next_cursor'] is not None


def test_a_members_articles_come_in_pages_too(client, admin_id, reader_id):
    create_dated(reader_id, 3)
    create_article(admin_id, title='Do admin')

    first = client.get('/api/articles?author=reader&limit=2').get_json()
    rest = client.get(f"/api/articles?author=reader&limit=2&cursor={first['next_cursor']}").get_json()

    assert titles(first) == ['Artigo 3', 'Artigo 2']
    assert titles(rest) == ['Artigo 1'] and rest['next_cursor'] is None


def test_a_cursor_keeps_its_place_when_new_articles_arrive(client, admin_id):
    create_dated(admin_id, 3)
    first = client.get('/api/articles?limit=2').get_json()

    create_article(admin_id, title='Novo')
    rest = client.get(f"/api/articles?limit=2&cursor={first['next_cursor']}").get_json()

    assert titles(rest) == ['Artigo 1']


@pytest.mark.parametrize('cursor', ['abc', '', 'MTp4', '%%%', 'OTk5OTk5OTk5OTk5OTk5OTk5Ojk='])
def test_invalid_cursors_are_refused(client, cursor):
    response = client.get(f'/api/articles?cursor={cursor}')

    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid cursor'}


@pytest.mark.parametrize('limit', ['0', '51', '-1', 'abc', '2.5', ''])
def test_invalid_limits_are_refused(client, limit):
    response = client.get(f'/api/articles?limit={limit}')

    assert response.status_code == 400
    assert response.get_json() == {'message': 'The limit must be from 1 to 50'}


def test_cursors_round_trip():
    published = datetime(2026, 11, 19, 13, 45, 7)

    assert pagination.decode_cursor(pagination.encode_cursor(published, 42)) == (published, 42)
