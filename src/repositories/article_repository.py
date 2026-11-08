from db import db_cursor

# The first placeholder is the viewer id, used to tell whether they liked each article.
ARTICLE_DETAILS_QUERY = (
    'SELECT a.article_id, a.article_title, a.article_content, '
    'a.publish_date, u.username AS author, '
    '(SELECT COUNT(*) FROM LIKES l WHERE l.article_id = a.article_id) AS likes, '
    'EXISTS(SELECT 1 FROM LIKES l '
    'WHERE l.article_id = a.article_id AND l.user_id = %s) AS liked '
    'FROM ARTICLES a LEFT JOIN USERS u ON a.author_id = u.user_id'
)

def _with_like_flag(article: dict | None) -> dict | None:
    if article is not None:
        article['liked'] = bool(article['liked'])
    return article

def get_all(viewer_id: int | None = None) -> list[dict]:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(ARTICLE_DETAILS_QUERY, (viewer_id,))
        return [_with_like_flag(article) for article in cursor.fetchall()]

def get_by_id(article_id: int, viewer_id: int | None = None) -> dict | None:
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            ARTICLE_DETAILS_QUERY + ' WHERE a.article_id = %s',
            (viewer_id, article_id)
        )
        return _with_like_flag(cursor.fetchone())

def create(title: str, content: str, author_id: int) -> int:
    with db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO ARTICLES(ARTICLE_TITLE, ARTICLE_CONTENT, AUTHOR_ID) '
            'VALUES (%s, %s, %s)',
            (title, content, author_id)
        )
        return cursor.lastrowid

def delete(article_id: int) -> bool:
    with db_cursor() as cursor:
        cursor.execute('DELETE FROM ARTICLES WHERE ARTICLE_ID = %s', (article_id,))
        return cursor.rowcount > 0

def update(
    article_id: int, title: str | None = None, content: str | None = None
) -> bool:
    if title is None and content is None:
        return False

    fields = []
    values = []

    if title is not None:
        fields.append('ARTICLE_TITLE = %s')
        values.append(title)

    if content is not None:
        fields.append('ARTICLE_CONTENT = %s')
        values.append(content)

    values.append(article_id)

    with db_cursor() as cursor:
        cursor.execute(
            f'UPDATE ARTICLES SET {", ".join(fields)} WHERE ARTICLE_ID = %s',
            tuple(values)
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
