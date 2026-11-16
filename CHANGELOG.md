# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Dependabot checks the Python packages, the Docker base image and the GitHub Actions for updates every week (#37).
- Security policy in `SECURITY.md`, with the supported versions and how to report a vulnerability privately (#37).
- Database migrations: numbered SQL files in `migrations/`, applied by `python src/migrate.py` and every time the web container starts, so the schema can change without discarding the data (#36).
- Gunicorn serves the application in the Docker image. Docker Compose keeps the development server (#19).
- `SESSION_COOKIE_SECURE` marks the session cookie `Secure` for deployments over HTTPS (#19).

### Changed

- **Breaking:** `POST`, `PATCH` and `DELETE` requests must send the CSRF token of the session, in the `csrf_token` form field or the `X-CSRF-Token` header (#19).
- **Breaking:** logout is `POST /auth/logout` instead of `GET` (#19).
- **Breaking:** the API sends CORS headers only to the origins listed in `CORS_ORIGINS`, and to none by default. It used to allow every origin (#19).
- Debug mode follows `FLASK_DEBUG` and is off when it is not set. Docker Compose switches it on (#19).
- The schema is created by the migrations instead of `sql-init/schema.sql`, which was removed. Databases created before keep their tables and data (#36).

### Fixed

- The tables were always created in a database named `BLOG`, even with another `DB_NAME` (#36).

### Security

- State-changing requests are protected against cross-site request forgery (#19).
- The login answers `429` after five failed attempts for the same email from the same address within fifteen minutes (#19).
- The container runs as an unprivileged user instead of root (#19).

## [1.0.0] - 2026-11-08

The first release: a personal blog with articles, public accounts, an admin panel and likes.

### Added

- Articles with title and content, listed on the home page, opened on their own page and searched by title or id.
- Accounts: public registration, login and logout with sessions (#4, #10, #18).
- Admin panel at `/admin` to create, filter and remove articles, and editing on the article page, restricted to admins (#5, #6).
- Likes on the feed and on the article page, with one like per user enforced by the database (#7).
- Authors shown on every article (#7).
- `src/create_user.py`, a command to create users and the first admin from the terminal (#17).
- Automated tests with pytest against a disposable MySQL database (#13).
- Continuous integration that runs the tests and audits the dependencies on every pull request (#32).
- README, contributing guide, pull request and issue templates, and documentation for authentication and likes (#9, #16).
- MIT license (#34).

### Changed

- The home page is read-only. Creating and removing articles moved to the admin panel (#6).
- The database starts empty, and the first admin is created with the command (#17).
- `SECRET_KEY` is required, and the application refuses to start without it (#4).
- Database access goes through a single helper that commits, rolls back and closes connections (#12).

### Fixed

- Saving an article without changes answered 404 (#24).
- Updates accepted an empty or blank title and empty content, values that were not text caused a 500, and removing a missing article answered 200 (#33).

### Security

- Writes to articles require an admin session, and liking requires a session (#4, #5, #7).
- Passwords are stored as hashes, and the session cookie is `HttpOnly` and `SameSite=Lax` (#4).
- The seeded accounts with known passwords were removed (#17).
- Database errors no longer expose internal details such as the database host (#11).
- Flask and Werkzeug updated to versions without known vulnerabilities (#31).

[Unreleased]: https://github.com/AndreLucas23/personal-blog-site/compare/v1.0.0...dev
[1.0.0]: https://github.com/AndreLucas23/personal-blog-site/releases/tag/v1.0.0
