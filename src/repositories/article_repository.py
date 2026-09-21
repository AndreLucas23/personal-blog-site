from db import get_db_connection

def get_all():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT ARTICLE_ID as article_id, '
            'ARTICLE_TITLE as article_title, '
            'ARTICLE_CONTENT as article_content, '
            'PUBLISH_DATE as publish_date '
            'FROM ARTICLES'
        )
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_by_id(article_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT ARTICLE_ID as article_id, '
            'ARTICLE_TITLE as article_title, '
            'ARTICLE_CONTENT as article_content, '
            'PUBLISH_DATE as publish_date '
            'FROM ARTICLES WHERE ARTICLE_ID = %s',
            (article_id,)
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create(title, content):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO ARTICLES(ARTICLE_TITLE, ARTICLE_CONTENT) VALUES (%s, %s)',
            (title, content)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete(article_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ARTICLES WHERE ARTICLE_ID = %s', (article_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update(article_id, title=None, content=None):
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

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE ARTICLES SET {", ".join(fields)} WHERE ARTICLE_ID = %s',
            tuple(values)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def search_by_id(search_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT ARTICLE_ID as article_id, '
            'ARTICLE_TITLE as article_title, '
            'ARTICLE_CONTENT as article_content, '
            'PUBLISH_DATE as publish_date '
            'FROM ARTICLES WHERE ARTICLE_ID LIKE %s',
            (f'%{search_id}%',)
        )
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def search_by_title(search_title):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT ARTICLE_ID as article_id, '
            'ARTICLE_TITLE as article_title, '
            'ARTICLE_CONTENT as article_content, '
            'PUBLISH_DATE as publish_date '
            'FROM ARTICLES WHERE ARTICLE_TITLE LIKE %s',
            (f'%{search_title}%',)
        )
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
