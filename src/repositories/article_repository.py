from db import db_cursor
from repositories import tag_repository

# The first placeholder is the viewer id, used to tell whether they liked each article.
ARTICLE_DETAILS_QUERY = (
    'SELECT a.article_id, a.author_id, a.article_title, a.summary, a.cover_path, a.article_content, '
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
ONLY_PUBLISHED = " WHERE a.status = 'published'"
# Placeholder: the viewer id. Without a viewer the comparison is NULL, so only published.
VISIBLE_TO_VIEWER = " AND (a.status = 'published' OR a.author_id = %s)"

def get_all(viewer_id: int | None = None, author_username: str | None = None) -> list[dict]:
    query, params = ARTICLE_DETAILS_QUERY + ONLY_PUBLISHED, [viewer_id]
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
            ARTICLE_DETAILS_QUERY + ' WHERE a.article_id = %s' + VISIBLE_TO_VIEWER,
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
    tags: list[str] | None = None,
) -> int:
    with db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO ARTICLES '
            '(article_title, summary, article_content, author_id, status, publish_date) '
            "VALUES (%s, %s, %s, %s, %s, IF(%s = 'published', CURRENT_TIMESTAMP, NULL))",
            (title, summary, content, author_id, status, status)
        )
        article_id = cursor.lastrowid
        if tags:
            tag_repository.replace_article_tags(cursor, article_id, tags)
        return article_id

def delete(article_id: int) -> tuple[bool, str | None]:
    """Delete the article. Whether it existed, and its cover, so the file can be removed."""
    with db_cursor() as cursor:
        # The lock keeps a cover uploaded at the same moment from outliving the article.
        cursor.execute('SELECT cover_path FROM ARTICLES WHERE article_id = %s FOR UPDATE', (article_id,))
        row = cursor.fetchone()
        if row is None:
            return False, None
        cursor.execute('DELETE FROM ARTICLES WHERE article_id = %s', (article_id,))
        return True, row[0]

def set_cover(article_id: int, cover_path: str | None) -> tuple[bool, str | None]:
    """Store the new cover. Whether the article exists, and its previous cover."""
    with db_cursor() as cursor:
        # The lock keeps two uploads at once from losing track of a file.
        cursor.execute('SELECT cover_path FROM ARTICLES WHERE article_id = %s FOR UPDATE', (article_id,))
        row = cursor.fetchone()
        if row is None:
            return False, None
        cursor.execute(
            'UPDATE ARTICLES SET cover_path = %s WHERE article_id = %s', (cover_path, article_id)
        )
        return True, row[0]

def update(
    article_id: int,
    changes: dict[str, str | None],
    tags: list[str] | None = None,
) -> bool:
    """Change the fields named as in COLUMNS, the status and, unless None, the tags.

    Changing a field or the tags marks the article as edited. False for a missing article.
    """
    fields = [field for field in COLUMNS if field in changes]
    assignments = [f'{COLUMNS[field]} = %s' for field in fields]
    values = [changes[field] for field in fields]
    if fields or tags is not None:
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
        if cursor.rowcount == 0:
            return False
        if tags is not None:
            tag_repository.replace_article_tags(cursor, article_id, tags)
        return True

def search_by_id(search_id: int, viewer_id: int | None = None) -> list[dict]:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + ONLY_PUBLISHED + ' AND a.article_id LIKE %s',
            (viewer_id, f'%{search_id}%')
        )
        return [_with_like_flag(article) for article in cursor.fetchall()]

def search_by_title(search_title: str, viewer_id: int | None = None) -> list[dict]:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + ONLY_PUBLISHED + ' AND a.article_title LIKE %s',
            (viewer_id, f'%{search_title}%')
        )
        return [_with_like_flag(article) for article in cursor.fetchall()]
