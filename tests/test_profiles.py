import pytest

from helpers import READER, create_article
from repositories import user_repository


def update(client, **fields):
    return client.patch('/api/users/me', json=fields)


def test_public_profile_shows_no_email(client, reader_id):
    response = client.get('/api/users/reader')

    assert response.status_code == 200
    profile = response.get_json()
    assert profile['username'] == 'reader'
    assert profile['display_name'] == 'Reader'
    assert profile['articles'] == 0
    assert profile['headline'] is None
    assert profile['joined_at']
    assert 'email' not in profile


def test_public_profile_reads_the_username_in_any_case_and_with_the_at(client, reader_id):
    assert client.get('/api/users/Reader').status_code == 200
    assert client.get('/api/users/@reader').status_code == 200


def test_public_profile_counts_the_articles(client, admin_id):
    create_article(admin_id)
    create_article(admin_id)

    assert client.get('/api/users/owner').get_json()['articles'] == 2


def test_unknown_profile_answers_404(client):
    response = client.get('/api/users/ghost')

    assert response.status_code == 404
    assert response.get_json() == {'message': 'User not found'}


def test_own_profile_needs_a_session(client):
    assert client.get('/api/users/me').status_code == 401
    assert client.patch('/api/users/me', json={'headline': 'x'}).status_code == 401


def test_own_profile_includes_the_email(reader_client):
    profile = reader_client.get('/api/users/me').get_json()

    assert profile['email'] == READER['email']
    assert profile['username'] == 'reader'


def test_update_profile_fields(reader_client):
    response = update(
        reader_client,
        display_name='  Leitora Dias ',
        headline=' Engenheira de dados ',
        bio='Primeira linha\r\nSegunda linha  ',
        location='Recife, PE',
        website='leitora.dev',
    )

    assert response.status_code == 200
    profile = response.get_json()
    assert profile['display_name'] == 'Leitora Dias'
    assert profile['headline'] == 'Engenheira de dados'
    assert profile['bio'] == 'Primeira linha\nSegunda linha'
    assert profile['location'] == 'Recife, PE'
    assert profile['website'] == 'https://leitora.dev'
    assert reader_client.get('/api/users/reader').get_json()['headline'] == 'Engenheira de dados'


def test_empty_optional_fields_are_cleared(reader_client):
    update(reader_client, headline='Algo', website='https://a.dev')

    profile = update(reader_client, headline='', website=None).get_json()

    assert profile['headline'] is None
    assert profile['website'] is None


def test_change_the_username(client, reader_client, reader_id):
    response = update(reader_client, username=' @Leitora_2026 ')

    assert response.status_code == 200
    assert response.get_json()['username'] == 'leitora_2026'
    assert client.get('/api/users/leitora_2026').status_code == 200
    assert client.get('/api/users/reader').status_code == 404


def test_taken_username_answers_409(reader_client, admin_id):
    response = update(reader_client, username='Owner')

    assert response.status_code == 409
    assert response.get_json() == {
        'message': 'Username taken',
        'errors': {'username': 'username_taken'},
    }
    assert user_repository.get_by_email(READER['email'])['username'] == 'reader'


@pytest.mark.parametrize(('fields', 'errors'), [
    ({'display_name': '  '}, {'display_name': 'name_required'}),
    ({'username': 'ab'}, {'username': 'username_too_short'}),
    ({'username': 'me'}, {'username': 'username_too_short'}),
    ({'username': 'admin'}, {'username': 'username_reserved'}),
    ({'headline': 'x' * 121}, {'headline': 'headline_too_long'}),
    ({'bio': 'x' * 501}, {'bio': 'bio_too_long'}),
    ({'location': 'x' * 81}, {'location': 'location_too_long'}),
    ({'website': 'not a site'}, {'website': 'website_invalid'}),
    ({'website': 'javascript:alert(1)'}, {'website': 'website_invalid'}),
    ({'website': 'ftp://files.example.com'}, {'website': 'website_invalid'}),
    ({'display_name': '', 'website': 'x'}, {'display_name': 'name_required', 'website': 'website_invalid'}),
])
def test_invalid_profile_fields_are_reported_and_nothing_changes(reader_client, fields, errors):
    response = update(reader_client, **fields)

    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid profile', 'errors': errors}
    profile = reader_client.get('/api/users/me').get_json()
    assert profile['display_name'] == 'Reader'
    assert profile['username'] == 'reader'


def test_non_text_values_are_rejected(reader_client):
    response = update(reader_client, display_name=42)

    assert response.status_code == 400
    assert response.get_json()['errors'] == {'display_name': 'invalid'}


def test_update_needs_a_known_field(reader_client):
    response = update(reader_client, is_admin=True, email='x@example.com')

    assert response.status_code == 400
    assert response.get_json() == {'message': 'No fields to update'}


def test_update_ignores_fields_members_cannot_change(reader_client):
    update(reader_client, headline='Nova', is_admin=1, email='x@example.com')

    user = user_repository.get_by_username('reader')
    assert user['is_admin'] == 0
    assert user['email'] == READER['email']


def test_update_rejects_a_body_that_is_not_an_object(reader_client):
    assert reader_client.patch('/api/users/me', json=['headline']).status_code == 400
