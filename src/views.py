from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

import article_validation
import markdown_render
import uploads
import user_validation as validation
from auth import admin_required, current_user_id
from links import article_url
from repositories import article_repository, user_repository

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def home():
    return render_template('home.html')

@views_bp.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

@views_bp.route('/articles/<int:article_id>')
@views_bp.route('/articles/<int:article_id>/<slug>')
def article(article_id, slug=None):
    found = article_repository.get_by_id(article_id, current_user_id())
    if found is None:
        abort(404)

    # The id finds the article; the words follow its current title, so links shared
    # before a new title, or without the words, still arrive.
    canonical = article_url(found)
    if url_for('views.article', article_id=article_id, slug=slug) != canonical:
        return redirect(canonical, 301)

    content_html, plain = markdown_render.render_with_plain_text(found['article_content'])
    published, updated = found['publish_date'], found['updated_at']
    updated_after = bool(published and updated and updated > published)
    return render_template(
        'article.html',
        article=found,
        updated_after=updated_after,
        # Edits on the day of publication are part of publishing; later ones are news.
        # The day here is UTC's, and the browser decides again in the reader's zone.
        updated_later=updated_after and updated.date() > published.date(),
        canonical_url=canonical,
        description=found['summary'] or markdown_render.excerpt(plain),
        content_html=content_html,
        reading_minutes=markdown_render.reading_minutes(plain),
    )

def _editor(article: dict | None):
    return render_template(
        'editor.html',
        article=article,
        back_url=article_url(article) if article else url_for('views.home'),
        max_title=article_validation.MAX_TITLE_LENGTH,
        max_summary=article_validation.MAX_SUMMARY_LENGTH,
        max_content=article_validation.MAX_CONTENT_LENGTH,
        max_tags=article_validation.MAX_TAGS,
        min_tag_length=article_validation.MIN_TAG_LENGTH,
        max_tag_length=article_validation.MAX_TAG_LENGTH,
    )

@views_bp.route('/write')
@login_required
def write():
    return _editor(None)

# Not /articles/<id>/edit, which would clash with an article whose words are "edit".
@views_bp.route('/write/<int:article_id>')
@login_required
def edit_article(article_id):
    found = article_repository.get_by_id(article_id, current_user.user_id)
    if found is None:
        abort(404)
    if found['author_id'] != current_user.user_id:
        abort(403)
    return _editor(found)

@views_bp.route('/open/<int:article_id>')
def open_article(article_id):
    """The address articles had before they got readable ones."""
    found = article_repository.get_by_id(article_id, current_user_id())
    if found is None:
        abort(404)
    return redirect(article_url(found), 301)

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
