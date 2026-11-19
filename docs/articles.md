# Articles

Every member writes articles in Markdown. The author edits and deletes their own articles, and admins remove articles that break the rules, without changing them.

## Writing

The editor lives at `/write` for a new article and at `/write/<id>` for an article of yours; other members get `403`. It has a title, an optional summary, the content and a preview of what readers will see. The toolbar and the shortcuts Ctrl+B, Ctrl+I and Ctrl+K add Markdown around the selection, Ctrl+Enter saves, and the browser warns before leaving unsaved changes. Saving opens the article.

| Field | Rule |
| --- | --- |
| `title` | Required, up to 150 characters, on one line |
| `summary` | Optional, up to 300 characters, on one line. Cards show it; without one, they show the start of the text |
| `content` | Required, up to 50,000 characters of Markdown |

## Markdown

Articles support the usual Markdown: emphasis, strikethrough, headings, lists, quotes, links, code, code blocks with a language and tables. The server renders it, and the HTML is safe to show:

- Raw HTML is shown as text, so `<script>` and event attributes never run.
- Links to `javascript:`, `vbscript:`, `file:` and `data:` are not links, and the others get `rel="nofollow ugc noopener noreferrer"`.
- Headings start at `h2`, because the title is the only `h1` of the page.
- Images are not loaded. Remote images would tell other sites who reads what, and the Content Security Policy blocks them anyway.

The reading time counts 200 words a minute.

## Addresses

An article lives at `/articles/<id>/<slug>`, where the slug is its title in lowercase ASCII words joined by hyphens, such as `/articles/12/arquitetura-limpa-na-pratica`. `/articles/<id>`, a slug from an older title and the old `/open/<id>` redirect there with `301`, so shared links keep working. The page names its canonical address and uses the summary or the start of the text as its description.

## Permissions

| Action | Anonymous | Member | Author | Admin |
| --- | --- | --- | --- | --- |
| Read | Allowed | Allowed | Allowed | Allowed |
| Create | `401` | Allowed | Allowed | Allowed |
| Edit | `401` | `403` | Allowed | `403`, unless they are the author |
| Delete | `401` | `403` | Allowed | Allowed |

The article page shows Editar and the delete button to the author, and Remover to admins. Both ask for confirmation. The moderation panel at `/admin` lists the articles with a search by title or id.

## API

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `GET` | `/api/articles` | Everyone | List the articles, or one member's with `?author=<username>` |
| `GET` | `/api/articles/<id>` | Everyone | One article with its content |
| `POST` | `/api/articles` | Signed in | Create an article with `title`, `summary` and `content` |
| `PATCH` | `/api/articles/<id>` | The author | Change any of `title`, `summary` and `content` |
| `DELETE` | `/api/articles/<id>` | The author or an admin | Delete the article |
| `POST` | `/api/previews` | Signed in | The HTML of the Markdown in `content`, as `{"html": "..."}` |

Lists give each article `article_id`, `url`, `article_title`, `summary`, `excerpt`, `reading_time`, `publish_date`, `author`, `author_username`, `author_avatar_url`, `likes` and `liked`. A single article, and the answers of `POST` and `PATCH`, also carry `article_content`.

Invalid fields answer `400` with a code for each one:

```json
{"message": "Invalid article", "errors": {"title": "title_too_long", "content": "content_required"}}
```

The codes are `title_required`, `title_too_long`, `summary_too_long`, `content_required`, `content_too_long` and `invalid` for a value that is not text. A missing article answers `404`, and an action the member may not take answers `403` with a message that says why.
