from flask import Blueprint, render_template, abort
from repositories import article_repository

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def home():
    return render_template('home.html')

@views_bp.route('/open/<int:article_id>')
def open_article(article_id):
    article = article_repository.get_by_id(article_id)

    if article is None:
        abort(404)

    return render_template('article.html', article=article), 200
