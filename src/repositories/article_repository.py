from db import db_cursor

# The first placeholder is the viewer id, used to tell whether they liked each article.
ARTICLE_DETAILS_QUERY = (
    'SELECT a.article_id, a.author_id, a.article_title, a.summary, a.article_content, '
    'a.status, a.publish_date, a.created_at, a.updated_at, '
    'u.display_name AS author, u.username AS author_username, '
    'u.avatar_path AS author_avatar_path, '
    "(SELECT GROUP_CONCAT(t.name ORDER BY article_tags.position SEPARATOR ',') "
    'FROM ARTICLE_TAGS article_tags JOIN TAGS t ON t.tag_id = article_tags.tag_id '
    'WHERE article_tags.article_id = a.article_id) AS tag_names, '
    '(SELECT COUNT(*) FROM LIKES l WHERE l.article_id = a.article_id) AS likes, '
    'EXISTS(SELECT 1 FROM LIKES l '
    'WHERE l.article_id = a.article_id AND l.user_id = %s) AS liked '
    'FROM ARTICLES a LEFT JOIN USERS u ON a.author_id = u.user_id'
)

def _with_like_flag(article: dict | None) -> dict | None:
    if article is not None:
        article['liked'] = bool(article['liked'])
        # Tags are normalized, so they never hold the comma that joins them.
        names = article.pop('tag_names')
        article['tags'] = names.split(',') if names else []
    return article

# Lists show published articles only; a draft is reached by its author alone.
PUBLISHED = " WHERE a.status = 'published'"
# Placeholder: the viewer id. Without a viewer the comparison is NULL, so only published.
VISIBLE = " AND (a.status = 'published' OR a.author_id = %s)"

def get_all(viewer_id: int | None = None, author_username: str | None = None) -> list[dict]:
    query, params = ARTICLE_DETAILS_QUERY + PUBLISHED, [viewer_id]
    if author_username is not None:
        query += ' AND u.username = %s'
        params.append(author_username)

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, tuple(params))
        return [_with_like_flag(article) for article in cursor.fetchall()]

def get_by_id(article_id: int, viewer_id: int | None = None) -> dict | None:
    """The article, if it is published or the viewer wrote it."""
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + ' WHERE a.article_id = %s' + VISIBLE,
            (viewer_id, article_id, viewer_id)
        )
        return _with_like_flag(cursor.fetchone())

def get_drafts(author_id: int) -> list[dict]:
    """The author's drafts, the most recently edited first."""
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY
            + " WHERE a.author_id = %s AND a.status = 'draft'"
            + ' ORDER BY COALESCE(a.updated_at, a.created_at) DESC, a.article_id DESC',
            (author_id, author_id)
        )
        return [_with_like_flag(article) for article in cursor.fetchall()]

# Columns of the fields an author writes, the only ones an update can change.
COLUMNS = {'title': 'article_title', 'summary': 'summary', 'content': 'article_content'}

def create(
    title: str,
    summary: str | None,
    content: str,
    author_id: int,
    status: str = 'published',
) -> int:
    with db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO ARTICLES '
            '(article_title, summary, article_content, author_id, status, publish_date) '
            "VALUES (%s, %s, %s, %s, %s, IF(%s = 'published', CURRENT_TIMESTAMP, NULL))",
            (title, summary, content, author_id, status, status)
        )
        return cursor.lastrowid

def delete(article_id: int) -> bool:
    with db_cursor() as cursor:
        cursor.execute('DELETE FROM ARTICLES WHERE ARTICLE_ID = %s', (article_id,))
        return cursor.rowcount > 0

def update(article_id: int, changes: dict[str, str | None], edited: bool = False) -> bool:
    """Change the fields named as in COLUMNS and the status. False for a missing article.

    Changing a field marks the article as edited, and so does edited, for changes
    such as tags that live in other tables.
    """
    fields = [field for field in COLUMNS if field in changes]
    assignments = [f'{COLUMNS[field]} = %s' for field in fields]
    values = [changes[field] for field in fields]
    if fields or edited:
        assignments.append('updated_at = CURRENT_TIMESTAMP')

    if 'status' in changes:
        # The first publication sets the date; publishing again later keeps it.
        assignments.append('status = %s')
        assignments.append(
            "publish_date = COALESCE(publish_date, IF(%s = 'published', CURRENT_TIMESTAMP, NULL))"
        )
        values += [changes['status'], changes['status']]

    if not assignments:
        return False

    with db_cursor() as cursor:
        cursor.execute(
            f'UPDATE ARTICLES SET {", ".join(assignments)} WHERE article_id = %s',
            (*values, article_id)
        )
        return cursor.rowcount > 0

def search_by_id(search_id: int, viewer_id: int | None = None) -> list[dict]:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + PUBLISHED + ' AND a.article_id LIKE %s',
            (viewer_id, f'%{search_id}%')
        )
        return [_with_like_flag(article) for article in cursor.fetchall()]

def search_by_title(search_title: str, viewer_id: int | None = None) -> list[dict]:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + PUBLISHED + ' AND a.article_title LIKE %s',
            (viewer_id, f'%{search_title}%')
        )
        return [_with_like_flag(article) for article in cursor.fetchall()]
