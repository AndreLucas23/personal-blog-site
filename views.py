from flask import Blueprint, render_template, abort
from db import get_db_connection

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def home():
    return render_template('home.html')

@views_bp.route('/open/<int:article_id>')
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
