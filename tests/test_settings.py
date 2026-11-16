import pytest

import settings


@pytest.mark.parametrize('value', ['1', 'true', 'True', 'YES', 'on', ' 1 '])
def test_env_flag_is_on_for_affirmative_values(monkeypatch, value):
    monkeypatch.setenv('BLOG_EXAMPLE_FLAG', value)

    assert settings.env_flag('BLOG_EXAMPLE_FLAG') is True


@pytest.mark.parametrize('value', ['', '0', 'false', 'no', 'off', 'anything'])
def test_env_flag_is_off_for_other_values(monkeypatch, value):
    monkeypatch.setenv('BLOG_EXAMPLE_FLAG', value)

    assert settings.env_flag('BLOG_EXAMPLE_FLAG') is False


def test_env_flag_is_off_when_the_variable_is_not_set(monkeypatch):
    monkeypatch.delenv('BLOG_EXAMPLE_FLAG', raising=False)

    assert settings.env_flag('BLOG_EXAMPLE_FLAG') is False
