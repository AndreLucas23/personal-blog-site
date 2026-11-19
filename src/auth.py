from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

import user_validation as validation
from auth_user import AuthUser
from errors import abort_with_message, is_api_request
from repositories import failed_login_repository, user_repository

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

MAX_FAILED_LOGINS = 5
FAILED_LOGIN_WINDOW_MINUTES = 15

ADMIN_REQUIRED_MESSAGE = 'Admin privileges required'
DUPLICATE_EMAIL_MESSAGE = 'Este e-mail já está cadastrado.'
DUPLICATE_USERNAME_MESSAGE = 'Este nome de usuário já está em uso.'
INVALID_LOGIN_MESSAGE = 'E-mail, nome de usuário ou senha inválidos.'
TOO_MANY_LOGINS_MESSAGE = (
    'Muitas tentativas de login. Aguarde alguns minutos e tente novamente.'
)
REGISTRATION_ERRORS = {
    validation.NAME_REQUIRED: 'Informe seu nome.',
    validation.NAME_TOO_LONG: (
        f'O nome pode ter até {validation.MAX_DISPLAY_NAME_LENGTH} caracteres.'
    ),
    validation.USERNAME_REQUIRED: 'Escolha um nome de usuário.',
    validation.USERNAME_TOO_SHORT: (
        f'O nome de usuário precisa ter pelo menos {validation.MIN_USERNAME_LENGTH} caracteres.'
    ),
    validation.USERNAME_TOO_LONG: (
        f'O nome de usuário pode ter até {validation.MAX_USERNAME_LENGTH} caracteres.'
    ),
    validation.USERNAME_INVALID: (
        'Use só letras minúsculas sem acento, números e _ no nome de usuário.'
    ),
    validation.USERNAME_RESERVED: 'Este nome de usuário não está disponível.',
    validation.EMAIL_TOO_LONG: (
        f'O e-mail pode ter no máximo {validation.MAX_EMAIL_LENGTH} caracteres.'
    ),
    validation.EMAIL_INVALID: 'Informe um e-mail válido.',
    validation.PASSWORD_TOO_SHORT: (
        f'A senha deve ter pelo menos {validation.MIN_PASSWORD_LENGTH} caracteres.'
    ),
    validation.PASSWORD_TOO_LONG: (
        f'A senha pode ter no máximo {validation.MAX_PASSWORD_LENGTH} caracteres.'
    ),
}


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            # Pages show their own message in Portuguese; the API explains in its language.
            if is_api_request():
                abort_with_message(403, ADMIN_REQUIRED_MESSAGE)
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def find_account(login_value: str) -> tuple[str, dict | None]:
    """Read the login field as an email or a username, and find the account.

    Returns the login as the form and the failed attempts keep it, and the account.
    """
    value = login_value.strip()
    if '@' in value.removeprefix('@'):
        return value, user_repository.get_by_email(value)

    username = validation.normalize_username(value)
    return username, user_repository.get_by_username(username)


def current_user_id() -> int | None:
    return current_user.user_id if current_user.is_authenticated else None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'GET':
        return render_template('login.html')

    login_name, user = find_account(request.form.get('login', ''))
    password = request.form.get('password', '')
    ip_address = request.remote_addr or ''

    # Attempts on an account count together, whether its email or its username was typed.
    attempt_key = user['email'] if user else login_name

    # Checked before the password, so a blocked client learns nothing from guessing.
    failures = failed_login_repository.count_recent(
        attempt_key, ip_address, FAILED_LOGIN_WINDOW_MINUTES
    )
    if failures >= MAX_FAILED_LOGINS:
        flash(TOO_MANY_LOGINS_MESSAGE)
        return render_template('login.html', login=login_name), 429

    if not (user and check_password_hash(user['password_hash'], password)):
        failed_login_repository.add(attempt_key, ip_address, FAILED_LOGIN_WINDOW_MINUTES)
        flash(INVALID_LOGIN_MESSAGE)
        return render_template('login.html', login=login_name), 401

    failed_login_repository.clear(attempt_key, ip_address)
    login_user(AuthUser(user))
    return redirect(url_for('views.home'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'GET':
        return render_template('register.html')

    display_name = request.form.get('display_name', '').strip()
    username = validation.normalize_username(request.form.get('username', ''))
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    form = {'display_name': display_name, 'username': username, 'email': email}

    error_code = validation.validate_new_user(display_name, username, email, password)
    if error_code:
        flash(REGISTRATION_ERRORS[error_code])
        return render_template('register.html', **form), 400

    password_hash = generate_password_hash(password)

    try:
        user_id = user_repository.create(display_name, username, email, password_hash)
    except user_repository.DuplicateUsernameError:
        flash(DUPLICATE_USERNAME_MESSAGE)
        return render_template('register.html', **form), 409
    except user_repository.DuplicateEmailError:
        flash(DUPLICATE_EMAIL_MESSAGE)
        return render_template('register.html', **form), 409

    login_user(AuthUser(user_repository.get_by_id(user_id)))
    return redirect(url_for('views.home'))


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))
