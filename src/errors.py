"""Error responses: JSON with a message under /api, a styled page everywhere else."""
import mysql.connector
from flask import Flask, Response, current_app, jsonify, make_response, render_template, request, session
from werkzeug.exceptions import HTTPException, InternalServerError

DATABASE_MESSAGE = 'An internal error occurred while accessing the database'

API_MESSAGES = {
    400: 'Bad request',
    403: 'Forbidden',
    404: 'Not found',
    405: 'Method not allowed',
    413: 'Request too large',
    429: 'Too many requests',
    500: 'Internal server error',
}

PAGE_MESSAGES = {
    400: ('Requisição inválida', 'Não foi possível entender o pedido. Volte e tente de novo.'),
    403: ('Acesso negado', 'Você não tem permissão para ver esta página.'),
    404: ('Página não encontrada', 'O endereço pode estar errado ou o conteúdo foi removido.'),
    405: ('Ação não permitida', 'Esta página não aceita essa ação.'),
    413: ('Arquivo grande demais', 'Envie um arquivo menor e tente de novo.'),
    429: ('Muitas tentativas', 'Aguarde um pouco antes de tentar de novo.'),
    500: ('Algo deu errado', 'Tivemos um problema do nosso lado. Tente de novo em instantes.'),
}


def is_api_request() -> bool:
    return request.blueprint == 'api' or request.path == '/api' or request.path.startswith('/api/')


def _custom_description(error: HTTPException) -> str | None:
    """The description passed to abort(), or None when Werkzeug's default text is used."""
    if error.description and error.description != type(error).description:
        return error.description
    return None


def _error_headers(error: HTTPException) -> list[tuple[str, str]]:
    # Headers such as Allow on a 405 must survive; the body and its type are ours.
    return [(name, value) for name, value in error.get_headers() if name.lower() != 'content-type']


def _render_page(status: int, message: str | None = None, *, with_account: bool = True) -> Response:
    title, default_message = PAGE_MESSAGES.get(status, PAGE_MESSAGES[500])
    try:
        page = render_template(
            'error.html',
            status=status,
            title=title,
            message=message or default_message,
            # The account menu loads the user from the database, which may be the failing part.
            skip_account=not with_account,
        )
    except Exception:
        current_app.logger.exception('Could not render the error page')
        return make_response(f'{status} {title}', status, {'Content-Type': 'text/plain; charset=utf-8'})
    return make_response(page, status)


def handle_http_error(error: HTTPException) -> Response:
    status = error.code or 500
    description = _custom_description(error)

    if is_api_request():
        message = description or API_MESSAGES.get(status, error.name)
        response = make_response(jsonify({'message': message}), status)
    else:
        response = _render_page(status, description)

    response.headers.extend(_error_headers(error))
    return response


def handle_internal_error(error: InternalServerError):
    # Flask already logged the original exception with its traceback.
    if is_api_request():
        return jsonify({'message': API_MESSAGES[500]}), 500
    return _render_page(500, with_account=False)


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
