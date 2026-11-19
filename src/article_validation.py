"""Rules for the articles members write."""
import re
import unicodedata

MAX_TITLE_LENGTH = 150
MAX_SUMMARY_LENGTH = 300
MAX_CONTENT_LENGTH = 50_000
MAX_TAGS = 5
MIN_TAG_LENGTH = 2
MAX_TAG_LENGTH = 30

TITLE_REQUIRED = 'title_required'
TITLE_TOO_LONG = 'title_too_long'
SUMMARY_TOO_LONG = 'summary_too_long'
CONTENT_REQUIRED = 'content_required'
CONTENT_TOO_LONG = 'content_too_long'
TAGS_TOO_MANY = 'tags_too_many'
TAG_TOO_SHORT = 'tag_too_short'
TAG_TOO_LONG = 'tag_too_long'
INVALID = 'invalid'

DRAFT = 'draft'
PUBLISHED = 'published'
STATUSES = (DRAFT, PUBLISHED)

# The fields members write, in the order of the editor. Optional ones are stored as
# NULL when left empty.
ARTICLE_FIELDS = ('title', 'summary', 'content')
OPTIONAL_FIELDS = ('summary',)


def normalize(field: str, value: str) -> str:
    if field == 'content':
        # Browsers send line breaks as \r\n. Leading spaces stay: they mark code in Markdown.
        return value.replace('\r\n', '\n').strip('\n').rstrip()
    # Titles and summaries are a single line.
    return ' '.join(value.split())


def normalize_tag(value: str) -> str:
    """Lowercase words joined by hyphens, such as banco-de-dados. Accents stay."""
    tag = unicodedata.normalize('NFC', value).lower().strip().lstrip('#')
    tag = re.sub(r'[\s_]+', '-', tag)
    kept = []
    for char in tag:
        kind = unicodedata.category(char)[0]
        # Scripts such as Hindi spell words with marks, which belong to the letter before them.
        if char == '-' or kind in 'LN' or (kind == 'M' and kept and kept[-1] != '-'):
            kept.append(char)
    return re.sub(r'-{2,}', '-', ''.join(kept)).strip('-')


def normalize_tags(values: list[str]) -> list[str]:
    """Normalized tags in the order given, without blanks or repeats."""
    tags = []
    for value in values:
        tag = normalize_tag(value)
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def validate_tags(tags: list[str]) -> str | None:
    if len(tags) > MAX_TAGS:
        return TAGS_TOO_MANY
    for tag in tags:
        if len(tag) < MIN_TAG_LENGTH:
            return TAG_TOO_SHORT
        if len(tag) > MAX_TAG_LENGTH:
            return TAG_TOO_LONG
    return None


def validate(fields: dict[str, str], *, title_required: bool, content_required: bool) -> dict[str, str]:
    """Check normalized fields and return the error code of each invalid one.

    A title that is sent cannot be empty. The content is required only to publish,
    so a draft can start with just its title.
    """
    errors = {}

    title = fields.get('title')
    if title is not None or title_required:
        if not title:
            errors['title'] = TITLE_REQUIRED
        elif len(title) > MAX_TITLE_LENGTH:
            errors['title'] = TITLE_TOO_LONG

    if len(fields.get('summary', '')) > MAX_SUMMARY_LENGTH:
        errors['summary'] = SUMMARY_TOO_LONG

    content = fields.get('content', '')
    if len(content) > MAX_CONTENT_LENGTH:
        errors['content'] = CONTENT_TOO_LONG
    elif content_required and not content.strip():
        errors['content'] = CONTENT_REQUIRED

    return errors
