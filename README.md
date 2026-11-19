# Social Blog

[![CI](https://github.com/AndreLucas23/personal-blog-site/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/AndreLucas23/personal-blog-site/actions/workflows/ci.yml)

Social Blog is a social network for publishing and reading articles, built with Flask and MySQL and run with Docker. The interface is in Brazilian Portuguese.

## Features

- Anyone can read and search articles, each with its author, date and like count.
- Visitors can create an account with a name and a unique username, and sign in with the email or the username.
- Every member has a public profile with a headline, a bio, a location, a website and a photo, which the API reads and changes.
- Signed-in users can like and unlike articles.
- Admins create, search and remove articles in the admin panel at `/admin`, and edit them on the article page.
- Every page shares a top bar and a layout with three columns on wide screens and one on phones, in light and dark themes that follow the system or the choice in the account menu.

How accounts, sessions and permissions work is described in [docs/authentication.md](docs/authentication.md), profiles and avatars in [docs/profiles.md](docs/profiles.md), and likes in [docs/likes.md](docs/likes.md).

## Stack

- Python 3.11 and Flask 3, with Flask-Login for sessions
- MySQL 8
- Gunicorn as the production server
- HTML, CSS and JavaScript without a build step
- Docker and Docker Compose

## Getting started

Requirements: Docker with the Compose plugin.

1. Create the environment file and replace the placeholder values. `SECRET_KEY` is required, and you can generate one with:

   ```bash
   cp TEMPLATE.env .env
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Start the application and the database:

   ```bash
   docker compose up --build
   ```

3. Create the first admin. The command asks for the name, the username, the email and the password:

   ```bash
   docker compose exec web python src/create_user.py --admin
   ```

4. Open http://localhost:5000, sign in and open the admin panel from Painel in the top bar.

The web container applies the [database migrations](#database-migrations) every time it starts, so a new database gets its tables on the first start. The database starts empty, with no accounts and no articles. To discard the data and start again, remove the volume:

```bash
docker compose down -v
```

If port 3306 is already used on your machine, change the host side of the `db` port mapping in `docker-compose.yml`.

## Configuration

Variables are read from `.env`, which is never committed. `TEMPLATE.env` lists all of them.

| Variable | Description | Default in `docker-compose.yml` |
| --- | --- | --- |
| `DB_HOST` | Database host name | `blog_mysql` |
| `DB_USER` | Application database user | `blog_user` |
| `DB_ROOT_PASSWORD` | MySQL root password | `root1234` |
| `DB_PASSWORD` | Application database password | `1234` |
| `DB_NAME` | Database name | `BLOG` |
| `SECRET_KEY` | Signs the session cookie | None: required |
| `FLASK_DEBUG` | `1` runs the development server with the debugger and the reloader | `1` |
| `CORS_ORIGINS` | Origins allowed to call the API from a browser, separated by commas | Empty: none |
| `SESSION_COOKIE_SECURE` | `1` makes browsers send the session cookie only over HTTPS | `0` |
| `UPLOAD_DIR` | Directory of the uploaded images, kept in the `uploads_data` volume | `/data/uploads` |

The defaults exist only for local development. Always set your own values outside of it.

## Database migrations

The schema is the result of the SQL files in `migrations/`, applied in the order of their numbers. The `SCHEMA_MIGRATIONS` table records the ones a database already has, so each file runs once and the data stays in place.

The web container applies the pending migrations before it starts the application. To apply them by hand:

```bash
docker compose exec web python src/migrate.py
```

On a deploy without Docker Compose, run `python src/migrate.py` with the `DB_*` variables set before starting the application. If a migration fails, the command exits with an error and the application does not start.

To change the schema, add a file with the next number, such as `migrations/002_add_article_summary.sql`:

- The name is three digits, an underscore and a short description in lowercase `snake_case`.
- A file can hold several statements.
- Never edit a migration that was already merged. Databases that have it will not run it again, so correct it with a new migration.
- MySQL cannot roll back `CREATE` or `ALTER TABLE`. A migration that fails halfway leaves its first statements applied, so keep each file small and undo the partial change by hand before running it again.

A database created before migrations existed needs nothing special: the first migration keeps the existing tables and their data and only records the starting point.

## Deployment

`docker-compose.yml` describes the development setup: the Flask development server with debug mode, the source code mounted into the container and default passwords. Do not expose it to the internet.

The image itself is ready for production. Its default command applies the pending migrations and starts Gunicorn on port 5000, as the unprivileged user `app`:

```bash
docker build -t personal-blog-site .
docker run --env-file production.env -p 5000:5000 personal-blog-site
```

`production.env` stands for a file with the variables of the Configuration section, where `DB_HOST` points at a MySQL server the container can reach.

Before the first deploy:

- Set your own `SECRET_KEY` and database passwords.
- Leave `FLASK_DEBUG` unset or `0`. The debugger lets anyone who reaches it run code on the server.
- Serve the application over HTTPS and set `SESSION_COOKIE_SECURE=1`, which also sends `Strict-Transport-Security`.
- Leave `CORS_ORIGINS` empty unless a page on another origin must call the API.
- Set `WEB_CONCURRENCY` to the number of Gunicorn workers you want. The default is one.

Behind a reverse proxy every request reaches the application from the address of the proxy, so the [login limit](docs/authentication.md#login-attempts) counts per account only.

## Tests

The suite uses pytest and a real MySQL 8 database, so it also checks the rules the database enforces. Run it with Docker Compose:

```bash
docker compose --profile test run --rm tests
```

The `test` profile starts a separate, disposable MySQL kept in memory, so your development data is never touched. The suite refuses to run unless `BLOG_TEST_DATABASE=1` is set, which only the test service does. The tests live in `tests/`, one module per area, with the shared fixtures in `tests/conftest.py`.

To run one module or one test, replace the service command:

```bash
docker compose --profile test run --rm tests sh -c "pip install -q -r requirements-dev.txt && pytest tests/test_likes.py"
```

## Project structure

```text
migrations/             Database schema, one numbered SQL file per change
docs/                   Authentication, profiles and likes
tests/                  Automated tests, run with the test profile
src/
  app.py                Application entry point and sessions
  errors.py             Error pages and JSON errors
  media.py              Serving the uploaded images under /media
  uploads.py            Checking, resizing and storing uploaded images
  security_headers.py   Content Security Policy and browser hardening headers
  template_helpers.py   Icons, avatars and dates for the templates
  views.py              Pages: home, article and admin panel
  api.py                JSON API under /api
  auth.py               Login, logout, registration and the admin check
  csrf.py               CSRF token for state-changing requests
  auth_user.py          The signed-in user model
  user_validation.py    Rules for usernames, emails and passwords
  create_user.py        Command to create users from the terminal
  migrate.py            Command to apply the pending database migrations
  db.py                 Database connection
  settings.py           Reading options from environment variables
  repositories/         Data access, one module per table
  templates/            Jinja pages that extend base.html, with shared pieces in partials/
  static/               Styles, scripts and images:
    css/                theme.css (tokens and themes), layout.css, ui.css (components) and pages/
    js/                 api.js, ui/ helpers, components/ and one entry point per page in pages/
    imgs/               Logo and the icons.svg sprite used by templates and scripts
```

## API

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `GET` | `/api/articles` | Everyone | List all articles, or one member's with `?author=<username>` |
| `GET` | `/api/articles/id/<id>` | Everyone | Search articles by id, partial match |
| `GET` | `/api/articles/title/<title>` | Everyone | Search articles by title, partial match |
| `POST` | `/api/articles` | Admins | Create an article with `new-title` and `new-content` |
| `PATCH` | `/api/articles/<id>` | Admins | Update `title` and/or `content` |
| `DELETE` | `/api/articles/<id>` | Admins | Remove an article |
| `POST` | `/api/articles/<id>/likes` | Signed in | Like an article |
| `DELETE` | `/api/articles/<id>/likes` | Signed in | Remove your like |
| `GET` | `/api/users/<username>` | Everyone | A member's public profile |
| `GET` | `/api/users/me` | Signed in | Your profile, with your email |
| `PATCH` | `/api/users/me` | Signed in | Change your name, username, headline, bio, location or website |
| `PUT` | `/api/users/me/avatar` | Signed in | Upload your avatar as a `multipart/form-data` field named `avatar` |
| `DELETE` | `/api/users/me/avatar` | Signed in | Remove your avatar |

Each article has `article_id`, `article_title`, `article_content`, `publish_date`, `author` with the display name of the author, `author_username`, `author_avatar_url`, `likes` and `liked`, which tells whether the signed-in viewer liked it. Titles are limited to 30 characters. [docs/profiles.md](docs/profiles.md#api) describes the profile endpoints and their errors.

Without a session the protected endpoints answer `401` with the login page URL, and regular users get `403` from the admin endpoints.

Errors answer JSON with a `message`, such as `{"message": "Not found"}` for an unknown route, and never include internal details. Database failures answer `500` with `{"status": "error", "message": "An internal error occurred while accessing the database"}`. Pages show the same errors as styled pages in Portuguese.

`POST`, `PATCH` and `DELETE` requests must send the CSRF token of the session in the `X-CSRF-Token` header and answer `400` without it, as [docs/authentication.md](docs/authentication.md#csrf-protection) describes.

## Security

To report a vulnerability, follow the [security policy](SECURITY.md) instead of opening a public issue.

Every response carries a Content Security Policy that only lets the application's own scripts, styles, images, fonts and forms run, and forbids framing the site. It also sends `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, a `Permissions-Policy` that turns off the camera, microphone, location, payment and USB features, and `Cross-Origin-Opener-Policy` and `Cross-Origin-Resource-Policy` set to `same-origin`. The policy blocks inline code, so templates have no inline scripts, styles or event handler attributes.

## Contributing

Branches, commits, pull requests and issues follow the conventions in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Released under the [MIT License](LICENSE).
