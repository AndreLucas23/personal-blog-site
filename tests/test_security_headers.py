import pytest

import security_headers

EXPECTED = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cross-Origin-Opener-Policy': 'same-origin',
}


@pytest.mark.parametrize('path', [
    '/',
    '/auth/login',
    '/api/articles',
    '/static/css/theme.css',
    '/nao-existe',
    '/api/nao-existe',
])
def test_every_response_carries_the_security_headers(client, path):
    response = client.get(path)

    for name, value in EXPECTED.items():
        assert response.headers.get(name) == value, (path, name)
    assert response.headers['Content-Security-Policy'] == security_headers.CONTENT_SECURITY_POLICY
    assert 'Permissions-Policy' in response.headers


def test_content_security_policy_allows_only_the_application(client):
    policy = client.get('/').headers['Content-Security-Policy']
    directives = dict(part.strip().split(' ', 1) for part in policy.split(';'))

    assert directives['default-src'] == "'self'"
    assert directives['script-src'] == "'self'"
    assert directives['style-src'] == "'self'"
    assert directives['object-src'] == "'none'"
    assert directives['frame-ancestors'] == "'none'"
    assert directives['form-action'] == "'self'"
    assert 'unsafe-inline' not in policy
    assert 'unsafe-eval' not in policy


def test_strict_transport_security_only_over_https(app, client, monkeypatch):
    assert 'Strict-Transport-Security' not in client.get('/').headers

    monkeypatch.setitem(app.config, 'SESSION_COOKIE_SECURE', True)

    assert client.get('/').headers['Strict-Transport-Security'] == 'max-age=31536000'
