from helpers import create_article


def test_home_page_renders_for_visitors(client):
    response = client.get('/')

    assert response.status_code == 200
    assert 'Artigos' in response.get_data(as_text=True)


def test_article_page_renders_existing_article(client, admin_id):
    article_id = create_article(admin_id, title='Olá', content='Primeiro post')

    response = client.get(f'/open/{article_id}')

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'Olá' in page
    assert 'por Owner' in page


def test_article_page_answers_404_for_missing_article(client):
    assert client.get('/open/999').status_code == 404


def test_login_and_registration_pages_render(client):
    assert client.get('/auth/login').status_code == 200
    assert client.get('/auth/register').status_code == 200
