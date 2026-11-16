import os

import mysql.connector
from flask import Flask, jsonify, redirect, request, session, url_for
from flask_cors import CORS
from flask_login import LoginManager

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

login_manager = LoginManager(app)

app.register_blueprint(views_bp)
app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)


@login_manager.user_loader
def load_user(user_id: str) -> AuthUser | None:
    from repositories import user_repository
    user = user_repository.get_by_id(int(user_id))
    return AuthUser(user) if user else None


def is_api_request() -> bool:
    return request.blueprint == 'api'


@login_manager.unauthorized_handler
def handle_unauthorized():
    login_url = url_for('auth.login')
    if is_api_request():
        return jsonify({
            'message': 'Authentication required',
            'login_url': login_url,
        }), 401
    return redirect(login_url)


@app.errorhandler(403)
def handle_forbidden(error):
    if is_api_request():
        return jsonify({'message': 'Admin privileges required'}), 403
    return error


@app.errorhandler(mysql.connector.Error)
def handle_db_error(error):
    # Use the session id: loading the user would query the failing database again.
    app.logger.error(
        'Database error on %s %s (user %s): [%s] %s',
        request.method, request.path, session.get('_user_id'), error.errno, error.msg,
    )
    return jsonify({
        'status': 'error',
        'message': 'An internal error occurred while accessing the database',
    }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=env_flag('FLASK_DEBUG'))
