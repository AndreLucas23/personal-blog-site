from db import db_cursor

FOLLOW_URL = '/api/users/{}/follow'


def profile(client, username: str) -> dict:
    return client.get(f'/api/users/{username}').get_json()


def test_a_member_follows_another(client, reader_client, admin_id):
    response = reader_client.put(FOLLOW_URL.format('owner'))

    assert response.status_code == 200
    assert response.get_json() == {'followed': True, 'followers': 1}
    assert profile(reader_client, 'owner')['followed'] is True
    assert profile(client, 'owner')['followers'] == 1
    assert profile(client, 'reader')['following'] == 1


def test_following_again_changes_nothing(reader_client, admin_id):
    reader_client.put(FOLLOW_URL.format('owner'))

    again = reader_client.put(FOLLOW_URL.format('owner'))

    assert again.get_json() == {'followed': True, 'followers': 1}


def test_a_member_unfollows(reader_client, admin_id):
    reader_client.put(FOLLOW_URL.format('owner'))

    response = reader_client.delete(FOLLOW_URL.format('owner'))
    again = reader_client.delete(FOLLOW_URL.format('owner'))

    assert response.get_json() == {'followed': False, 'followers': 0}
    assert again.status_code == 200 and again.get_json() == {'followed': False, 'followers': 0}
    assert profile(reader_client, 'owner')['followed'] is False


def test_follows_point_one_way(admin_client, reader_client):
    reader_client.put(FOLLOW_URL.format('owner'))

    assert profile(admin_client, 'reader')['followed'] is False
    assert profile(admin_client, 'reader')['followers'] == 0


def test_the_username_is_read_like_everywhere_else(reader_client, admin_id):
    assert reader_client.put(FOLLOW_URL.format('@Owner')).get_json()['followed'] is True


def test_members_cannot_follow_themselves(reader_client):
    response = reader_client.put(FOLLOW_URL.format('reader'))

    assert response.status_code == 400
    assert response.get_json() == {'message': 'You cannot follow yourself'}
    assert profile(reader_client, 'reader')['followers'] == 0


def test_following_a_missing_member_answers_404(reader_client):
    for method in (reader_client.put, reader_client.delete):
        response = method(FOLLOW_URL.format('ghost'))
        assert response.status_code == 404
        assert response.get_json() == {'message': 'User not found'}


def test_following_needs_a_session(client, admin_id):
    assert client.put(FOLLOW_URL.format('owner')).status_code == 401
    assert client.delete(FOLLOW_URL.format('owner')).status_code == 401


def test_profiles_start_without_follows(client, reader_id):
    shown = profile(client, 'reader')

    assert (shown['followers'], shown['following'], shown['followed']) == (0, 0, False)


def test_your_own_profile_carries_your_counts(reader_client, admin_id):
    reader_client.put(FOLLOW_URL.format('owner'))

    own = reader_client.get('/api/users/me').get_json()

    assert (own['followers'], own['following'], own['followed']) == (0, 1, False)


def test_follows_go_away_with_the_account(client, reader_client, reader_id, admin_id):
    reader_client.put(FOLLOW_URL.format('owner'))

    with db_cursor() as cursor:
        cursor.execute('DELETE FROM USERS WHERE user_id = %s', (reader_id,))

    assert profile(client, 'owner')['followers'] == 0


def page(client, path: str) -> str:
    return client.get(path, follow_redirects=True).get_data(as_text=True)


def test_a_profile_offers_to_follow_its_member(reader_client, admin_id):
    shown = page(reader_client, '/@owner')

    assert 'data-follow="owner"' in shown and 'aria-pressed="false"' in shown
    assert 'aria-label="Seguir Owner"' in shown


def test_a_followed_member_shows_seguindo(reader_client, admin_id):
    reader_client.put(FOLLOW_URL.format('owner'))

    shown = page(reader_client, '/@owner')

    assert 'aria-pressed="true"' in shown and 'Seguindo' in shown
    assert '<strong id="profile-followers">1</strong>' in shown and '>seguidor<' in shown


def test_your_own_profile_has_no_follow_button(reader_client):
    shown = page(reader_client, '/@reader')

    assert 'data-follow' not in shown and 'Editar perfil' in shown


def test_visitors_follow_by_signing_in_first(client, reader_id):
    shown = page(client, '/@reader')

    assert 'href="/auth/login?next=/@reader" aria-label="Seguir Reader">Seguir</a>' in shown


def test_profiles_count_followers_and_following(client, reader_client, admin_id):
    reader_client.put(FOLLOW_URL.format('owner'))

    owner = page(client, '/@owner')
    reader = page(client, '/@reader')

    assert '<strong id="profile-followers">1</strong>' in owner
    assert '<strong id="profile-followers">0</strong>' in reader and '>seguidores<' in reader
    assert '<li><strong>1</strong> seguindo</li>' in reader


def test_articles_offer_to_follow_their_author(client, reader_client, admin_client, reader_id):
    from helpers import create_article
    article_id = create_article(reader_id)
    path = f'/articles/{article_id}'

    admin_client.put(FOLLOW_URL.format('reader'))

    assert 'data-follow="reader"' in page(admin_client, path)
    assert 'aria-pressed="true"' in page(admin_client, path)
    assert 'data-follow' not in page(reader_client, path)
    assert f'href="/auth/login?next={path}/titulo" aria-label="Seguir Reader">Seguir</a>' in page(client, path)
