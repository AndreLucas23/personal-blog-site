"""CSRF protection: a token kept in the session that every state-changing request sends back."""
import hmac
import secrets

from flask import Flask, abort, current_app, jsonify, request, session

from errors import is_api_request

SESSION_KEY = '_csrf_token'
FORM_FIELD = 'csrf_token'
HEADER = 'X-CSRF-Token'
SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS', 'TRACE'})

API_MESSAGE = 'Invalid or missing CSRF token'
PAGE_MESSAGE = 'A página expirou. Volte, recarregue a página e tente novamente.'


def csrf_token() -> str:
    if SESSION_KEY not in session:
        session[SESSION_KEY] = secrets.token_urlsafe(32)
    return session[SESSION_KEY]


def _is_valid_token() -> bool:
    expected = session.get(SESSION_KEY)
    sent = request.headers.get(HEADER) or request.form.get(FORM_FIELD)
    if not expected or not sent:
        return False
    return hmac.compare_digest(expected.encode(), sent.encode())


def _protect():
    if not current_app.config['CSRF_ENABLED'] or request.method in SAFE_METHODS:
        return None

    # No view runs for a request that matched no route, so its 404 or 405 comes first.
    if request.routing_exception is not None:
        return None

    if _is_valid_token():
        return None

    if is_api_request():
        return jsonify({'message': API_MESSAGE}), 400
    abort(400, description=PAGE_MESSAGE)


def init_app(app: Flask) -> None:
    app.config.setdefault('CSRF_ENABLED', True)
    app.before_request(_protect)
    app.jinja_env.globals['csrf_token'] = csrf_token
