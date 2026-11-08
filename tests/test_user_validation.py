import pytest

import user_validation as validation

VALID_PASSWORD = 'long-enough'


@pytest.mark.parametrize(
    ('username', 'email', 'expected'),
    [
        ('Ana', 'ana@example.com', None),
        ('João Silva', 'joao@exemplo.com.br', None),
        ('x' * 50, 'a@b.co', None),
        ('', 'a@b.co', validation.USERNAME_REQUIRED),
        ('x' * 51, 'a@b.co', validation.USERNAME_TOO_LONG),
        ('Ana', 'x' * 250 + '@b.co', None),
        ('Ana', 'x' * 251 + '@b.co', validation.EMAIL_TOO_LONG),
        ('Ana', 'no-at-sign', validation.EMAIL_INVALID),
        ('Ana', 'a@b', validation.EMAIL_INVALID),
        ('Ana', 'a b@c.co', validation.EMAIL_INVALID),
    ],
)
def test_validate_identity(username, email, expected):
    assert validation.validate_identity(username, email) == expected


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


def test_validate_new_user_reports_identity_before_password():
    error = validation.validate_new_user('', 'bad', 'short')

    assert error == validation.USERNAME_REQUIRED


def test_validate_new_user_accepts_valid_data():
    error = validation.validate_new_user('Ana', 'ana@example.com', VALID_PASSWORD)

    assert error is None
