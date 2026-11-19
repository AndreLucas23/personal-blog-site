from datetime import datetime, timedelta

import pytest

from db import db_cursor
from helpers import create_user


def member(username: str) -> int:
    return create_user(username.title(), username, f'{username}@example.com', 'password-123')


def follow_at(follower_id: int, followed_id: int, when: datetime) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO FOLLOWS (follower_id, followed_id, created_at) VALUES (%s, %s, %s)',
            (follower_id, followed_id, when),
        )


def usernames(response) -> list[str]:
    return [listed['username'] for listed in response.get_json()['members']]


START = datetime(2026, 3, 1, 12, 0)


def test_followers_come_with_the_most_recent_follows_first(client, admin_id):
    for day, username in enumerate(('ana', 'bia', 'caio')):
        follow_at(member(username), admin_id, START + timedelta(days=day))

    response = client.get('/api/users/owner/followers')

    assert response.status_code == 200
    assert usernames(response) == ['caio', 'bia', 'ana']
    assert response.get_json()['next_cursor'] is None


def test_following_lists_whom_a_member_follows(client, admin_id):
    for day, username in enumerate(('ana', 'bia')):
        follow_at(admin_id, member(username), START + timedelta(days=day))

    assert usernames(client.get('/api/users/owner/following')) == ['bia', 'ana']
    assert usernames(client.get('/api/users/owner/followers')) == []


def test_lists_come_in_pages(client, admin_id):
    same_second = START
    for username in ('ana', 'bia', 'caio'):
        follow_at(member(username), admin_id, same_second)

    first = client.get('/api/users/owner/followers?limit=2').get_json()
    rest = client.get(f"/api/users/owner/followers?limit=2&cursor={first['next_cursor']}").get_json()

    listed = [m['username'] for m in first['members'] + rest['members']]
    assert sorted(listed) == ['ana', 'bia', 'caio'] and len(set(listed)) == 3
    assert rest['next_cursor'] is None


def test_members_listed_carry_their_profile(client, admin_id):
    follow_at(member('ana'), admin_id, START)

    listed = client.get('/api/users/owner/followers').get_json()['members'][0]

    assert listed == {'username': 'ana', 'display_name': 'Ana', 'headline': None,
                      'avatar_url': None, 'followed': False}


def test_lists_tell_whether_the_viewer_follows_each_member(reader_client, reader_id, admin_id):
    ana, bia = member('ana'), member('bia')
    follow_at(ana, admin_id, START)
    follow_at(bia, admin_id, START + timedelta(days=1))
    follow_at(reader_id, ana, START)

    listed = reader_client.get('/api/users/owner/followers').get_json()['members']

    assert {m['username']: m['followed'] for m in listed} == {'ana': True, 'bia': False}


def test_the_lists_of_a_missing_member_answer_404(client):
    for path in ('/api/users/ghost/followers', '/api/users/ghost/following'):
        response = client.get(path)
        assert response.status_code == 404
        assert response.get_json() == {'message': 'User not found'}


@pytest.mark.parametrize('query', ['cursor=abc', 'limit=0', 'limit=51'])
def test_invalid_pages_are_refused(client, admin_id, query):
    assert client.get(f'/api/users/owner/followers?{query}').status_code == 400


def test_the_followers_page_names_its_list(client, admin_id):
    follow_at(member('ana'), admin_id, START)

    page = client.get('/@owner/followers').get_data(as_text=True)

    assert '<title>Seguidores de Owner | Social Blog</title>' in page
    assert 'data-kind="followers"' in page and 'data-username="owner"' in page
    assert 'Seguidores <span class="tab__count">1</span>' in page
    assert 'href="/@owner/followers"\n            aria-current="page"' in page


def test_the_following_page_names_its_list(client, admin_id):
    page = client.get('/@owner/following').get_data(as_text=True)

    assert '<title>Quem Owner segue | Social Blog</title>' in page
    assert 'data-kind="following"' in page


def test_visitors_get_a_way_to_sign_in_and_come_back(client, admin_id):
    page = client.get('/@owner/followers').get_data(as_text=True)

    assert 'data-viewer=""' in page
    assert 'data-login-url="/auth/login?next=/@owner/followers"' in page


def test_the_lists_know_who_reads_them(reader_client, admin_id):
    page = reader_client.get('/@owner/followers').get_data(as_text=True)

    assert 'data-viewer="reader"' in page


def test_the_pages_of_a_missing_member_answer_404(client):
    assert client.get('/@ghost/followers').status_code == 404
    assert client.get('/@ghost/following').status_code == 404


def test_the_pages_have_one_address_whatever_the_letter_case(client, admin_id):
    response = client.get('/@Owner/following')

    assert response.status_code == 301
    assert response.headers['Location'] == '/@owner/following'


def test_profile_counts_open_the_lists(client, admin_id):
    page = client.get('/@owner').get_data(as_text=True)

    assert 'href="/@owner/followers"' in page and 'href="/@owner/following"' in page
