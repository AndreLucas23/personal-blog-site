import re
from datetime import datetime

from db import db_cursor
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


def test_article_page_shows_the_tags_in_order(client, reader_client, reader_id):
    article_id = create_article(reader_id)
    reader_client.patch(f'/api/articles/{article_id}', json={'tags': ['sql', 'banco-de-dados']})

    page = page_of(client, article_id)

    assert page.index('<li class="chip">sql</li>') < page.index('<li class="chip">banco-de-dados</li>')


def test_a_draft_page_tells_its_author_and_has_no_likes(reader_client, reader_id):
    article_id = create_article(reader_id, status='draft')

    page = page_of(reader_client, article_id)

    assert 'Rascunho: só você vê este artigo até publicá-lo.' in page
    assert f'href="/write/{article_id}"' in page
    assert 'like-btn' not in page


PUBLISHED = datetime(2026, 3, 5, 10, 0)


def update_note(client, article_id: int, updated_at: datetime) -> str | None:
    """The opening tag of the update note of an article published at PUBLISHED (UTC)."""
    with db_cursor() as cursor:
        cursor.execute(
            'UPDATE ARTICLES SET publish_date = %s, updated_at = %s WHERE article_id = %s',
            (PUBLISHED, updated_at, article_id),
        )
    found = re.search(r'<span data-updated-after="[^"]+"[^>]*>', page_of(client, article_id))
    return found and found.group()


def test_edits_on_a_later_day_are_shown(client, admin_id):
    note = update_note(client, create_article(admin_id), datetime(2026, 3, 7, 10, 0))

    assert note is not None and 'hidden' not in note


def test_edits_on_the_day_of_publication_start_hidden(client, admin_id):
    # The browser shows them when the reader's zone puts the two on different days.
    note = update_note(client, create_article(admin_id), datetime(2026, 3, 5, 22, 30))

    assert note is not None and 'hidden' in note


def test_edits_before_publication_are_not_updates(client, admin_id):
    assert update_note(client, create_article(admin_id), datetime(2026, 3, 4, 10, 0)) is None
