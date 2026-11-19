import argparse
import getpass
import sys

from werkzeug.security import generate_password_hash

import user_validation as validation
from repositories import user_repository

ERROR_MESSAGES = {
    validation.NAME_REQUIRED: 'A name is required.',
    validation.NAME_TOO_LONG: (
        f'The name can have at most {validation.MAX_DISPLAY_NAME_LENGTH} characters.'
    ),
    validation.USERNAME_REQUIRED: 'A username is required.',
    validation.USERNAME_TOO_SHORT: (
        f'The username needs at least {validation.MIN_USERNAME_LENGTH} characters.'
    ),
    validation.USERNAME_TOO_LONG: (
        f'The username can have at most {validation.MAX_USERNAME_LENGTH} characters.'
    ),
    validation.USERNAME_INVALID: (
        'The username can only have lowercase letters, digits and underscores.'
    ),
    validation.USERNAME_RESERVED: 'This username is reserved.',
    validation.EMAIL_TOO_LONG: (
        f'The email can have at most {validation.MAX_EMAIL_LENGTH} characters.'
    ),
    validation.EMAIL_INVALID: 'A valid email is required.',
    validation.PASSWORD_TOO_SHORT: (
        f'The password must have at least {validation.MIN_PASSWORD_LENGTH} characters.'
    ),
    validation.PASSWORD_TOO_LONG: (
        f'The password can have at most {validation.MAX_PASSWORD_LENGTH} characters.'
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Create a Social Blog user.')
    parser.add_argument('--name', help='display name, asked for when omitted')
    parser.add_argument('--username', help='unique username, asked for when omitted')
    parser.add_argument('--email', help='login email, asked for when omitted')
    parser.add_argument('--admin', action='store_true', help='grant admin privileges')
    return parser.parse_args()


def exit_on_error(error_code: str | None) -> None:
    if error_code:
        sys.exit(ERROR_MESSAGES[error_code])


def ask_password() -> str:
    password = getpass.getpass('Password: ')
    exit_on_error(validation.validate_password(password))

    if getpass.getpass('Repeat the password: ') != password:
        sys.exit('The passwords do not match.')

    return password


def main() -> None:
    args = parse_args()
    display_name = (args.name or input('Name: ')).strip()
    exit_on_error(validation.validate_display_name(display_name))
    username = validation.normalize_username(args.username or input('Username: '))
    exit_on_error(validation.validate_username(username))
    email = (args.email or input('Email: ')).strip()
    exit_on_error(validation.validate_email(email))

    password_hash = generate_password_hash(ask_password())

    try:
        user_id = user_repository.create(
            display_name, username, email, password_hash, args.admin
        )
    except user_repository.DuplicateUsernameError:
        sys.exit(f'The username {username} is already taken.')
    except user_repository.DuplicateEmailError:
        sys.exit(f'A user with the email {email} already exists.')

    role = 'admin' if args.admin else 'regular user'
    print(f'Created {role} {display_name} (@{username}) <{email}> with id {user_id}.')


if __name__ == '__main__':
    main()
