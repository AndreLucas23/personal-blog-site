"""Addresses of pages, built the same way by the pages and the API."""
import re
from urllib.parse import quote

from flask import request, url_for

from slugs import slugify

# One slash, then printable ASCII without spaces or backslashes: "//host" and "/\host"
# would take the browser to another site, and so could the spaces and controls browsers drop.
LOCAL_PATH = re.compile(r'/(?!/)[!-\[\]-~]*')
# The API answers JSON and the sign-in pages lead nowhere new, so a sign-in never ends there.
NOT_PAGES = ('/api/', '/auth/')
# What a path keeps as it is; the rest is percent-encoded, as browsers send it.
PATH_CHARACTERS = "/:@!$&'()*+,;=~"


def local_path(target: str | None) -> str | None:
    """The target when it is a page of this site, the only place a sign-in leads back to."""
    if target and LOCAL_PATH.fullmatch(target) and not target.startswith(NOT_PAGES):
        return target
    return None


def current_page() -> str | None:
    """The page being read, as the browser asked for it, when a sign-in may lead back to it."""
    if request.method != 'GET' or request.blueprint == 'auth':
        return None
    # request.path comes decoded, where an encoded "?" would read as the start of the query.
    page = quote(request.path, safe=PATH_CHARACTERS)
    if request.query_string:
        page += '?' + request.query_string.decode('latin-1')
    return local_path(page)


def login_url() -> str:
    """The sign-in page, which leads back to the page being read."""
    # url_for leaves out a next that is None.
    return url_for('auth.login', next=current_page())


def article_url(article: dict) -> str:
    """The canonical address of an article, with the words of its current title."""
    return url_for(
        'views.article',
        article_id=article['article_id'],
        slug=slugify(article['article_title']),
    )
