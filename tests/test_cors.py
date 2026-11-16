from flask import Flask

from app import configure_cors

ALLOWED_ORIGIN = 'https://blog.example'
OTHER_ORIGIN = 'https://other.example'


def app_with_cors(origins: list[str]) -> Flask:
    flask_app = Flask(__name__)
    flask_app.add_url_rule('/api/ping', 'ping', lambda: 'pong')
    flask_app.add_url_rule('/page', 'page', lambda: 'page')
    configure_cors(flask_app, origins)
    return flask_app


def allowed_origin(flask_app: Flask, path: str, origin: str) -> str | None:
    response = flask_app.test_client().get(path, headers={'Origin': origin})
    return response.headers.get('Access-Control-Allow-Origin')


def test_api_answers_other_origins_without_cors_headers_by_default(client):
    response = client.get('/api/articles', headers={'Origin': OTHER_ORIGIN})

    assert response.status_code == 200
    assert 'Access-Control-Allow-Origin' not in response.headers


def test_configured_origin_is_allowed_on_the_api():
    flask_app = app_with_cors([ALLOWED_ORIGIN])

    assert allowed_origin(flask_app, '/api/ping', ALLOWED_ORIGIN) == ALLOWED_ORIGIN


def test_origin_that_is_not_configured_is_not_allowed():
    flask_app = app_with_cors([ALLOWED_ORIGIN])

    assert allowed_origin(flask_app, '/api/ping', OTHER_ORIGIN) is None


def test_configured_origin_is_not_allowed_outside_the_api():
    flask_app = app_with_cors([ALLOWED_ORIGIN])

    assert allowed_origin(flask_app, '/page', ALLOWED_ORIGIN) is None


def test_no_origin_is_allowed_without_configuration():
    flask_app = app_with_cors([])

    assert allowed_origin(flask_app, '/api/ping', ALLOWED_ORIGIN) is None
