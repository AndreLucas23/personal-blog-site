"""Files members uploaded, served from the uploads volume."""
from flask import Blueprint, Flask, abort, current_app, send_from_directory, url_for

import uploads

media_bp = Blueprint('media', __name__, url_prefix='/media')

# A removed photo must stop showing up: only browsers keep a file, for a day, and
# shared caches such as proxies never store it.
CACHE_SECONDS = 24 * 60 * 60


@media_bp.route('/<filename>')
def uploaded_file(filename: str):
    if not uploads.is_upload_name(filename):
        abort(404)

    # Every upload is WebP. The type is set here because the slim image has no
    # mime.types file, and nosniff would make browsers refuse a generic type.
    response = send_from_directory(
        current_app.config['UPLOAD_DIR'], filename, mimetype='image/webp', max_age=CACHE_SECONDS
    )
    response.cache_control.public = False
    response.cache_control.private = True
    return response


def media_url(file_name: str | None) -> str | None:
    return url_for('media.uploaded_file', filename=file_name) if file_name else None


def init_app(app: Flask) -> None:
    app.register_blueprint(media_bp)
    app.jinja_env.globals['media_url'] = media_url
