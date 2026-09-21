from flask import Blueprint, jsonify, request
from db import get_db_connection

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/articles', methods=['GET'])
def get_articles():
    all_articles = []
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
        all_articles = cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify(all_articles)

@api_bp.route('/articles', methods=['POST'])
def add_article():
    data = request.get_json() or {}
    article_title = data.get('new-title')
    article_content = data.get('new-content')
    
    if not article_title or len(article_title) > 30:
        return jsonify({'message': 'Invalid title'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO ARTICLES(ARTICLE_TITLE, ARTICLE_CONTENT) VALUES (%s, %s)',
            (article_title, article_content)
        )
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify({'message': 'artigo criado com sucesso'}), 201

@api_bp.route('/articles/<int:article_id>', methods=['DELETE', 'PATCH'])
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
        
    if new_title and len(new_title) > 30:
        return jsonify({'message': 'Invalid title'}), 400

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

@api_bp.route('/articles/id/<int:search_id>', methods=['GET'])
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
        search_articles = cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify(search_articles), 200

@api_bp.route('/articles/title/<string:search_title>', methods=['GET'])
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
        search_articles = cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify(search_articles), 200
