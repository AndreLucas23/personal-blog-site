# Personal Blog Site

A personal blog for publishing articles, built with Flask and MySQL and run with Docker. The interface is in Brazilian Portuguese.

## Stack

- Python 3.11 and Flask 3
- MySQL 8
- HTML, CSS and JavaScript without a build step
- Docker and Docker Compose

## Getting started

Requirements: Docker with the Compose plugin.

1. Create the environment file and replace the placeholder values:

   ```bash
   cp TEMPLATE.env .env
   ```

2. Start the application and the database:

   ```bash
   docker compose up --build
   ```

3. Open http://localhost:5000.

The database schema and sample data are loaded by the MySQL container on its first start. To discard the data and load it again, remove the volume:

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

The defaults exist only for local development. Always set your own values outside of it.

## Project structure

```text
src/
  app.py            Application entry point and error handling
  views.py          Pages: home and article
  api.py            JSON API under /api
  db.py             Database connection
  repositories/     Data access, one module per table
  templates/        Jinja templates
  static/           CSS, JavaScript and images
```

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/articles` | List all articles |
| `POST` | `/api/articles` | Create an article with `new-title` and `new-content` |
| `PATCH` | `/api/articles/<id>` | Update `title` and/or `content` |
| `DELETE` | `/api/articles/<id>` | Remove an article |
| `GET` | `/api/articles/id/<id>` | Search articles by id, partial match |
| `GET` | `/api/articles/title/<title>` | Search articles by title, partial match |

Titles are limited to 30 characters.

## Contributing

Branches, commits, pull requests and issues follow the conventions in [CONTRIBUTING.md](CONTRIBUTING.md).
