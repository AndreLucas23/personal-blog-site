"""Readable words for addresses, made from titles."""
import re
import unicodedata

MAX_SLUG_LENGTH = 80


def slugify(text: str) -> str:
    """Lowercase ASCII words joined by hyphens, such as arquitetura-limpa-na-pratica."""
    # NFKD splits accented letters into the letter and the accent, which ASCII drops.
    ascii_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_text.lower()).strip('-')
    return slug[:MAX_SLUG_LENGTH].rstrip('-') or 'artigo'
