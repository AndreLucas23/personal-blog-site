from helpers import create_article


def page_of(client, article_id: int) -> str:
    return client.get(f'/articles/{article_id}', follow_redirects=True).get_data(as_text=True)


def test_article_page_renders_the_markdown(client, admin_id):
    article_id = create_article(admin_id, content='# Seção\n\nTexto **forte** com [link](https://a.dev).')

    page = page_of(client, article_id)

    assert '<h2>Seção</h2>' in page
    assert '<strong>forte</strong>' in page
    assert '<a href="https://a.dev" rel="nofollow ugc noopener noreferrer">link</a>' in page


def test_article_page_shows_the_summary_and_the_reading_time(client, admin_id):
    article_id = create_article(admin_id, summary='Um resumo', content='palavra ' * 450)

    page = page_of(client, article_id)

    assert '<p class="article__summary">Um resumo</p>' in page
    assert '2 min de leitura' in page


def test_author_gets_edit_and_delete(reader_client, reader_id):
    article_id = create_article(reader_id)

    page = page_of(reader_client, article_id)

    assert f'href="/write/{article_id}"' in page
    assert 'aria-label="Excluir artigo"' in page
    assert 'data-next="/@reader"' in page


def test_admin_gets_only_the_moderation_removal(admin_client, reader_id):
    article_id = create_article(reader_id)

    page = page_of(admin_client, article_id)

    assert f'href="/write/{article_id}"' not in page
    assert 'Remover' in page
    assert 'data-next="/admin"' in page


def test_other_members_and_visitors_get_no_actions(client, reader_client, admin_id):
    article_id = create_article(admin_id)

    for viewer in (client, reader_client):
        page = page_of(viewer, article_id)
        assert 'data-delete-article' not in page
        assert 'id="edit-btn"' not in page
