from helpers import create_article
from repositories import user_repository

AVATAR = 'a' * 32 + '.webp'


def fill_profile(user_id: int, **fields) -> None:
    user_repository.update_profile(user_id, fields)


def test_profile_page_shows_the_member(client, reader_id):
    fill_profile(reader_id, headline='Engenheira de dados', location='Recife, PE')

    response = client.get('/@reader')

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<h1 class="profile__name" id="profile-name">Reader</h1>' in page
    assert '@reader' in page
    assert 'Engenheira de dados' in page
    assert 'Recife, PE' in page
    assert 'Membro desde' in page
    assert '<title>Reader (@reader) | Social Blog</title>' in page


def test_profile_page_counts_the_articles(client, admin_id):
    create_article(admin_id)

    page = client.get('/@owner').get_data(as_text=True)

    assert '<strong>1</strong>' in page
    assert 'artigo publicado' in page


def test_profile_address_is_lowercase(client, reader_id):
    response = client.get('/@Reader')

    assert response.status_code == 301
    assert response.headers['Location'].endswith('/@reader')


def test_unknown_profile_answers_404(client):
    response = client.get('/@ghost')

    assert response.status_code == 404
    assert 'Página não encontrada' in response.get_data(as_text=True)


def test_only_the_owner_sees_the_edit_link(client, reader_client, reader_id, admin_id):
    assert 'href="/settings/profile"' in reader_client.get('/@reader').get_data(as_text=True)
    assert 'Editar perfil' not in client.get('/@reader').get_data(as_text=True)
    page = reader_client.get('/@owner').get_data(as_text=True)
    assert '<a class="btn btn--secondary" href="/settings/profile">' not in page


def test_website_opens_without_passing_authority(client, reader_id):
    fill_profile(reader_id, website='https://www.leitora.dev/')

    page = client.get('/@reader').get_data(as_text=True)

    assert (
        '<a href="https://www.leitora.dev/" rel="nofollow ugc noopener noreferrer" '
        'target="_blank">leitora.dev</a>'
    ) in page


def test_bio_is_escaped(client, reader_id):
    fill_profile(reader_id, bio='<script>alert(1)</script>')

    page = client.get('/@reader').get_data(as_text=True)

    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;' in page


def test_profile_shows_the_photo(client, reader_id):
    user_repository.set_avatar(reader_id, AVATAR)

    page = client.get('/@reader').get_data(as_text=True)

    assert f'<img class="avatar avatar--xl" src="/media/{AVATAR}"' in page


def test_settings_need_a_session(client):
    response = client.get('/settings/profile')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_settings_start_with_the_current_profile(reader_client, reader_id):
    fill_profile(reader_id, headline='Engenheira', bio='Linha 1')

    page = reader_client.get('/settings/profile').get_data(as_text=True)

    assert 'value="Reader"' in page
    assert 'value="reader"' in page
    assert 'value="Engenheira"' in page
    assert '>Linha 1</textarea>' in page
    assert 'id="avatar-remove"' in page
