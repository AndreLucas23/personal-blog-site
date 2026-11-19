import pytest

import markdown_render


def html(text: str) -> str:
    return str(markdown_render.render(text))


def test_common_formatting_is_rendered():
    page = html('**negrito**, _itálico_ e ~~riscado~~\n\n- um\n- dois\n\n> citação\n\n`código`')

    assert '<strong>negrito</strong>' in page
    assert '<em>itálico</em>' in page
    assert '<s>riscado</s>' in page
    assert '<li>um</li>' in page
    assert '<blockquote>' in page
    assert '<code>código</code>' in page


def test_tables_and_code_blocks_are_rendered():
    page = html('| a | b |\n| - | - |\n| 1 | 2 |\n\n```python\nprint(1)\n```')

    assert '<table>' in page and '<td>1</td>' in page
    assert '<pre><code class="language-python">print(1)' in page


def test_raw_html_is_shown_as_text():
    page = html('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>')

    assert '<script>' not in page
    assert '<img' not in page
    assert '&lt;script&gt;' in page


@pytest.mark.parametrize('target', [
    'javascript:alert(1)', 'JAVASCRIPT:alert(1)', 'vbscript:msgbox(1)', 'data:text/html,<b>x</b>',
])
def test_dangerous_link_targets_are_not_links(target):
    assert 'href' not in html(f'[clique]({target})')


def test_links_are_marked_as_user_content():
    page = html('[site](https://example.com)')

    assert '<a href="https://example.com" rel="nofollow ugc noopener noreferrer">site</a>' in page


def test_remote_images_are_not_loaded():
    assert '<img' not in html('![rastreador](https://evil.example/pixel.png)')


def test_headings_start_below_the_page_title():
    page = html('# Um\n\n## Dois\n\n###### Seis')

    assert '<h2>Um</h2>' in page
    assert '<h3>Dois</h3>' in page
    assert '<h6>Seis</h6>' in page
    assert '<h1>' not in page


def test_plain_text_drops_the_formatting():
    text = '# Título\n\nUm **texto** com [link](https://a.dev) e `código`.\n\n- item'

    assert markdown_render.plain_text(text) == 'Título Um texto com link e código. item'
    assert markdown_render.plain_text('linha um\nlinha dois') == 'linha um linha dois'


def test_excerpt_cuts_at_a_word():
    text = 'palavra ' * 100

    excerpt = markdown_render.excerpt(text, length=30)

    assert excerpt == 'palavra palavra palavra…'
    assert markdown_render.excerpt('curto') == 'curto'


@pytest.mark.parametrize(('words', 'minutes'), [(10, 1), (200, 1), (400, 2), (1000, 5)])
def test_reading_minutes(words, minutes):
    assert markdown_render.reading_minutes('palavra ' * words) == minutes


def test_preview_needs_a_session(client):
    assert client.post('/api/previews', json={'content': 'x'}).status_code == 401


def test_preview_renders_the_markdown(reader_client):
    response = reader_client.post('/api/previews', json={'content': '# Oi\n\n<b>x</b>'})

    assert response.status_code == 200
    assert response.get_json() == {'html': '<h2>Oi</h2>\n<p>&lt;b&gt;x&lt;/b&gt;</p>\n'}


def test_preview_rejects_a_body_without_text(reader_client):
    assert reader_client.post('/api/previews', json={'content': 3}).status_code == 400
    assert reader_client.post('/api/previews', json=['x']).status_code == 400
