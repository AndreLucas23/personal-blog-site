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
TOO_MANY_LOGINS_MESSAGE = (
    'Muitas tentativas de login. Aguarde alguns minutos e tente novamente.'
)
REGISTRATION_ERRORS = {
    validation.USERNAME_REQUIRED: 'Informe um nome de usuário.',
    validation.USERNAME_TOO_LONG: (
        f'O nome de usuário pode ter até {validation.MAX_USERNAME_LENGTH} caracteres.'
    ),
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


def current_user_id() -> int | None:
    return current_user.user_id if current_user.is_authenticated else None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    ip_address = request.remote_addr or ''

    # Checked before the password, so a blocked client learns nothing from guessing.
    failures = failed_login_repository.count_recent(
        email, ip_address, FAILED_LOGIN_WINDOW_MINUTES
    )
    if failures >= MAX_FAILED_LOGINS:
        flash(TOO_MANY_LOGINS_MESSAGE)
        return render_template('login.html', email=email), 429

    user = user_repository.get_by_email(email)
    is_valid = user and check_password_hash(user['password_hash'], password)

    if not is_valid:
        failed_login_repository.add(email, ip_address, FAILED_LOGIN_WINDOW_MINUTES)
        flash('E-mail ou senha inválidos.')
        return render_template('login.html', email=email), 401

    failed_login_repository.clear(email, ip_address)
    login_user(AuthUser(user))
    return redirect(url_for('views.home'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    error_code = validation.validate_new_user(username, email, password)
    if error_code:
        flash(REGISTRATION_ERRORS[error_code])
        return render_template('register.html', username=username, email=email), 400

    password_hash = generate_password_hash(password)

    try:
        user_id = user_repository.create(username, email, password_hash)
    except user_repository.DuplicateEmailError:
        flash(DUPLICATE_EMAIL_MESSAGE)
        return render_template('register.html', username=username, email=email), 409

    login_user(AuthUser(user_repository.get_by_id(user_id)))
    return redirect(url_for('views.home'))


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))
