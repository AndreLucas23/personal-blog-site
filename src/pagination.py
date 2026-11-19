"""Cursors for lists that go newest first, so each page continues where the last ended."""
import base64
import binascii
from datetime import datetime, timezone

PAGE_SIZE = 20
MAX_PAGE_SIZE = 50


def encode_cursor(published: datetime, article_id: int) -> str:
    """An opaque cursor for the position of an article. Dates come from MySQL in UTC."""
    seconds = int(published.replace(tzinfo=timezone.utc).timestamp())
    return base64.urlsafe_b64encode(f'{seconds}:{article_id}'.encode()).decode().rstrip('=')


def decode_cursor(cursor: str) -> tuple[datetime, int] | None:
    """The publication date in UTC and the id a cursor points after, or None for no cursor."""
    try:
        text = base64.urlsafe_b64decode(cursor + '=' * (-len(cursor) % 4)).decode()
        seconds, article_id = text.split(':')
        published = datetime.fromtimestamp(int(seconds), tz=timezone.utc).replace(tzinfo=None)
        return published, int(article_id)
    except (ValueError, binascii.Error, OverflowError, OSError):
        return None


def read_limit(value: str | None, default: int = PAGE_SIZE, maximum: int = MAX_PAGE_SIZE) -> int | None:
    """The number of items a request asks for, the default without one, or None when invalid."""
    if value is None:
        return default
    if not value.isdecimal() or not 1 <= int(value) <= maximum:
        return None
    return int(value)
