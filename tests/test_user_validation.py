import pytest

import user_validation as validation

VALID_PASSWORD = 'long-enough'


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        ('Ana', None),
        ('João da Silva', None),
        ('x' * 50, None),
        ('', validation.NAME_REQUIRED),
        ('x' * 51, validation.NAME_TOO_LONG),
    ],
)
def test_validate_display_name(name, expected):
    assert validation.validate_display_name(name) == expected


@pytest.mark.parametrize(
    ('raw', 'normalized'),
    [
        ('ana', 'ana'),
        ('  Ana_Souza  ', 'ana_souza'),
        ('@ana', 'ana'),
        (' @ANA ', 'ana'),
    ],
)
def test_normalize_username(raw, normalized):
    assert validation.normalize_username(raw) == normalized


@pytest.mark.parametrize(
    ('username', 'expected'),
    [
        ('ana', None),
        ('ana_souza_2026', None),
        ('x' * 30, None),
        ('', validation.USERNAME_REQUIRED),
        ('an', validation.USERNAME_TOO_SHORT),
        ('x' * 31, validation.USERNAME_TOO_LONG),
        ('ana souza', validation.USERNAME_INVALID),
        ('ana-souza', validation.USERNAME_INVALID),
        ('andré', validation.USERNAME_INVALID),
        ('Ana', validation.USERNAME_INVALID),
        ('me', validation.USERNAME_TOO_SHORT),
        ('admin', validation.USERNAME_RESERVED),
        ('socialblog', validation.USERNAME_RESERVED),
    ],
)
def test_validate_username(username, expected):
    assert validation.validate_username(username) == expected


def test_reserved_usernames_include_the_api_alias():
    assert 'me' in validation.RESERVED_USERNAMES


@pytest.mark.parametrize(
    ('email', 'expected'),
    [
        ('ana@example.com', None),
        ('joao@exemplo.com.br', None),
        ('x' * 250 + '@b.co', None),
        ('x' * 251 + '@b.co', validation.EMAIL_TOO_LONG),
        ('no-at-sign', validation.EMAIL_INVALID),
        ('a@b', validation.EMAIL_INVALID),
        ('a b@c.co', validation.EMAIL_INVALID),
    ],
)
def test_validate_email(email, expected):
    assert validation.validate_email(email) == expected


@pytest.mark.parametrize(
    ('password', 'expected'),
    [
        ('x' * 8, None),
        ('x' * 128, None),
        ('x' * 7, validation.PASSWORD_TOO_SHORT),
        ('', validation.PASSWORD_TOO_SHORT),
        ('x' * 129, validation.PASSWORD_TOO_LONG),
    ],
)
def test_validate_password(password, expected):
    assert validation.validate_password(password) == expected


def test_validate_new_user_reports_the_first_problem_in_form_order():
    assert validation.validate_new_user('', 'a', 'bad', 'short') == validation.NAME_REQUIRED
    assert validation.validate_new_user('Ana', 'a', 'bad', 'short') == validation.USERNAME_TOO_SHORT
    assert validation.validate_new_user('Ana', 'ana', 'bad', 'short') == validation.EMAIL_INVALID
    assert validation.validate_new_user('Ana', 'ana', 'a@b.co', 'short') == validation.PASSWORD_TOO_SHORT


def test_validate_new_user_accepts_valid_data():
    error = validation.validate_new_user('Ana', 'ana', 'ana@example.com', VALID_PASSWORD)

    assert error is None


@pytest.mark.parametrize(
    ('raw', 'normalized'),
    [
        ('', ''),
        ('  ', ''),
        ('example.com', 'https://example.com'),
        (' http://example.com ', 'http://example.com'),
        ('https://example.com/path?q=1', 'https://example.com/path?q=1'),
    ],
)
def test_normalize_website(raw, normalized):
    assert validation.normalize_website(raw) == normalized


@pytest.mark.parametrize(
    ('website', 'expected'),
    [
        ('', None),
        ('https://example.com', None),
        ('http://sub.example.com.br/a', None),
        ('https://' + 'a' * 190 + '.com', validation.WEBSITE_TOO_LONG),
        ('https://localhost', validation.WEBSITE_INVALID),
        ('https://exa mple.com', validation.WEBSITE_INVALID),
        ('ftp://example.com', validation.WEBSITE_INVALID),
        ('https://javascript:alert(1)', validation.WEBSITE_INVALID),
        ('https://[::1', validation.WEBSITE_INVALID),
    ],
)
def test_validate_website(website, expected):
    assert validation.validate_website(website) == expected


def test_validate_profile_reports_every_invalid_field():
    errors = validation.validate_profile({
        'display_name': '',
        'username': 'ok_name',
        'headline': 'x' * 121,
        'bio': 'fine',
        'website': 'nope',
    })

    assert errors == {
        'display_name': validation.NAME_REQUIRED,
        'headline': validation.HEADLINE_TOO_LONG,
        'website': validation.WEBSITE_INVALID,
    }


def test_validate_profile_accepts_valid_changes():
    assert validation.validate_profile({'headline': 'x' * 120, 'location': ''}) == {}
