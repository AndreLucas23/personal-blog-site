# Authentication

Readers browse the blog without an account. Creating, editing and removing articles requires a signed-in user.

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

| Endpoint | Anonymous | Signed in |
| --- | --- | --- |
| `GET /api/articles` and the search endpoints | Allowed | Allowed |
| `POST`, `PATCH` and `DELETE` under `/api/articles` | `401` with `{"message": "Authentication required"}` | Allowed |

New articles are stored with the signed-in user as author. Any signed-in user can write for now, and a later change restricts writing to admin users.

Pages that need a session redirect anonymous visitors to `/auth/login`. API routes answer with `401` instead, because the client is JavaScript and not a browser navigation.

## Trying it

```bash
curl -c cookies.txt -d 'email=admin@gmail.com&password=admin123' http://localhost:5000/auth/login
curl -b cookies.txt -H 'Content-Type: application/json' \
  -d '{"new-title": "Hello", "new-content": "First post"}' \
  http://localhost:5000/api/articles
```

## Development accounts

`sql-init/seed.sql` creates two accounts for local development only:

| Email | Password | Role |
| --- | --- | --- |
| `admin@gmail.com` | `admin123` | Admin |
| `user@gmail.com` | `user123` | Regular |

Never deploy with these accounts. Remove them from the seed or change their passwords first.

## Password hashes

Passwords are stored as Werkzeug hashes and never in plain text. To create a hash for a new seed account:

```bash
docker compose exec web python -c "from werkzeug.security import generate_password_hash as h; print(h('your-password'))"
```
