from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.exceptions import RequestEntityTooLarge

import article_validation
import markdown_render
import uploads
import user_validation as validation
from auth import current_user_id
from media import media_url
from links import article_url
from repositories import article_repository, like_repository, user_repository

api_bp = Blueprint('api', __name__, url_prefix='/api')

def _json_object() -> dict | None:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None

def _article_json(article: dict, *, with_content: bool = False) -> dict:
    """An article as the API shows it. Lists leave the content out, which can be long."""
    content = article['article_content']
    plain = markdown_render.plain_text(content)
    shown = {
        'article_id': article['article_id'],
        'url': article_url(article),
        'article_title': article['article_title'],
        'summary': article['summary'],
        'tags': article['tags'],
        'excerpt': article['summary'] or markdown_render.excerpt(plain),
        'reading_time': markdown_render.reading_minutes(plain),
        'status': article['status'],
        'publish_date': article['publish_date'],
        'created_at': article['created_at'],
        'updated_at': article['updated_at'],
        'author': article['author'],
        'author_username': article['author_username'],
        'author_avatar_url': media_url(article['author_avatar_path']),
        'likes': article['likes'],
        'liked': article['liked'],
    }
    if with_content:
        shown['article_content'] = content
    return shown

def _articles_json(articles: list[dict]):
    return jsonify([_article_json(article) for article in articles])

@api_bp.route('/articles', methods=['GET'])
def get_articles():
    author = request.args.get('author')
    if author is None:
        return _articles_json(article_repository.get_all(current_user_id()))

    username = validation.normalize_username(author)
    articles = article_repository.get_all(current_user_id(), author_username=username)
    # Only an empty list needs a second query to tell a quiet member from a missing one.
    if not articles and user_repository.get_by_username(username) is None:
        return jsonify({'message': 'User not found'}), 404
    return _articles_json(articles)

def _read_article_fields(data: dict) -> tuple[dict[str, str], dict[str, str]]:
    """The article fields of a request body, normalized, and the ones that are not text."""
    fields, errors = {}, {}
    for field in article_validation.ARTICLE_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if value is None and field in article_validation.OPTIONAL_FIELDS:
            value = ''
        if not isinstance(value, str):
            errors[field] = article_validation.INVALID
            continue
        fields[field] = article_validation.normalize(field, value)
    return fields, errors

def _read_status(data: dict) -> tuple[str | None, dict[str, str]]:
    """The status a request body asks for, if any, and an error when it is not one."""
    if 'status' not in data:
        return None, {}
    if data['status'] not in article_validation.STATUSES:
        return None, {'status': article_validation.INVALID}
    return data['status'], {}

def _read_tags(data: dict) -> tuple[list[str] | None, dict[str, str]]:
    """The normalized tags of a request body, if it has them, and their error."""
    if 'tags' not in data:
        return None, {}
    values = data['tags']
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        return None, {'tags': article_validation.INVALID}

    tags = article_validation.normalize_tags(values)
    error = article_validation.validate_tags(tags)
    return tags, ({'tags': error} if error else {})

def _stored(fields: dict[str, str]) -> dict[str, str | None]:
    return {
        field: (value or None) if field in article_validation.OPTIONAL_FIELDS else value
        for field, value in fields.items()
    }

def _invalid_article(errors: dict[str, str]):
    return jsonify({'message': 'Invalid article', 'errors': errors}), 400

def _article_not_found():
    return jsonify({'message': 'Article not found'}), 404

@api_bp.route('/articles', methods=['POST'])
@login_required
def create_article():
    data = _json_object()
    if data is None:
        return jsonify({'message': 'Invalid request body'}), 400

    fields, errors = _read_article_fields(data)
    status, status_errors = _read_status(data)
    tags, tag_errors = _read_tags(data)
    status = status or article_validation.PUBLISHED
    # A value that is not text says more than "required", so it wins.
    errors = article_validation.validate(
        fields,
        title_required=True,
        content_required=status == article_validation.PUBLISHED,
    ) | errors | status_errors | tag_errors
    if errors:
        return _invalid_article(errors)

    stored = _stored(fields)
    article_id = article_repository.create(
        stored['title'],
        stored.get('summary'),
        stored.get('content') or '',
        current_user.user_id,
        status,
        tags,
    )
    article = article_repository.get_by_id(article_id, current_user.user_id)
    # The author may delete it from another tab before this read.
    if article is None:
        return _article_not_found()
    return jsonify(_article_json(article, with_content=True)), 201

@api_bp.route('/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    article = article_repository.get_by_id(article_id, current_user_id())
    if article is None:
        return _article_not_found()
    return jsonify(_article_json(article, with_content=True))

@api_bp.route('/articles/<int:article_id>', methods=['PATCH'])
@login_required
def update_article(article_id):
    article = article_repository.get_by_id(article_id, current_user.user_id)
    if article is None:
        return _article_not_found()
    # Admins moderate by removing; changing someone's words is only for the author.
    if article['author_id'] != current_user.user_id:
        return jsonify({'message': 'Only the author can edit this article'}), 403

    data = _json_object()
    if data is None:
        return jsonify({'message': 'Invalid request body'}), 400

    fields, errors = _read_article_fields(data)
    status, status_errors = _read_status(data)
    tags, tag_errors = _read_tags(data)
    errors |= status_errors | tag_errors
    if not fields and not errors and status is None and tags is None:
        return jsonify({'message': 'No fields to update'}), 400

    errors = article_validation.validate(
        fields, title_required=False, content_required=False
    ) | errors
    # A published article needs content, whether it is published now or stays published.
    publishing = (status or article['status']) == article_validation.PUBLISHED
    if publishing and not fields.get('content', article['article_content']).strip():
        errors.setdefault('content', article_validation.CONTENT_REQUIRED)
    if errors:
        return _invalid_article(errors)

    # The editor sends every field on each save; only what differs is an edit.
    changes = {
        field: value for field, value in _stored(fields).items()
        if value != article[article_repository.COLUMNS[field]]
    }
    if status is not None and status != article['status']:
        changes['status'] = status
    if tags == article['tags']:
        tags = None
    # An admin may remove the article between the checks above and this save.
    if (changes or tags is not None) and not article_repository.update(article_id, changes, tags):
        return _article_not_found()
    article = article_repository.get_by_id(article_id, current_user.user_id)
    if article is None:
        return _article_not_found()
    return jsonify(_article_json(article, with_content=True))

@api_bp.route('/articles/<int:article_id>', methods=['DELETE'])
@login_required
def delete_article(article_id):
    # Drafts are private, so admins cannot reach the drafts of others either.
    article = article_repository.get_by_id(article_id, current_user.user_id)
    if article is None:
        return _article_not_found()
    if article['author_id'] != current_user.user_id and not current_user.is_admin:
        return jsonify({'message': 'Only the author or an admin can remove this article'}), 403

    article_repository.delete(article_id)
    return jsonify({'message': 'Article removed'}), 200

@api_bp.route('/previews', methods=['POST'])
@login_required
def preview_markdown():
    """The HTML a Markdown text becomes, so the editor shows what readers will see."""
    data = _json_object()
    if data is None or not isinstance(data.get('content'), str):
        return jsonify({'message': 'Invalid request body'}), 400
    if len(data['content']) > article_validation.MAX_CONTENT_LENGTH:
        return _invalid_article({'content': article_validation.CONTENT_TOO_LONG})
    return jsonify({'html': str(markdown_render.render(data['content']))})

@api_bp.route('/articles/<int:article_id>/likes', methods=['POST', 'DELETE'])
@login_required
def article_likes(article_id):
    article = article_repository.get_by_id(article_id, current_user.user_id)
    # Only published articles collect likes.
    if article is None or article['status'] != article_validation.PUBLISHED:
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
    for field in validation.PROFILE_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if value is None and field in validation.OPTIONAL_PROFILE_FIELDS:
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
        field: (value or None) if field in validation.OPTIONAL_PROFILE_FIELDS else value
        for field, value in changes.items()
    }
    try:
        user_repository.update_profile(current_user.user_id, stored)
    except user_repository.DuplicateUsernameError:
        return jsonify({'message': 'Username taken', 'errors': {'username': 'username_taken'}}), 409

    profile = user_repository.get_profile_by_id(current_user.user_id)
    return jsonify(_profile_json(profile, include_email=True))


@api_bp.route('/users/me/drafts', methods=['GET'])
@login_required
def get_own_drafts():
    return _articles_json(article_repository.get_drafts(current_user.user_id))


def _invalid_image(field: str, code: str, status: int = 400):
    return jsonify({'message': 'Invalid image', 'errors': {field: code}}), status

def _uploaded_image(field: str):
    """The file sent in a form field, and the answer to give when there is none to take."""
    try:
        image = request.files.get(field)
    except RequestEntityTooLarge:
        # Same code as a file over the image limit, so clients handle one case.
        return None, _invalid_image(field, uploads.IMAGE_TOO_LARGE, 413)
    if image is None:
        return None, _invalid_image(field, uploads.IMAGE_MISSING)
    return image, None

@api_bp.route('/users/me/avatar', methods=['PUT'])
@login_required
def upload_avatar():
    image, refused = _uploaded_image('avatar')
    if refused:
        return refused

    upload_dir = current_app.config['UPLOAD_DIR']
    try:
        file_name = uploads.save_avatar(image.stream, upload_dir)
    except uploads.ImageError as error:
        return _invalid_image('avatar', error.code)

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
