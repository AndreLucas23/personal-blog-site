import pytest

from slugs import MAX_SLUG_LENGTH, slugify


@pytest.mark.parametrize(('title', 'slug'), [
    ('Arquitetura limpa na prática', 'arquitetura-limpa-na-pratica'),
    ('Ação & Reação: parte 2!', 'acao-reacao-parte-2'),
    ('  --Olá--  ', 'ola'),
    ('Ünïcödé çà', 'unicode-ca'),
    ('???', 'artigo'),
    ('日本語', 'artigo'),
])
def test_slugify(title, slug):
    assert slugify(title) == slug


def test_long_titles_are_cut_without_a_trailing_hyphen():
    slug = slugify('palavra ' * 30)

    assert len(slug) <= MAX_SLUG_LENGTH
    assert not slug.endswith('-')
