# Authentication

Readers browse the blog without an account. Creating, editing and removing articles requires an admin user.

## Configuration

The session cookie is signed with `SECRET_KEY`. The application and `docker compose` refuse to start when it is missing or empty.

Generate a value and store it in `.env`, which `TEMPLATE.env` lists:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Changing the value signs every user out.

## Routes

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/auth/login` | Login page. Redirects to the home page when the user is already signed in |
| `POST` | `/auth/login` | Form fields `email` and `password`. Redirects to the home page on success and answers `401` with the login page otherwise |
| `GET` | `/auth/logout` | Ends the session and redirects to the home page. Requires a session |

The session cookie is `HttpOnly` and `SameSite=Lax`.

## Access rules

| Endpoint | Anonymous | Signed-in user | Admin |
| --- | --- | --- | --- |
| `GET /api/articles` and the search endpoints | Allowed | Allowed | Allowed |
| `POST`, `PATCH` and `DELETE` under `/api/articles` | `401` with `{"message": "Authentication required"}` | `403` with `{"message": "Admin privileges required"}` | Allowed |
| `GET /admin` | Redirects to `/auth/login` | `403` | Allowed |

New articles are stored with the admin who created them as author. The admin flag is read from the database on every request, so removing it takes effect immediately, even for sessions that are already open.

Pages that need a session redirect anonymous visitors to `/auth/login`. API routes answer with `401` instead, because the client is JavaScript and not a browser navigation. The `/admin` page is a placeholder until the admin panel interface is delivered.

## Creating users

The database starts empty: no account exists until you create one. With the stack running, create the first admin:

```bash
docker compose exec web python src/create_user.py --admin
```

The command asks for the username, the email and the password, which is typed twice and never shown. Pass `--username` and `--email` to skip those questions, and leave out `--admin` to create a regular user. The password needs at least 8 characters and is stored as a Werkzeug hash, never in plain text. An email that is already registered is reported and nothing is created.

## Trying it

```bash
curl -c cookies.txt -d 'email=you@example.com&password=your-password' http://localhost:5000/auth/login
curl -b cookies.txt -H 'Content-Type: application/json' \
  -d '{"new-title": "Hello", "new-content": "First post"}' \
  http://localhost:5000/api/articles
```

Use the email and password of the admin you created.

## Databases created before this change

Earlier versions seeded two accounts with known passwords, `admin@gmail.com` and `user@gmail.com`, together with sample articles. A database volume created back then still contains them. Never keep those accounts outside your own machine. To start clean in development, discard the volume and let the schema run again:

```bash
docker compose down -v
docker compose up --build
```

Deleting only the two users also deletes the sample articles written by them, because articles are removed together with their author.
