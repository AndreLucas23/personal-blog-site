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

    response = client.get(f'/open/{article_id}')

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<h1 class="article__title" id="view-title">Olá</h1>' in page
    assert '<span class="byline__name">Owner</span>' in page
    assert 'Primeiro post' in page
    assert '<title>Olá | Social Blog</title>' in page


def test_article_page_answers_404_for_missing_article(client):
    assert client.get('/open/999').status_code == 404


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


def test_only_admins_get_the_edit_button(admin_client, reader_client, admin_id):
    article_id = create_article(admin_id)

    assert 'id="edit-btn"' in admin_client.get(f'/open/{article_id}').get_data(as_text=True)
    assert 'id="edit-btn"' not in reader_client.get(f'/open/{article_id}').get_data(as_text=True)


def test_member_content_is_escaped(client, admin_id):
    article_id = create_article(admin_id, title='<b>x</b>', content='<script>alert(1)</script>')

    page = client.get(f'/open/{article_id}').get_data(as_text=True)

    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in page
    assert '<b>x</b>' not in page


@pytest.mark.parametrize('path', ['/', '/auth/login', '/auth/register', '/admin', '/open/{article_id}'])
def test_pages_have_no_inline_code(admin_client, admin_id, path):
    article_id = create_article(admin_id)

    page = admin_client.get(path.format(article_id=article_id)).get_data(as_text=True)

    assert not INLINE_SCRIPT.search(page)
    assert not INLINE_STYLE.search(page)
    assert not INLINE_HANDLER.search(page)
