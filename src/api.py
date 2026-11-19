from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

import uploads
import user_validation as validation
from auth import admin_required, current_user_id
from media import media_url
from repositories import article_repository, like_repository, user_repository

api_bp = Blueprint('api', __name__, url_prefix='/api')

MAX_TITLE_LENGTH = 30

def _json_object() -> dict | None:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None

def _is_valid_title(title) -> bool:
    if not isinstance(title, str):
        return False
    return bool(title.strip()) and len(title) <= MAX_TITLE_LENGTH

def _is_valid_content(content) -> bool:
    return isinstance(content, str) and bool(content.strip())

def _article_json(article: dict) -> dict:
    """An article as the API shows it, with a URL for the author's avatar."""
    shown = dict(article)
    shown['author_avatar_url'] = media_url(shown.pop('author_avatar_path'))
    return shown

def _articles_json(articles: list[dict]):
    return jsonify([_article_json(article) for article in articles])

@api_bp.route('/articles', methods=['GET'])
def get_articles():
    author = request.args.get('author')
    if author is None:
        return _articles_json(article_repository.get_all(current_user_id()))

    username = validation.normalize_username(author)
    if user_repository.get_by_username(username) is None:
        return jsonify({'message': 'User not found'}), 404
    return _articles_json(article_repository.get_all(current_user_id(), author_username=username))

@api_bp.route('/articles', methods=['POST'])
@admin_required
def add_article():
    data = _json_object()
    if data is None:
        return jsonify({'message': 'Invalid request body'}), 400

    article_title = data.get('new-title')
    article_content = data.get('new-content')

    if not _is_valid_title(article_title):
        return jsonify({'message': 'Invalid title'}), 400

    if not _is_valid_content(article_content):
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
    if not article_repository.delete(article_id):
        return jsonify({'message': 'Article not found'}), 404

    return jsonify({'message': 'artigo removido com sucesso'}), 200

def _patch_article(article_id):
    data = _json_object()
    if data is None:
        return jsonify({'message': 'Invalid request body'}), 400

    new_title = data.get('title')
    new_content = data.get('content')

    if new_title is None and new_content is None:
        return jsonify({'message': 'No fields to update'}), 400

    if new_title is not None and not _is_valid_title(new_title):
        return jsonify({'message': 'Invalid title'}), 400

    if new_content is not None and not _is_valid_content(new_content):
        return jsonify({'message': 'Invalid content'}), 400

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
    return _articles_json(search_articles), 200

@api_bp.route('/articles/title/<string:search_title>', methods=['GET'])
def search_by_title(search_title):
    search_articles = article_repository.search_by_title(
        search_title, current_user_id()
    )
    return _articles_json(search_articles), 200


# Optional profile fields are stored as NULL when a member leaves them empty.
OPTIONAL_PROFILE_FIELDS = ('headline', 'bio', 'location', 'website')


def _normalize_profile_field(field: str, value: str) -> str:
    if field == 'username':
        return validation.normalize_username(value)
    if field == 'website':
        return validation.normalize_website(value)
    if field == 'bio':
        return value.replace('\r\n', '\n').strip()
    return value.strip()


def _profile_json(user: dict, *, include_email: bool = False) -> dict:
    profile = {
        'username': user['username'],
        'display_name': user['display_name'],
        'headline': user['headline'],
        'bio': user['bio'],
        'location': user['location'],
        'website': user['website'],
        'avatar_url': media_url(user['avatar_path']),
        'joined_at': user['created_at'],
        'articles': user['article_count'],
    }
    if include_email:
        profile['email'] = user['email']
    return profile


@api_bp.route('/users/me', methods=['GET'])
@login_required
def get_own_profile():
    profile = user_repository.get_profile_by_id(current_user.user_id)
    return jsonify(_profile_json(profile, include_email=True))


@api_bp.route('/users/me', methods=['PATCH'])
@login_required
def update_own_profile():
    data = _json_object()
    if data is None:
        return jsonify({'message': 'Invalid request body'}), 400

    changes = {}
    for field in user_repository.PROFILE_COLUMNS:
        if field not in data:
            continue
        value = data[field]
        if value is None and field in OPTIONAL_PROFILE_FIELDS:
            value = ''
        if not isinstance(value, str):
            return jsonify({'message': 'Invalid profile', 'errors': {field: 'invalid'}}), 400
        changes[field] = _normalize_profile_field(field, value)

    if not changes:
        return jsonify({'message': 'No fields to update'}), 400

    errors = validation.validate_profile(changes)
    if errors:
        return jsonify({'message': 'Invalid profile', 'errors': errors}), 400

    stored = {
        field: (value or None) if field in OPTIONAL_PROFILE_FIELDS else value
        for field, value in changes.items()
    }
    try:
        user_repository.update_profile(current_user.user_id, stored)
    except user_repository.DuplicateUsernameError:
        return jsonify({'message': 'Username taken', 'errors': {'username': 'username_taken'}}), 409

    profile = user_repository.get_profile_by_id(current_user.user_id)
    return jsonify(_profile_json(profile, include_email=True))


@api_bp.route('/users/me/avatar', methods=['PUT'])
@login_required
def upload_avatar():
    image = request.files.get('avatar')
    if image is None:
        return jsonify({'message': 'Invalid image', 'errors': {'avatar': uploads.IMAGE_MISSING}}), 400

    upload_dir = current_app.config['UPLOAD_DIR']
    try:
        file_name = uploads.save_avatar(image.stream, upload_dir)
    except uploads.ImageError as error:
        return jsonify({'message': 'Invalid image', 'errors': {'avatar': error.code}}), 400

    try:
        previous = user_repository.set_avatar(current_user.user_id, file_name)
    except Exception:
        # Without the row nothing points at the new file, so it must not stay behind.
        uploads.delete_upload(file_name, upload_dir)
        raise
    uploads.delete_upload(previous, upload_dir)
    return jsonify({'avatar_url': media_url(file_name)})


@api_bp.route('/users/me/avatar', methods=['DELETE'])
@login_required
def remove_avatar():
    previous = user_repository.set_avatar(current_user.user_id, None)
    uploads.delete_upload(previous, current_app.config['UPLOAD_DIR'])
    return jsonify({'avatar_url': None})


@api_bp.route('/users/<string:username>', methods=['GET'])
def get_profile(username):
    profile = user_repository.get_profile(validation.normalize_username(username))
    if profile is None:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(_profile_json(profile))
