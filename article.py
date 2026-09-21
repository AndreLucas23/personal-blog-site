from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    abort,
)

from db import get_db_connection

article_bp = Blueprint('article', __name__)

@article_bp.route('/open/<int:article_id>')
def open_article(article_id):
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
        article = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    if article is None:
        abort(404)

    return render_template('article.html', article=article), 200

@article_bp.route('/articles/<int:article_id>', methods=['DELETE', 'PATCH'])
def article_by_id(article_id):
    if request.method == 'DELETE':
        return _delete_article(article_id)
    return _patch_article(article_id)

def _delete_article(article_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ARTICLES WHERE ARTICLE_ID = %s', (article_id,))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify({'message': 'artigo removido com sucesso'}), 200

def _patch_article(article_id):
    data = request.get_json() or {}
    new_title = data.get('title')
    new_content = data.get('content')

    if new_title is None and new_content is None:
        return jsonify({'message': 'No fields to update'}), 400

    fields = []
    values = []

    if new_title is not None:
        fields.append('ARTICLE_TITLE = %s')
        values.append(new_title)

    if new_content is not None:
        fields.append('ARTICLE_CONTENT = %s')
        values.append(new_content)

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

        if cursor.rowcount == 0:
            return jsonify({'message': 'Article not found'}), 404
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify({'message': 'Article updated'}), 200
