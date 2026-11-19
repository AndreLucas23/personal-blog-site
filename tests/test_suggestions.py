from datetime import datetime, timedelta

import pytest

from db import db_cursor
from helpers import create_article, create_user

SUGGESTIONS_URL = '/api/users/me/suggestions'


def member(username: str) -> int:
    return create_user(username.title(), username, f'{username}@example.com', 'password-123')


def follows(follower_id: int, *followed_ids: int) -> None:
    with db_cursor() as cursor:
        for followed_id in followed_ids:
            cursor.execute(
                'INSERT INTO FOLLOWS (follower_id, followed_id) VALUES (%s, %s)', (follower_id, followed_id)
            )


def published(author_id: int, day: int) -> None:
    article_id = create_article(author_id)
    with db_cursor() as cursor:
        cursor.execute(
            'UPDATE ARTICLES SET publish_date = %s WHERE article_id = %s',
            (datetime(2026, 3, 1) + timedelta(days=day), article_id),
        )


def suggested(client, query: str = '') -> list[str]:
    return [m['username'] for m in client.get(SUGGESTIONS_URL + query).get_json()['members']]


def test_members_followed_by_the_people_you_follow_come_first(reader_client, reader_id):
    ana, bia, caio, dani = (member(name) for name in ('ana', 'bia', 'caio', 'dani'))
    follows(reader_id, ana, bia)
    follows(ana, caio, dani)
    follows(bia, caio)

    # Caio is followed by two of the people the reader follows, Dani by one.
    assert suggested(reader_client) == ['caio', 'dani']


def test_suggestions_leave_out_yourself_and_whom_you_follow(reader_client, reader_id):
    ana, bia = member('ana'), member('bia')
    follows(reader_id, ana, bia)
    follows(ana, reader_id, bia)

    assert suggested(reader_client) == []


def test_recent_authors_fill_the_rest(reader_client, reader_id):
    ana, bia, caio, dani = (member(name) for name in ('ana', 'bia', 'caio', 'dani'))
    follows(reader_id, ana)
    follows(ana, bia)
    published(caio, day=1)
    published(dani, day=5)
    published(bia, day=9)
    published(reader_id, day=10)

    # Bia comes from the people followed; then the authors, the most recent first.
    assert suggested(reader_client) == ['bia', 'dani', 'caio']


def test_drafts_do_not_make_an_author(reader_client):
    ana = member('ana')
    create_article(ana, status='draft')

    assert suggested(reader_client) == []


def test_the_number_of_suggestions_can_be_chosen(reader_client):
    for day, name in enumerate(('ana', 'bia', 'caio', 'dani')):
        published(member(name), day=day)

    assert len(suggested(reader_client)) == 3
    assert suggested(reader_client, '?limit=2') == ['dani', 'caio']


@pytest.mark.parametrize('limit', ['0', '11', 'abc'])
def test_invalid_limits_are_refused(reader_client, limit):
    assert reader_client.get(f'{SUGGESTIONS_URL}?limit={limit}').status_code == 400


def test_suggestions_need_a_session(client):
    assert client.get(SUGGESTIONS_URL).status_code == 401


def test_suggestions_carry_the_profile_of_each_member(reader_client):
    published(member('ana'), day=1)

    assert reader_client.get(SUGGESTIONS_URL).get_json()['members'] == [
        {'username': 'ana', 'display_name': 'Ana', 'headline': None, 'avatar_url': None, 'followed': False}
    ]


def test_members_get_the_suggestions_card(reader_client):
    page = reader_client.get('/').get_data(as_text=True)

    assert 'id="suggestions"' in page and 'data-viewer="reader"' in page


def test_visitors_do_not(client):
    assert 'id="suggestions"' not in client.get('/').get_data(as_text=True)


def test_authors_come_only_from_the_latest_articles(reader_client, monkeypatch):
    from repositories import follow_repository

    monkeypatch.setattr(follow_repository, 'RECENT_ARTICLES', 2)
    ana, bia = member('ana'), member('bia')
    published(ana, day=1)
    published(bia, day=8)
    published(bia, day=9)

    # Ana's article is older than the two latest, which are both by Bia.
    assert suggested(reader_client) == ['bia']
