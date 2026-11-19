import re

import pytest

from helpers import READER
from links import local_path

READER_LOGIN = {'login': READER['email'], 'password': READER['password']}


@pytest.mark.parametrize('target', ['/', '/articles/12/ola-mundo', '/@reader?tab=1', '/write/3'])
def test_paths_on_this_site_are_kept(target):
    assert local_path(target) == target


@pytest.mark.parametrize('target', [
    None, '', 'https://evil.example', '//evil.example', '/\\evil.example', '/a\\b',
    'evil.example', 'javascript:alert(1)', '/\tevil', '/ evil', '/\nevil', '/café',
])
def test_anything_else_is_refused(target):
    assert local_path(target) is None


def test_signing_in_leads_back_to_the_page(client, reader_id):
    response = client.post('/auth/login', data={**READER_LOGIN, 'next': '/articles/12/ola'})

    assert response.status_code == 302
    assert response.headers['Location'] == '/articles/12/ola'


@pytest.mark.parametrize('target', ['https://evil.example', '//evil.example', '/\\evil.example'])
def test_signing_in_never_leaves_the_site(client, reader_id, target):
    response = client.post('/auth/login', data={**READER_LOGIN, 'next': target})

    assert response.headers['Location'] == '/'


def test_the_login_form_keeps_the_way_back(client, reader_id):
    page = client.get('/auth/login?next=/@reader').get_data(as_text=True)
    failed = client.post('/auth/login', data={'login': 'reader', 'password': 'wrong', 'next': '/@reader'})

    assert '<input type="hidden" name="next" value="/@reader">' in page
    assert 'href="/auth/register?next=/@reader"' in page
    assert '<input type="hidden" name="next" value="/@reader">' in failed.get_data(as_text=True)


def test_an_unsafe_way_back_is_left_out_of_the_form(client):
    page = client.get('/auth/login?next=//evil.example').get_data(as_text=True)

    assert 'name="next"' not in page and 'evil.example' not in page


def test_a_signed_in_member_goes_straight_back(reader_client):
    response = reader_client.get('/auth/login?next=/write')

    assert response.headers['Location'] == '/write'


def test_registering_leads_back_to_the_page(client):
    response = client.post('/auth/register', data={
        'display_name': 'Nova Pessoa', 'username': 'nova_pessoa', 'email': 'nova@example.com',
        'password': 'password-123', 'next': '/@reader',
    })

    assert response.headers['Location'] == '/@reader'


def test_pages_that_need_a_session_send_the_way_back(client):
    response = client.get('/write')

    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login?next=/write'


def test_the_api_leaves_the_way_back_to_the_page(client):
    response = client.put('/api/users/owner/follow')

    assert response.status_code == 401
    assert response.get_json()['login_url'] == '/auth/login'


def test_the_sign_in_link_of_a_page_leads_back_to_it(client, reader_id):
    page = client.get('/@reader').get_data(as_text=True)

    assert 'href="/auth/login?next=/@reader"' in page


def sign_in_link(page: str) -> str:
    return re.search(r'href="(/auth/login[^"]*)"', page).group(1)


def test_the_way_back_keeps_the_address_as_the_browser_sent_it(client):
    page = client.get('/nao%3Fexiste').get_data(as_text=True)

    # The "?" of the address is part of the path, so it stays encoded.
    assert sign_in_link(page) == '/auth/login?next=/nao%253Fexiste'


def test_addresses_with_accents_keep_their_way_back(client):
    page = client.get('/caf%C3%A9').get_data(as_text=True)

    assert sign_in_link(page) == '/auth/login?next=/caf%25C3%25A9'

