from helpers import create_article


def test_editor_needs_a_session(client, admin_id):
    article_id = create_article(admin_id)

    for path in ('/write', f'/write/{article_id}'):
        response = client.get(path)
        assert response.status_code == 302, path
        assert response.headers['Location'].endswith('/auth/login')


def test_new_article_editor_starts_empty(reader_client):
    response = reader_client.get('/write')

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<title>Escrever artigo | Social Blog</title>' in page
    assert 'data-article-id=""' in page
    assert 'maxlength="150"' in page
    assert 'maxlength="300"' in page
    assert 'maxlength="50000"' in page
    assert 'Publicar' in page


def test_author_edits_with_the_current_fields(reader_client, reader_id):
    article_id = create_article(reader_id, title='Meu título', content='## Texto', summary='Resumo')

    response = reader_client.get(f'/write/{article_id}')

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert f'data-article-id="{article_id}"' in page
    assert '>Meu título</textarea>' in page
    assert '>Resumo</textarea>' in page
    assert '>## Texto</textarea>' in page
    assert 'Salvar alterações' in page
    assert f'href="/articles/{article_id}/meu-titulo"' in page


def test_only_the_author_opens_the_editor_of_an_article(reader_client, admin_id):
    article_id = create_article(admin_id)

    assert reader_client.get(f'/write/{article_id}').status_code == 403


def test_editor_of_a_missing_article_answers_404(reader_client):
    assert reader_client.get('/write/999').status_code == 404


def test_editor_content_is_escaped(reader_client, reader_id):
    article_id = create_article(reader_id, content='</textarea><script>alert(1)</script>')

    page = reader_client.get(f'/write/{article_id}').get_data(as_text=True)

    assert '<script>alert(1)</script>' not in page
    assert '&lt;/textarea&gt;&lt;script&gt;' in page


def test_members_see_the_write_link_and_visitors_do_not(client, reader_client):
    assert 'href="/write"' in reader_client.get('/').get_data(as_text=True)
    assert 'href="/write"' not in client.get('/').get_data(as_text=True)


def test_editor_offers_the_actions_of_the_article_state(reader_client, reader_id):
    draft = create_article(reader_id, status='draft')
    published = create_article(reader_id)

    new_page = reader_client.get('/write').get_data(as_text=True)
    draft_page = reader_client.get(f'/write/{draft}').get_data(as_text=True)
    published_page = reader_client.get(f'/write/{published}').get_data(as_text=True)

    assert 'id="editor-draft"' in new_page and 'id="editor-unpublish"' not in new_page
    assert 'id="editor-draft"' in draft_page and 'data-status="draft"' in draft_page
    assert 'id="editor-unpublish"' in published_page and 'id="editor-draft"' not in published_page


def test_editor_starts_with_the_tags(reader_client, reader_id):
    article_id = create_article(reader_id)
    reader_client.patch(f'/api/articles/{article_id}', json={'tags': ['sql', 'python']})

    page = reader_client.get(f'/write/{article_id}').get_data(as_text=True)

    assert page.index('data-tag="sql"') < page.index('data-tag="python"')
    assert 'data-max="5"' in page
    # A pasted list is longer than one tag, so the length is checked per tag instead.
    assert 'data-min-length="2"' in page and 'data-max-length="30"' in page
