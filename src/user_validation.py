import re

MAX_USERNAME_LENGTH = 50
MAX_EMAIL_LENGTH = 255
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

USERNAME_REQUIRED = 'username_required'
USERNAME_TOO_LONG = 'username_too_long'
EMAIL_TOO_LONG = 'email_too_long'
EMAIL_INVALID = 'email_invalid'
PASSWORD_TOO_SHORT = 'password_too_short'
PASSWORD_TOO_LONG = 'password_too_long'

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def validate_new_user(username: str, email: str, password: str) -> str | None:
    """Return the code of the first problem found, or None when the data is valid."""
    if not username:
        return USERNAME_REQUIRED

    if len(username) > MAX_USERNAME_LENGTH:
        return USERNAME_TOO_LONG

    if len(email) > MAX_EMAIL_LENGTH:
        return EMAIL_TOO_LONG

    if not EMAIL_PATTERN.match(email):
        return EMAIL_INVALID

    if len(password) < MIN_PASSWORD_LENGTH:
        return PASSWORD_TOO_SHORT

    if len(password) > MAX_PASSWORD_LENGTH:
        return PASSWORD_TOO_LONG

    return None
