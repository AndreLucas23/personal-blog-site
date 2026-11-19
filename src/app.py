import os

from flask import Flask, jsonify, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, current_user

import csrf
import errors
import security_headers
import template_helpers
from api import api_bp
from auth import auth_bp
from auth_user import AuthUser
from settings import env_flag, env_list
from views import views_bp

secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError('The SECRET_KEY environment variable must be set')


def configure_cors(flask_app: Flask, origins: list[str]) -> None:
    # Without origins there are no CORS headers, and browsers only let the
    # pages of this application call the API.
    if origins:
        CORS(flask_app, resources={r'/api/*': {'origins': origins}})


app = Flask(__name__)
configure_cors(app, env_list('CORS_ORIGINS'))
app.secret_key = secret_key
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Browsers send a Secure cookie only over HTTPS, so it stays off for plain HTTP.
app.config['SESSION_COOKIE_SECURE'] = env_flag('SESSION_COOKIE_SECURE')

login_manager = LoginManager(app, add_context_processor=False)
csrf.init_app(app)
errors.init_app(app)
security_headers.init_app(app)
template_helpers.init_app(app)

app.register_blueprint(views_bp)
app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)


@app.context_processor
def inject_current_user() -> dict:
    # Flask-Login's own processor loads the member for every template. The proxy loads
    # it only when a template reads it, so error pages can be drawn without the database.
    return {'current_user': current_user}


@login_manager.user_loader
def load_user(user_id: str) -> AuthUser | None:
    from repositories import user_repository
    user = user_repository.get_by_id(int(user_id))
    return AuthUser(user) if user else None


@login_manager.unauthorized_handler
def handle_unauthorized():
    login_url = url_for('auth.login')
    if errors.is_api_request():
        return jsonify({
            'message': 'Authentication required',
            'login_url': login_url,
        }), 401
    return redirect(login_url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=env_flag('FLASK_DEBUG'))
