# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Article covers: JPEG, PNG or WebP, cropped to 1200 by 630 and stored as WebP, chosen in the editor and sent with the article, shown on cards and on the article page, with `PUT` and `DELETE /api/articles/<id>/cover` (#82).
- Mais artigos on the home page, on profiles and in moderation, which loads the next page of articles (#82).
- Private drafts: save without publishing, publish later and move a published article back to drafts, with a Rascunhos tab on your profile and `GET /api/users/me/drafts` (#81).
- Up to 5 tags per article, normalized to lowercase words joined by hyphens, shown on cards and articles and given in the editor as chips (#81).
- Articles record when they were updated, and their page mentions edits made on a later day (#81).
- Every member writes articles in Markdown, with an optional summary, in an editor at `/write` with a toolbar, shortcuts and a preview, and edits them at `/write/<id>` (#80).
- Articles live at `/articles/<id>/<slug>`, show the formatted text and the reading time, and give the author Editar and Excluir (#80).
- `GET /api/articles/<id>` and `POST /api/previews` (#80).
- Profile pages at `/@<username>` with the member's photo, details, bio and articles, and the profile settings at `/settings/profile` with the photo upload (#76).
- Member photos in the top bar, the account menu, the profile card, the article cards and the byline, which link to the profile (#76).
- Every member has a unique username and a display name. Existing accounts get a username derived from their name (#75).
- Sign in with the email or the username (#75).
- Profile fields: headline, bio, location and website, with `GET /api/users/<username>`, and `GET` and `PATCH /api/users/me` (#75).
- Avatar upload with `PUT` and `DELETE /api/users/me/avatar`: JPEG, PNG or WebP up to 5 MB, stored as a 400 px WebP square in the `uploads_data` volume and served from `/media`, where only browsers cache them, for a day (#75).
- Articles in the API carry `author_username` and `author_avatar_url`, and `GET /api/articles?author=<username>` lists one member's articles (#75).
- `UPLOAD_DIR` sets the directory of the uploaded images (#75).
- A social network layout on every page: a top bar with the main destinations and an account menu, three columns on wide screens and one on phones, and shared components for cards, forms, menus, dialogs and messages (#70).
- Light and dark themes that follow the system, with a theme choice in the account menu (#70).
- Error pages in the new layout for 400, 403, 404, 405 and 500, and JSON errors with a `message` for every error under `/api` (#71).
- Dependabot checks the Python packages, the Docker base image and the GitHub Actions for updates every week (#37).
- Security policy in `SECURITY.md`, with the supported versions and how to report a vulnerability privately (#37).
- Database migrations: numbered SQL files in `migrations/`, applied by `python src/migrate.py` and every time the web container starts, so the schema can change without discarding the data (#36).
- Gunicorn serves the application in the Docker image. Docker Compose keeps the development server (#19).
- `SESSION_COOKIE_SECURE` marks the session cookie `Secure` for deployments over HTTPS (#19).

### Changed

- **Breaking:** `GET /api/articles` answers one page, newest first, as `{"articles": [...], "next_cursor": ...}` instead of a list of every article, with `limit` and `cursor` to choose the page (#82).
- The Content Security Policy also allows `blob:` images, so the editor shows a chosen cover before it is sent (#82).
- **Breaking:** `POST /api/articles` takes `title`, `summary` and `content` instead of `new-title` and `new-content`, and invalid fields answer `400` with an error code for each one (#80).
- **Breaking:** any member creates articles; only the author edits them, and the author or an admin deletes them. Admins no longer edit other members' articles (#80).
- **Breaking:** article lists leave `article_content` out and carry `url`, `summary`, `excerpt` and `reading_time` (#80).
- `/open/<id>` redirects to the article's new address (#80).
- Titles take up to 150 characters, and the content up to 50,000 (#80).
- The admin panel became Moderação, without the creation dialog (#80).
- **Breaking:** the login form field is `login` instead of `email`, and registration asks for `display_name` and `username` (#75).
- **Breaking:** `create_user.py` takes `--name` for the display name, and `--username` is now the unique username (#75).
- `author` in the API and the pages is the display name of the author (#75).
- The failed-login limit counts the attempts on an account together, whether its email or its username was typed (#75).
- Requests larger than 6 MB answer `413` (#75).
- The product is now called Social Blog (#70).
- Pages use system fonts and one SVG icon sprite instead of Google Fonts and inline icons, so they make no requests to other sites (#70).
- A database error on a page shows the error page instead of JSON (#71).
- **Breaking:** `POST`, `PATCH` and `DELETE` requests must send the CSRF token of the session, in the `csrf_token` form field or the `X-CSRF-Token` header (#19).
- **Breaking:** logout is `POST /auth/logout` instead of `GET` (#19).
- **Breaking:** the API sends CORS headers only to the origins listed in `CORS_ORIGINS`, and to none by default. It used to allow every origin (#19).
- Debug mode follows `FLASK_DEBUG` and is off when it is not set. Docker Compose switches it on (#19).
- The schema is created by the migrations instead of `sql-init/schema.sql`, which was removed. Databases created before keep their tables and data (#36).

### Fixed

- The tables were always created in a database named `BLOG`, even with another `DB_NAME` (#36).

### Security

- Article Markdown is rendered without raw HTML or unsafe links, links are marked `nofollow ugc`, and remote images are not loaded (#80).
- Profile websites cannot carry a user name before the host, such as `https://bank.com@evil.example`, which would disguise where the link goes (#76).
- Every response carries a Content Security Policy that allows only the application's own scripts, styles, images and forms, plus `nosniff`, frame denial, a strict referrer policy, a permissions policy and same-origin isolation headers (#71).
- `SESSION_COOKIE_SECURE=1` also sends `Strict-Transport-Security` (#71).
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
