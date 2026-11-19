"""Addresses of pages, built the same way by the pages and the API."""
from flask import url_for

from slugs import slugify


def article_url(article: dict) -> str:
    """The canonical address of an article, with the words of its current title."""
    return url_for(
        'views.article',
        article_id=article['article_id'],
        slug=slugify(article['article_title']),
    )
