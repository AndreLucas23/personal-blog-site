# Authentication

Readers browse Social Blog without an account. Writing, liking and editing a profile need one, and moderation needs an admin.

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
| `GET` | `/auth/login` | Login page. Redirects to the home page, or to `next`, when the user is already signed in |
| `POST` | `/auth/login` | Form fields `login`, the email or the username, and `password`. Redirects to `next`, or to the home page, on success and answers `401` with the login page otherwise, or `429` after too many failed attempts |
| `GET` | `/auth/register` | Registration page. Redirects to the home page, or to `next`, when the user is already signed in |
| `POST` | `/auth/register` | Form fields `display_name`, `username`, `email` and `password`. Creates a regular user, signs them in and redirects to `next` or to the home page. Answers `400` for invalid data and `409` for an email or a username that is already registered, both with the registration page |
| `POST` | `/auth/logout` | Ends the session and redirects to the home page. Requires a session |

Every `POST` needs the CSRF token described below.

Both forms take an optional `next`, in the address or as a form field, with the page to return to after signing in. Only a page on this site is accepted: a path that starts with one `/`, followed by printable ASCII without spaces or backslashes, outside `/api/` and `/auth/`. Anything else, such as `https://other.site`, `//other.site` or `/\other.site`, is ignored and the member goes to the home page, so the login cannot be used to send people to another site. The forms keep `next` through failed attempts and pass it to each other.

The session cookie is `HttpOnly` and `SameSite=Lax`. With `SESSION_COOKIE_SECURE=1` it is also `Secure`, so browsers send it only over HTTPS. Switch it on whenever the application is served over HTTPS.

## CSRF protection

A page on another site must not be able to act as a signed-in visitor. Each session has a random token, and every `POST`, `PATCH` and `DELETE` request has to send it back:

- Forms send it in the hidden field `csrf_token`.
- The JavaScript client sends it in the `X-CSRF-Token` header, read from `<meta name="csrf-token">` in the page.

A request without the token of its session answers `400`, as a page for the forms and as `{"message": "Invalid or missing CSRF token"}` for the API. The token is checked before the session, so an API request without it answers `400` even for a visitor.

Logout is a `POST` for the same reason: a link that ends the session could be triggered from any site.

## Login attempts

After five failed attempts on the same account from the same address within fifteen minutes, the login answers `429` and asks the visitor to wait, even when the password is right. The block ends when the oldest of those attempts is fifteen minutes old, and a successful login clears the count.

Attempts on an account count together whether its email or its username was typed. Logins that match no account are limited by what was typed, so the answer does not reveal which emails or usernames are registered. The attempts are stored in the `FAILED_LOGINS` table and removed once they no longer count.

## Registration

Anyone can create an account. Registration always creates a regular user, and any admin field sent with the form is ignored. Admins are created only with the command described below.

The same rules apply to registration and to the create-user command:

| Field | Rule |
| --- | --- |
| Name | Required and up to 50 characters, with surrounding spaces removed |
| Username | 3 to 30 lowercase letters without accents, digits and underscores, unique and not reserved, as [profiles.md](profiles.md#usernames) describes |
| Email | A valid address of up to 255 characters, unique regardless of letter case |
| Password | Between 8 and 128 characters |

## Access rules

| Endpoint | Anonymous | Signed-in user | Admin |
| --- | --- | --- | --- |
| `GET /api/articles` and the search endpoints | Allowed | Allowed | Allowed |
| `POST /api/articles` | `401` | Allowed | Allowed |
| `PATCH /api/articles/<id>` | `401` | Only for their own articles, `403` otherwise | Only for their own articles |
| `DELETE /api/articles/<id>` | `401` | Only for their own articles, `403` otherwise | Allowed |
| `POST` and `DELETE /api/articles/<id>/likes` | `401` | Allowed | Allowed |
| `GET /admin` | Redirects to `/auth/login` | `403` | Allowed |

Every `401` from the API has the body `{"message": "Authentication required", "login_url": "/auth/login"}`. Likes are described in [likes.md](likes.md).

New articles are stored with the member who created them as author, as [articles.md](articles.md#permissions) describes. The admin flag is read from the database on every request, so removing it takes effect immediately, even for sessions that are already open.

Pages that need a session redirect anonymous visitors to `/auth/login?next=<page>`, and the Entrar and Criar conta links of the pages lead back to them too. API routes answer with `401` instead, because the client is JavaScript and not a browser navigation. When the browser receives a `401` from the API, for example after the session expired or when a visitor clicks a like button, it opens the `login_url` with the current page as `next`.

## Pages

| Page | Who sees it | What it offers |
| --- | --- | --- |
| `/` | Everyone | The article list with authors and like buttons, and the search by title. Articles cannot be changed from it |
| `/articles/<id>/<slug>` | Everyone | The article, its author and its like button. The author also gets Editar and Excluir, and admins Remover |
| `/write` and `/write/<id>` | Signed in | The editor, for a new article or one of your own |
| `/admin` | Admins | Moderação: the article list with the search and the removal of articles |
| `/@<username>` | Everyone | The profile of a member, as [profiles.md](profiles.md#pages) describes |
| `/settings/profile` | Signed in | The profile settings. Visitors are sent to the login page |
| `/auth/login` | Visitors | The login form, with the email or the username. After an invalid attempt the login is kept and the password is asked again |
| `/auth/register` | Visitors | The registration form. After an error the name, the username and the email are kept, and the browser already blocks passwords shorter than 8 characters |

The top bar shows Entrar and Criar conta to visitors, and the login and registration pages link to each other. Signed-in users get Escrever and an account menu with their photo, name and username, links to their profile and to the profile settings, the theme choice and Sair, and admins also see Moderação in the top bar.

## Creating users

The database starts empty: no account exists until you create one. With the stack running, create the first admin:

```bash
docker compose exec web python src/create_user.py --admin
```

The command asks for the name, the username, the email and the password, which is typed twice and never shown. Pass `--name`, `--username` and `--email` to skip those questions, and leave out `--admin` to create a regular user. The command follows the rules listed under Registration. The password is stored as a Werkzeug hash, never in plain text. An email or a username that is already registered is reported and nothing is created.

## Trying it

```bash
token=$(curl -s -c cookies.txt http://localhost:5000/auth/login \
  | grep -o 'name="csrf-token" content="[^"]*"' | cut -d'"' -f4)
curl -b cookies.txt -c cookies.txt --data-urlencode "csrf_token=$token" \
  -d 'login=you@example.com&password=your-password' http://localhost:5000/auth/login
curl -b cookies.txt -H "X-CSRF-Token: $token" -H 'Content-Type: application/json' \
  -d '{"new-title": "Hello", "new-content": "First post"}' \
  http://localhost:5000/api/articles
```

The first command opens a session and reads its CSRF token from the login page. Use the email or the username and the password of the admin you created.

## Databases created before this change

Earlier versions seeded two accounts with known passwords, `admin@gmail.com` and `user@gmail.com`, together with sample articles. A database volume created back then still contains them. Never keep those accounts outside your own machine. To start clean in development, discard the volume and let the schema run again:

```bash
docker compose down -v
docker compose up --build
```

Deleting only the two users also deletes the sample articles written by them, because articles are removed together with their author.
