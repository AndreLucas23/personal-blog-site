import logging
import os

import mysql.connector
from flask import Flask, jsonify, redirect, request, url_for
from flask_cors import CORS
from flask_login import LoginManager

from api import api_bp
from auth import auth_bp
from auth_user import AuthUser
from views import views_bp

secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError('The SECRET_KEY environment variable must be set')

app = Flask(__name__)
CORS(app)
app.secret_key = secret_key
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

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
    if is_api_request():
        return jsonify({'message': 'Authentication required'}), 401
    return redirect(url_for('auth.login'))


@app.errorhandler(403)
def handle_forbidden(error):
    if is_api_request():
        return jsonify({'message': 'Admin privileges required'}), 403
    return error


@app.errorhandler(mysql.connector.Error)
def handle_db_error(error):
    logging.error(f'Erro do banco de dados: [{error.errno}] {error.msg}')
    return jsonify({
        'status': 'error',
        'message': 'Houve um erro interno ao processar os dados do banco',
        'debug_error': f'[{error.errno}] {error.msg}'
    }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
