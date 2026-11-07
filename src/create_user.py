import argparse
import getpass
import sys

import mysql.connector
from werkzeug.security import generate_password_hash

from repositories import user_repository

MIN_PASSWORD_LENGTH = 8
DUPLICATE_ENTRY_ERROR = 1062


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Create a blog user.')
    parser.add_argument('--username', help='display name, asked for when omitted')
    parser.add_argument('--email', help='login email, asked for when omitted')
    parser.add_argument('--admin', action='store_true', help='grant admin privileges')
    return parser.parse_args()


def ask_password() -> str:
    password = getpass.getpass('Password: ')
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f'The password must have at least {MIN_PASSWORD_LENGTH} characters.')

    if getpass.getpass('Repeat the password: ') != password:
        sys.exit('The passwords do not match.')

    return password


def main() -> None:
    args = parse_args()
    username = (args.username or input('Username: ')).strip()
    email = (args.email or input('Email: ')).strip()

    if not username or '@' not in email:
        sys.exit('A username and a valid email are required.')

    password_hash = generate_password_hash(ask_password())

    try:
        user_id = user_repository.create(username, email, password_hash, args.admin)
    except mysql.connector.IntegrityError as error:
        if error.errno != DUPLICATE_ENTRY_ERROR:
            raise
        sys.exit(f'A user with the email {email} already exists.')

    role = 'admin' if args.admin else 'regular user'
    print(f'Created {role} {username} <{email}> with id {user_id}.')


if __name__ == '__main__':
    main()
