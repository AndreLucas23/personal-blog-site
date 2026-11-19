from datetime import datetime, timezone

import pytest

import template_helpers


@pytest.mark.parametrize('name, expected', [
    ('Ana Souza', 'AS'),
    ('ana  maria   souza', 'AS'),
    ('Owner', 'O'),
    ('ñandú Peña', 'ÑP'),
    ('', '?'),
    ('   ', '?'),
])
def test_initials_use_the_first_and_last_words(name, expected):
    assert template_helpers.initials(name) == expected


def test_avatar_color_is_stable_and_in_range():
    # The same values as static/js/ui/avatar.js, which must stay in sync.
    assert template_helpers.avatar_color('Ana Souza') == 4
    assert template_helpers.avatar_color('André Lucas') == 2
    assert template_helpers.avatar_color('') == 0
    assert all(0 <= template_helpers.avatar_color(f'user {n}') < 8 for n in range(50))


def test_long_date_uses_portuguese_month_names():
    assert template_helpers.long_date(datetime(2026, 11, 18, 23, 59)) == '18 de nov. de 2026'
    assert template_helpers.long_date(datetime(2026, 1, 2)) == '2 de jan. de 2026'


def test_iso_datetime_marks_naive_values_as_utc():
    assert template_helpers.iso_datetime(datetime(2026, 11, 18, 10, 30)) == '2026-11-18T10:30:00+00:00'
    aware = datetime(2026, 11, 18, 10, 30, tzinfo=timezone.utc)
    assert template_helpers.iso_datetime(aware) == '2026-11-18T10:30:00+00:00'


def test_avatar_escapes_the_name(app):
    with app.test_request_context():
        markup = str(template_helpers.avatar('<i>x</i>', 'sm'))

    assert '<i>' not in markup
    assert 'avatar--sm' in markup


def test_icon_points_at_the_sprite(app):
    with app.test_request_context():
        markup = str(template_helpers.icon('heart', 'icon--sm'))

    assert 'class="icon icon--sm"' in markup
    assert 'href="/static/imgs/icons.svg#heart"' in markup
    assert 'aria-hidden="true"' in markup


def test_avatar_shows_the_photo_when_there_is_one(app):
    with app.test_request_context():
        markup = str(template_helpers.avatar('Ana', 'lg', '/media/x.webp'))

    assert markup.startswith('<img class="avatar avatar--lg"')
    assert 'src="/media/x.webp"' in markup
    assert 'alt=""' in markup


def test_month_year_uses_full_portuguese_month_names():
    assert template_helpers.month_year(datetime(2026, 3, 5)) == 'março de 2026'


@pytest.mark.parametrize(('url', 'label'), [
    ('https://ana.dev', 'ana.dev'),
    ('https://www.ana.dev/', 'ana.dev'),
    ('http://ana.dev/blog/', 'ana.dev/blog'),
    ('https://paypal.com@evil.example/', 'evil.example'),
    ('https://ana.dev:8443/', 'ana.dev'),
])
def test_website_label_drops_the_scheme_and_the_www(url, label):
    assert template_helpers.website_label(url) == label
