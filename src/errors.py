"""Error responses: JSON with a message under /api, a styled page everywhere else."""
from typing import NoReturn

import mysql.connector
from flask import Flask, Response, current_app, jsonify, make_response, render_template, request, session
from werkzeug.exceptions import HTTPException, InternalServerError, default_exceptions

DATABASE_MESSAGE = 'An internal error occurred while accessing the database'

API_MESSAGES = {
    400: 'Bad request',
    403: 'Forbidden',
    404: 'Not found',
    405: 'Method not allowed',
    500: 'Internal server error',
}

PAGE_MESSAGES = {
    400: ('Requisição inválida', 'Não foi possível entender o pedido. Volte e tente de novo.'),
    403: ('Acesso negado', 'Você não tem permissão para ver esta página.'),
    404: ('Página não encontrada', 'O endereço pode estar errado ou o conteúdo foi removido.'),
    405: ('Ação não permitida', 'Esta página não aceita essa ação.'),
    500: ('Algo deu errado', 'Tivemos um problema do nosso lado. Tente de novo em instantes.'),
}


def is_api_request() -> bool:
    return request.blueprint == 'api' or request.path == '/api' or request.path.startswith('/api/')


def abort_with_message(status: int, message: str) -> NoReturn:
    """Abort with a message chosen by the application, which the error response shows."""
    error = default_exceptions[status](description=message)
    # Descriptions from Werkzeug or other libraries can carry internal details, so
    # only messages marked here reach the client.
    error.public_message = message
    raise error


def _public_message(error: HTTPException) -> str | None:
    return getattr(error, 'public_message', None)


def _error_headers(error: HTTPException) -> list[tuple[str, str]]:
    # Headers such as Allow on a 405 must survive; the body and its type are ours.
    return [(name, value) for name, value in error.get_headers() if name.lower() != 'content-type']


def _render_page(status: int, message: str | None = None, *, with_account: bool = True) -> Response:
    # Other client errors read as an invalid request, other server errors as a failure.
    title, default_message = PAGE_MESSAGES.get(status) or PAGE_MESSAGES[400 if status < 500 else 500]
    context = {'status': status, 'title': title, 'message': message or default_message}

    # The account menu loads the member from the database, which may be the failing part,
    # so a page that cannot be drawn with it is drawn again without it.
    for skip_account in ((False, True) if with_account else (True,)):
        try:
            return make_response(render_template('error.html', skip_account=skip_account, **context), status)
        except Exception:
            current_app.logger.exception('Could not render the error page')

    return make_response(f'{status} {title}', status, {'Content-Type': 'text/plain; charset=utf-8'})


def handle_http_error(error: HTTPException) -> Response:
    status = error.code or 500
    message = _public_message(error)

    if is_api_request():
        response = make_response(jsonify({'message': message or API_MESSAGES.get(status, error.name)}), status)
    else:
        response = _render_page(status, message)

    response.headers.extend(_error_headers(error))
    return response


def handle_internal_error(error: InternalServerError):
    # Flask already logged the original exception with its traceback.
    if is_api_request():
        return jsonify({'message': API_MESSAGES[500]}), 500
    return _render_page(500)


def handle_database_error(error: mysql.connector.Error):
    # Use the session id: loading the user would query the failing database again.
    current_app.logger.error(
        'Database error on %s %s (user %s): [%s] %s',
        request.method, request.path, session.get('_user_id'), error.errno, error.msg,
    )
    if is_api_request():
        return jsonify({'status': 'error', 'message': DATABASE_MESSAGE}), 500
    return _render_page(500, with_account=False)


def init_app(app: Flask) -> None:
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(InternalServerError, handle_internal_error)
    app.register_error_handler(mysql.connector.Error, handle_database_error)
