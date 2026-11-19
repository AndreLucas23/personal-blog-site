"""Addresses of pages, built the same way by the pages and the API."""
import re

from flask import request, url_for

from slugs import slugify

# One slash, then printable ASCII without spaces: "//host" and "/\host" would take the
# browser to another site, and so could the spaces and controls browsers drop.
LOCAL_PATH = re.compile(r'/(?![/\\])[!-~]*')


def local_path(target: str | None) -> str | None:
    """The target when it is a path on this site, the only place a sign-in leads back to."""
    if target and LOCAL_PATH.fullmatch(target) and '\\' not in target:
        return target
    return None


def login_url() -> str:
    """The sign-in page, which leads back to the page being read."""
    here = request.full_path.rstrip('?')
    if request.method != 'GET' or request.blueprint == 'auth' or not local_path(here):
        return url_for('auth.login')
    return url_for('auth.login', next=here)


def article_url(article: dict) -> str:
    """The canonical address of an article, with the words of its current title."""
    return url_for(
        'views.article',
        article_id=article['article_id'],
        slug=slugify(article['article_title']),
    )
