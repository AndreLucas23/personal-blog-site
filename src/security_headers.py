"""Browser hardening headers sent with every response."""
from flask import Flask, Response, current_app

# Only this application's own files may run, style the pages, load or receive data.
CONTENT_SECURITY_POLICY = '; '.join((
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self'",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
))

HEADERS = {
    'Content-Security-Policy': CONTENT_SECURITY_POLICY,
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
}

# Sent only when the site is served over HTTPS, which SESSION_COOKIE_SECURE declares.
STRICT_TRANSPORT_SECURITY = 'max-age=31536000'


def add_security_headers(response: Response) -> Response:
    for name, value in HEADERS.items():
        response.headers.setdefault(name, value)

    if current_app.config.get('SESSION_COOKIE_SECURE'):
        response.headers.setdefault('Strict-Transport-Security', STRICT_TRANSPORT_SECURITY)

    return response


def init_app(app: Flask) -> None:
    app.after_request(add_security_headers)
