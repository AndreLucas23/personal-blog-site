from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from auth_user import AuthUser
from repositories import user_repository

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    user = user_repository.get_by_email(email)
    is_valid = user and check_password_hash(user['password_hash'], password)

    if not is_valid:
        flash('E-mail ou senha inválidos.')
        return render_template('login.html'), 401

    login_user(AuthUser(user))
    return redirect(url_for('views.home'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))
