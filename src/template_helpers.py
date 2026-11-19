"""Helpers that templates call to draw icons, avatars and dates the same way everywhere."""
from datetime import datetime, timezone
from urllib.parse import urlsplit

from flask import Flask, url_for
from markupsafe import Markup, escape

AVATAR_COLORS = 8
MONTHS = (
    'jan.', 'fev.', 'mar.', 'abr.', 'mai.', 'jun.',
    'jul.', 'ago.', 'set.', 'out.', 'nov.', 'dez.',
)
MONTH_NAMES = (
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
)


def long_date(value: datetime) -> str:
    """A date as people read it in Brazil, such as 18 de nov. de 2026."""
    return f'{value.day} de {MONTHS[value.month - 1]} de {value.year}'


def month_year(value: datetime) -> str:
    """Such as novembro de 2026, for how long someone has been a member."""
    return f'{MONTH_NAMES[value.month - 1]} de {value.year}'


def website_label(url: str) -> str:
    """A website as people say it: without the scheme, the www and the last slash."""
    parts = urlsplit(url)
    label = (parts.netloc + parts.path).removeprefix('www.').rstrip('/')
    return label or url


def iso_datetime(value: datetime) -> str:
    # MySQL returns TIMESTAMP columns without a zone, in UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def initials(name: str) -> str:
    """The first letter of the first and the last word, as avatars show them."""
    words = (name or '').split()
    if not words:
        return '?'
    letters = words[0][0] + (words[-1][0] if len(words) > 1 else '')
    return letters.upper()


def avatar_color(name: str) -> int:
    """A stable color index for a name. static/js/ui/avatar.js computes the same value."""
    value = 0
    for character in name or '':
        value = (value * 31 + ord(character)) & 0xFFFFFFFF
    return value % AVATAR_COLORS


def icon(name: str, class_name: str = '') -> Markup:
    href = f"{url_for('static', filename='imgs/icons.svg')}#{name}"
    classes = f'icon {class_name}'.strip()
    return Markup(
        f'<svg class="{escape(classes)}" aria-hidden="true" focusable="false">'
        f'<use href="{escape(href)}"></use></svg>'
    )


def avatar(name: str, size: str = 'md', image_url: str | None = None) -> Markup:
    """The member's photo when there is one, their initials otherwise."""
    if image_url:
        # The name is always shown next to it, so the photo needs no text of its own.
        return Markup(
            f'<img class="avatar avatar--{escape(size)}" src="{escape(image_url)}" '
            'alt="" loading="lazy" decoding="async">'
        )
    return Markup(
        f'<span class="avatar avatar--{escape(size)} avatar--c{avatar_color(name)}" '
        f'aria-hidden="true">{escape(initials(name))}</span>'
    )


def init_app(app: Flask) -> None:
    app.jinja_env.globals.update(icon=icon, avatar=avatar)
    app.jinja_env.filters.update(
        long_date=long_date,
        month_year=month_year,
        website_label=website_label,
        iso_datetime=iso_datetime,
    )
