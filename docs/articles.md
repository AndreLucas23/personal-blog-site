# Articles

Every member writes articles in Markdown. The author edits and deletes their own articles, and admins remove articles that break the rules, without changing them.

## Writing

The editor lives at `/write` for a new article and at `/write/<id>` for an article of yours; other members get `403`. It has a title, an optional summary, the content and a preview of what readers will see. The toolbar and the shortcuts Ctrl+B, Ctrl+I and Ctrl+K add Markdown around the selection, Ctrl+Enter saves, and the browser warns before leaving unsaved changes. Saving opens the article.

| Field | Rule |
| --- | --- |
| `title` | Required, up to 150 characters, on one line |
| `summary` | Optional, up to 300 characters, on one line. Cards show it; without one, they show the start of the text |
| `content` | Required to publish, up to 50,000 characters of Markdown |
| `tags` | Optional, up to 5 tags, as described below |
| `status` | `draft` or `published`, the default |

## Drafts

An article is a draft or published. A draft needs only its title, so members can start with an idea and write later; publishing needs the content too.

- A draft is visible only to its author: it stays out of every list, search and profile count, and its page, its editor and `GET /api/articles/<id>` answer `404` to anyone else, admins included.
- The editor saves a draft with Salvar rascunho and stays open, showing when it was saved; a new draft gets its own address, so a reload keeps editing it. Publicar publishes and opens the article.
- The first publication sets the publication date. A published article can go back to drafts with Mover para rascunhos, and publishing it again keeps the first date.
- Changing the title, the summary, the content or the tags records when the article was updated, while saving them unchanged or only moving between draft and published does not. The article page mentions the update when it happened on a later day than the publication.
- Your profile has a Rascunhos tab with your drafts, the most recently edited first, and only published articles collect likes.

## Tags

An article has up to 5 tags, given in the editor as chips and kept in the order given. Tags are normalized to lowercase words joined by hyphens, with accents kept and repeats dropped: `Banco de Dados` becomes `banco-de-dados` and `#Python` becomes `python`. Each tag has 2 to 30 characters. Variants with and without accents, such as `programação` and `programacao`, are the same tag, which keeps the spelling it was first given.

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
| `POST` | `/api/articles` | Signed in | Create an article with `title`, `summary`, `content`, `tags` and `status` |
| `PATCH` | `/api/articles/<id>` | The author | Change any of `title`, `summary`, `content`, `tags` and `status` |
| `DELETE` | `/api/articles/<id>` | The author or an admin | Delete the article |
| `GET` | `/api/users/me/drafts` | Signed in | Your drafts, the most recently edited first |
| `POST` | `/api/previews` | Signed in | The HTML of the Markdown in `content`, as `{"html": "..."}` |

Lists give each article `article_id`, `url`, `article_title`, `summary`, `tags`, `excerpt`, `reading_time`, `status`, `publish_date` (`null` for a draft that was never published), `created_at`, `updated_at`, `author`, `author_username`, `author_avatar_url`, `likes` and `liked`. A single article, and the answers of `POST` and `PATCH`, also carry `article_content`.

Invalid fields answer `400` with a code for each one:

```json
{"message": "Invalid article", "errors": {"title": "title_too_long", "content": "content_required"}}
```

The codes are `title_required`, `title_too_long`, `summary_too_long`, `content_required`, `content_too_long`, `tags_too_many`, `tag_too_short`, `tag_too_long` and `invalid` for a value of the wrong type, such as tags that are not a list of text or an unknown status. A missing article answers `404`, and an action the member may not take answers `403` with a message that says why.
