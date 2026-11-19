import re
from urllib.parse import urlsplit

MAX_DISPLAY_NAME_LENGTH = 50
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 30
MAX_EMAIL_LENGTH = 255
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_HEADLINE_LENGTH = 120
MAX_BIO_LENGTH = 500
MAX_LOCATION_LENGTH = 80
MAX_WEBSITE_LENGTH = 200

NAME_REQUIRED = 'name_required'
NAME_TOO_LONG = 'name_too_long'
USERNAME_REQUIRED = 'username_required'
USERNAME_TOO_SHORT = 'username_too_short'
USERNAME_TOO_LONG = 'username_too_long'
USERNAME_INVALID = 'username_invalid'
USERNAME_RESERVED = 'username_reserved'
EMAIL_TOO_LONG = 'email_too_long'
EMAIL_INVALID = 'email_invalid'
PASSWORD_TOO_SHORT = 'password_too_short'
PASSWORD_TOO_LONG = 'password_too_long'
HEADLINE_TOO_LONG = 'headline_too_long'
BIO_TOO_LONG = 'bio_too_long'
LOCATION_TOO_LONG = 'location_too_long'
WEBSITE_TOO_LONG = 'website_too_long'
WEBSITE_INVALID = 'website_invalid'

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
USERNAME_PATTERN = re.compile(r'^[a-z0-9_]+$')

OPTIONAL_TEXT_LIMITS = {
    'headline': (MAX_HEADLINE_LENGTH, HEADLINE_TOO_LONG),
    'bio': (MAX_BIO_LENGTH, BIO_TOO_LONG),
    'location': (MAX_LOCATION_LENGTH, LOCATION_TOO_LONG),
}

# Names that would clash with /api/users/me or pass for the staff.
# migrations/003_add_usernames.sql renames existing accounts with the same list.
RESERVED_USERNAMES = frozenset({'me', 'admin', 'moderacao', 'socialblog', 'suporte'})


def normalize_username(value: str) -> str:
    """Usernames are lowercase, and members may type the @ of the profile address."""
    return value.strip().removeprefix('@').lower()


def normalize_website(value: str) -> str:
    """Members often leave out the scheme, so https:// is assumed."""
    value = value.strip()
    if value and '://' not in value:
        value = f'https://{value}'
    return value


def validate_display_name(name: str) -> str | None:
    if not name:
        return NAME_REQUIRED

    if len(name) > MAX_DISPLAY_NAME_LENGTH:
        return NAME_TOO_LONG

    return None


def validate_username(username: str) -> str | None:
    """Check a username that already went through normalize_username."""
    if not username:
        return USERNAME_REQUIRED

    if len(username) < MIN_USERNAME_LENGTH:
        return USERNAME_TOO_SHORT

    if len(username) > MAX_USERNAME_LENGTH:
        return USERNAME_TOO_LONG

    if not USERNAME_PATTERN.match(username):
        return USERNAME_INVALID

    if username in RESERVED_USERNAMES:
        return USERNAME_RESERVED

    return None


def validate_email(email: str) -> str | None:
    if len(email) > MAX_EMAIL_LENGTH:
        return EMAIL_TOO_LONG

    if not EMAIL_PATTERN.match(email):
        return EMAIL_INVALID

    return None


def validate_password(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return PASSWORD_TOO_SHORT

    if len(password) > MAX_PASSWORD_LENGTH:
        return PASSWORD_TOO_LONG

    return None


def validate_website(website: str) -> str | None:
    """Check a website that already went through normalize_website. Empty means none."""
    if not website:
        return None

    if len(website) > MAX_WEBSITE_LENGTH:
        return WEBSITE_TOO_LONG

    try:
        parts = urlsplit(website)
    except ValueError:
        return WEBSITE_INVALID

    # Only links a browser opens as a page; this also rules out javascript: and data:.
    if parts.scheme not in ('http', 'https') or not parts.hostname or '.' not in parts.hostname:
        return WEBSITE_INVALID

    if any(character.isspace() for character in website):
        return WEBSITE_INVALID

    return None


def validate_profile(changes: dict[str, str]) -> dict[str, str]:
    """Check the profile fields a member is changing, already normalized.

    Returns the error code of each invalid field, and an empty dict when all are valid.
    """
    errors = {}

    if 'display_name' in changes:
        errors['display_name'] = validate_display_name(changes['display_name'])
    if 'username' in changes:
        errors['username'] = validate_username(changes['username'])
    for field, (limit, code) in OPTIONAL_TEXT_LIMITS.items():
        if field in changes and len(changes[field]) > limit:
            errors[field] = code
    if 'website' in changes:
        errors['website'] = validate_website(changes['website'])

    return {field: code for field, code in errors.items() if code}


def validate_new_user(
    display_name: str, username: str, email: str, password: str
) -> str | None:
    """Return the code of the first problem found, or None when the data is valid."""
    return (
        validate_display_name(display_name)
        or validate_username(username)
        or validate_email(email)
        or validate_password(password)
    )
