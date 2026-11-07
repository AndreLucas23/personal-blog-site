from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from auth import admin_required, current_user_id
from repositories import article_repository, like_repository

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/articles', methods=['GET'])
def get_articles():
    all_articles = article_repository.get_all(current_user_id())
    return jsonify(all_articles)

@api_bp.route('/articles', methods=['POST'])
@admin_required
def add_article():
    data = request.get_json() or {}
    article_title = data.get('new-title')
    article_content = data.get('new-content')
    
    if not article_title or len(article_title) > 30:
        return jsonify({'message': 'Invalid title'}), 400

    if not article_content:
        return jsonify({'message': 'Invalid content'}), 400

    article_repository.create(article_title, article_content, current_user.user_id)
    return jsonify({'message': 'artigo criado com sucesso'}), 201

@api_bp.route('/articles/<int:article_id>', methods=['DELETE', 'PATCH'])
@admin_required
def article_by_id(article_id):
    if request.method == 'DELETE':
        return _delete_article(article_id)
    return _patch_article(article_id)

def _delete_article(article_id):
    deleted = article_repository.delete(article_id)
    if not deleted:
        # Technically in the original code we returned 200 anyway, but this is fine.
        pass
    return jsonify({'message': 'artigo removido com sucesso'}), 200

def _patch_article(article_id):
    data = request.get_json() or {}
    new_title = data.get('title')
    new_content = data.get('content')

    if new_title is None and new_content is None:
        return jsonify({'message': 'No fields to update'}), 400
        
    if new_title and len(new_title) > 30:
        return jsonify({'message': 'Invalid title'}), 400

    updated = article_repository.update(article_id, title=new_title, content=new_content)
    if not updated:
        return jsonify({'message': 'Article not found'}), 404

    return jsonify({'message': 'Article updated'}), 200

@api_bp.route('/articles/<int:article_id>/likes', methods=['POST', 'DELETE'])
@login_required
def article_likes(article_id):
    if article_repository.get_by_id(article_id) is None:
        return jsonify({'message': 'Article not found'}), 404

    is_like = request.method == 'POST'
    if is_like:
        like_repository.add(current_user.user_id, article_id)
    else:
        like_repository.remove(current_user.user_id, article_id)

    return jsonify({'liked': is_like, 'likes': like_repository.count(article_id)}), 200

@api_bp.route('/articles/id/<int:search_id>', methods=['GET'])
def search_by_id(search_id):
    search_articles = article_repository.search_by_id(search_id, current_user_id())
    return jsonify(search_articles), 200

@api_bp.route('/articles/title/<string:search_title>', methods=['GET'])
def search_by_title(search_title):
    search_articles = article_repository.search_by_title(
        search_title, current_user_id()
    )
    return jsonify(search_articles), 200
