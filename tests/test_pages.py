import re

import pytest

from helpers import create_article

# A strict Content Security Policy blocks inline code, so pages must not have any.
INLINE_SCRIPT = re.compile(r'<script(?![^>]*\ssrc=)[^>]*>', re.IGNORECASE)
INLINE_STYLE = re.compile(r'\sstyle=', re.IGNORECASE)
INLINE_HANDLER = re.compile(r'\son[a-z]+=', re.IGNORECASE)


def test_home_page_renders_for_visitors(client):
    response = client.get('/')

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'Artigos' in page
    assert '<title>Social Blog</title>' in page


def test_article_page_renders_existing_article(client, admin_id):
    article_id = create_article(admin_id, title='Olá', content='Primeiro post')

    response = client.get(f'/articles/{article_id}/ola')

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<h1 class="article__title" id="view-title">Olá</h1>' in page
    assert '<a class="byline__name" href="/@owner">Owner</a>' in page
    assert 'Primeiro post' in page
    assert '<title>Olá | Social Blog</title>' in page


def test_article_page_answers_404_for_missing_article(client):
    assert client.get('/articles/999/x').status_code == 404
    assert client.get('/open/999').status_code == 404


@pytest.mark.parametrize('path', [
    '/open/{article_id}',
    '/articles/{article_id}',
    '/articles/{article_id}/titulo-antigo',
])
def test_other_article_addresses_redirect_to_the_readable_one(client, admin_id, path):
    article_id = create_article(admin_id, title='Ação & Reação: parte 2!')

    response = client.get(path.format(article_id=article_id))

    assert response.status_code == 301
    assert response.headers['Location'].endswith(f'/articles/{article_id}/acao-reacao-parte-2')


def test_article_page_describes_itself_for_search_engines(client, admin_id):
    article_id = create_article(admin_id, title='Olá', summary='Um resumo curto')

    page = client.get(f'/articles/{article_id}/ola').get_data(as_text=True)

    assert '<meta name="description" content="Um resumo curto">' in page
    assert f'<link rel="canonical" href="/articles/{article_id}/ola">' in page


def test_login_and_registration_pages_render(client):
    assert client.get('/auth/login').status_code == 200
    assert client.get('/auth/register').status_code == 200


def test_visitors_see_the_sign_in_buttons(client):
    page = client.get('/').get_data(as_text=True)

    assert 'class="topnav__guest"' in page
    assert 'id="account-menu"' not in page


def test_members_see_their_account_menu_without_the_admin_link(reader_client):
    page = reader_client.get('/').get_data(as_text=True)

    assert 'id="account-menu"' in page
    assert 'Reader' in page
    assert '@reader' in page
    assert 'href="/admin"' not in page
    assert 'class="topnav__guest"' not in page


def test_admins_see_the_admin_link(admin_client):
    page = admin_client.get('/').get_data(as_text=True)

    assert 'href="/admin"' in page


def test_current_page_is_marked_in_the_navigation(admin_client):
    page = admin_client.get('/admin').get_data(as_text=True)

    assert re.search(r'href="/admin"\s+aria-current="page"', page)
    assert not re.search(r'href="/"\s+aria-current="page"', page)


def test_only_the_author_gets_the_edit_button(admin_client, reader_client, admin_id):
    article_id = create_article(admin_id)

    path = f'/articles/{article_id}/titulo'
    assert 'id="edit-btn"' in admin_client.get(path).get_data(as_text=True)
    assert 'id="edit-btn"' not in reader_client.get(path).get_data(as_text=True)


def test_member_content_is_escaped(client, admin_id):
    article_id = create_article(admin_id, title='<b>x</b>', content='<script>alert(1)</script>')

    page = client.get(f'/open/{article_id}', follow_redirects=True).get_data(as_text=True)

    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in page
    assert '<b>x</b>' not in page


@pytest.mark.parametrize('path', [
    '/', '/auth/login', '/auth/register', '/admin', '/articles/{article_id}/titulo',
    '/@owner', '/settings/profile',
])
def test_pages_have_no_inline_code(admin_client, admin_id, path):
    article_id = create_article(admin_id)

    page = admin_client.get(path.format(article_id=article_id)).get_data(as_text=True)

    assert not INLINE_SCRIPT.search(page)
    assert not INLINE_STYLE.search(page)
    assert not INLINE_HANDLER.search(page)


def test_registration_page_carries_the_username_rules(client):
    page = client.get('/auth/register').get_data(as_text=True)

    assert 'data-pattern="^[a-z0-9_]+$"' in page
    assert 'data-reserved="admin me moderacao socialblog suporte"' in page
