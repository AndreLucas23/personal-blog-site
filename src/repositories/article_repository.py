from db import db_cursor

# The first placeholder is the viewer id, used to tell whether they liked each article.
ARTICLE_DETAILS_QUERY = (
    'SELECT a.article_id, a.author_id, a.article_title, a.summary, a.article_content, '
    'a.publish_date, u.display_name AS author, u.username AS author_username, '
    'u.avatar_path AS author_avatar_path, '
    '(SELECT COUNT(*) FROM LIKES l WHERE l.article_id = a.article_id) AS likes, '
    'EXISTS(SELECT 1 FROM LIKES l '
    'WHERE l.article_id = a.article_id AND l.user_id = %s) AS liked '
    'FROM ARTICLES a LEFT JOIN USERS u ON a.author_id = u.user_id'
)

def _with_like_flag(article: dict | None) -> dict | None:
    if article is not None:
        article['liked'] = bool(article['liked'])
    return article

def get_all(viewer_id: int | None = None, author_username: str | None = None) -> list[dict]:
    query, params = ARTICLE_DETAILS_QUERY, [viewer_id]
    if author_username is not None:
        query += ' WHERE u.username = %s'
        params.append(author_username)

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, tuple(params))
        return [_with_like_flag(article) for article in cursor.fetchall()]

def get_by_id(article_id: int, viewer_id: int | None = None) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + ' WHERE a.article_id = %s',
            (viewer_id, article_id)
        )
        return _with_like_flag(cursor.fetchone())

# Columns of the fields an author writes, the only ones an update can change.
COLUMNS = {'title': 'article_title', 'summary': 'summary', 'content': 'article_content'}

def create(title: str, summary: str | None, content: str, author_id: int) -> int:
    with db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO ARTICLES (article_title, summary, article_content, author_id) '
            'VALUES (%s, %s, %s, %s)',
            (title, summary, content, author_id)
        )
        return cursor.lastrowid

def delete(article_id: int) -> bool:
    with db_cursor() as cursor:
        cursor.execute('DELETE FROM ARTICLES WHERE ARTICLE_ID = %s', (article_id,))
        return cursor.rowcount > 0

def update(article_id: int, changes: dict[str, str | None]) -> bool:
    """Change the given fields, named as in COLUMNS. Returns False for a missing article."""
    fields = [field for field in COLUMNS if field in changes]
    if not fields:
        return False

    assignments = ', '.join(f'{COLUMNS[field]} = %s' for field in fields)
    with db_cursor() as cursor:
        cursor.execute(
            f'UPDATE ARTICLES SET {assignments} WHERE article_id = %s',
            (*(changes[field] for field in fields), article_id)
        )
        return cursor.rowcount > 0

def search_by_id(search_id: int, viewer_id: int | None = None) -> list[dict]:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + ' WHERE a.article_id LIKE %s',
            (viewer_id, f'%{search_id}%')
        )
        return [_with_like_flag(article) for article in cursor.fetchall()]

def search_by_title(search_title: str, viewer_id: int | None = None) -> list[dict]:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + ' WHERE a.article_title LIKE %s',
            (viewer_id, f'%{search_title}%')
        )
        return [_with_like_flag(article) for article in cursor.fetchall()]
