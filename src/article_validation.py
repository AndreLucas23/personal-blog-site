"""Rules for the articles members write."""
MAX_TITLE_LENGTH = 150
MAX_SUMMARY_LENGTH = 300
MAX_CONTENT_LENGTH = 50_000

TITLE_REQUIRED = 'title_required'
TITLE_TOO_LONG = 'title_too_long'
SUMMARY_TOO_LONG = 'summary_too_long'
CONTENT_REQUIRED = 'content_required'
CONTENT_TOO_LONG = 'content_too_long'
INVALID = 'invalid'

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


def validate(fields: dict[str, str], *, require_all: bool) -> dict[str, str]:
    """Check normalized fields and return the error code of each invalid one.

    With require_all, as when an article is created, a missing title or content is an error.
    """
    errors = {}

    if require_all or 'title' in fields:
        title = fields.get('title', '')
        if not title:
            errors['title'] = TITLE_REQUIRED
        elif len(title) > MAX_TITLE_LENGTH:
            errors['title'] = TITLE_TOO_LONG

    if len(fields.get('summary', '')) > MAX_SUMMARY_LENGTH:
        errors['summary'] = SUMMARY_TOO_LONG

    if require_all or 'content' in fields:
        content = fields.get('content', '')
        if not content.strip():
            errors['content'] = CONTENT_REQUIRED
        elif len(content) > MAX_CONTENT_LENGTH:
            errors['content'] = CONTENT_TOO_LONG

    return errors
