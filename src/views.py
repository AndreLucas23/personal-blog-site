from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

import uploads
import user_validation as validation
from auth import admin_required, current_user_id
from repositories import article_repository, user_repository

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def home():
    return render_template('home.html')

@views_bp.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

@views_bp.route('/open/<int:article_id>')
def open_article(article_id):
    article = article_repository.get_by_id(article_id, current_user_id())

    if article is None:
        abort(404)

    return render_template('article.html', article=article), 200

@views_bp.route('/@<username>')
def profile(username):
    canonical = validation.normalize_username(username)
    member = user_repository.get_profile(canonical)
    if member is None:
        abort(404)

    # One address per profile, whatever the letter case someone typed.
    if username != canonical:
        return redirect(url_for('views.profile', username=canonical), 301)

    is_own = current_user.is_authenticated and current_user.user_id == member['user_id']
    return render_template('profile.html', member=member, is_own=is_own)


@views_bp.route('/settings/profile')
@login_required
def profile_settings():
    member = user_repository.get_profile_by_id(current_user.user_id)
    return render_template(
        'settings_profile.html',
        member=member,
        max_image_bytes=uploads.MAX_IMAGE_BYTES,
        max_image_mb=uploads.MAX_IMAGE_BYTES // (1024 * 1024),
    )
