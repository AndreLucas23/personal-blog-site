# Personal Blog Site

A personal blog for publishing articles, built with Flask and MySQL and run with Docker. The interface is in Brazilian Portuguese.

## Features

- Anyone can read and filter articles, each with its author, date and like count.
- Visitors can create an account, sign in and sign out.
- Signed-in users can like and unlike articles.
- Admins create, filter and remove articles in the admin panel at `/admin`, and edit them on the article page.

How accounts, sessions and permissions work is described in [docs/authentication.md](docs/authentication.md), and likes in [docs/likes.md](docs/likes.md).

## Stack

- Python 3.11 and Flask 3, with Flask-Login for sessions
- MySQL 8
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

3. Create the first admin. The command asks for the username, the email and the password:

   ```bash
   docker compose exec web python src/create_user.py --admin
   ```

4. Open http://localhost:5000, sign in and open the admin panel from the sidebar.

The MySQL container creates the schema from `sql-init/schema.sql` on its first start. The database starts empty, with no accounts and no articles. To discard the data and start again, remove the volume:

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

The defaults exist only for local development. Always set your own values outside of it.

## Project structure

```text
sql-init/schema.sql     Database schema, loaded on the first start
docs/                   Authentication and likes
src/
  app.py                Application entry point, sessions and error handling
  views.py              Pages: home, article and admin panel
  api.py                JSON API under /api
  auth.py               Login, logout, registration and the admin check
  auth_user.py          The signed-in user model
  user_validation.py    Rules for usernames, emails and passwords
  create_user.py        Command to create users from the terminal
  db.py                 Database connection
  repositories/         Data access, one module per table
  templates/            Jinja pages, with shared pieces in partials/
  static/               CSS, JavaScript and images, with page entry points in js/pages/
```

## API

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `GET` | `/api/articles` | Everyone | List all articles |
| `GET` | `/api/articles/id/<id>` | Everyone | Search articles by id, partial match |
| `GET` | `/api/articles/title/<title>` | Everyone | Search articles by title, partial match |
| `POST` | `/api/articles` | Admins | Create an article with `new-title` and `new-content` |
| `PATCH` | `/api/articles/<id>` | Admins | Update `title` and/or `content` |
| `DELETE` | `/api/articles/<id>` | Admins | Remove an article |
| `POST` | `/api/articles/<id>/likes` | Signed in | Like an article |
| `DELETE` | `/api/articles/<id>/likes` | Signed in | Remove your like |

Each article has `article_id`, `article_title`, `article_content`, `publish_date`, `author`, `likes` and `liked`, which tells whether the signed-in viewer liked it. Titles are limited to 30 characters.

Without a session the protected endpoints answer `401` with the login page URL, and regular users get `403` from the admin endpoints.

## Contributing

Branches, commits, pull requests and issues follow the conventions in [CONTRIBUTING.md](CONTRIBUTING.md).
