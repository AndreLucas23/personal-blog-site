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
- Changing the title, the summary, the content, the tags or the cover records when the article was updated, while saving them unchanged or only moving between draft and published does not. The article page mentions the update when it happened on a later day than the publication.
- Your profile has a Rascunhos tab with your drafts, the most recently edited first, and only published articles collect likes.

## Covers

An article may have a cover: a JPEG, PNG or WebP image of up to 5 MB, cropped to 1200 by 630 pixels, the shape of link previews, and stored as WebP in the uploads volume like avatars. Cards and the article page show it above the title.

The editor shows the chosen cover at once and sends it when the article is saved, like the words, so a new cover reaches readers only with Publicar or Salvar alterações. Publicar saves the draft and its new cover before it publishes, so readers get the article with the cover or not at all. If the cover is refused, the article is saved without it and the editor keeps the reason next to the cover. Replacing or removing a cover, or deleting the article, deletes the old file.

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
| `GET` | `/api/articles` | Everyone | A page of published articles, newest first, or of one member's with `?author=<username>` |
| `GET` | `/api/articles/<id>` | Everyone | One article with its content |
| `POST` | `/api/articles` | Signed in | Create an article with `title`, `summary`, `content`, `tags` and `status` |
| `PATCH` | `/api/articles/<id>` | The author | Change any of `title`, `summary`, `content`, `tags` and `status` |
| `DELETE` | `/api/articles/<id>` | The author or an admin | Delete the article |
| `PUT` | `/api/articles/<id>/cover` | The author | Set the cover, sent as a `multipart/form-data` field named `cover` |
| `DELETE` | `/api/articles/<id>/cover` | The author | Remove the cover |
| `GET` | `/api/users/me/drafts` | Signed in | Your drafts, the most recently edited first |
| `POST` | `/api/previews` | Signed in | The HTML of the Markdown in `content`, as `{"html": "..."}` |

`GET /api/articles` answers one page at a time, as `{"articles": [...], "next_cursor": "..."}`. `limit` sets the number of articles, from 1 to 50 and 20 by default, and `next_cursor`, passed back as `?cursor=`, asks for the next page; it is `null` on the last one. A cursor holds the position of the last article shown, so articles published in the meantime do not repeat or skip any. An invalid cursor or limit answers `400`. The searches by title and by id answer every match in a list, and so does the list of drafts.

Lists give each article `article_id`, `url`, `article_title`, `summary`, `cover_url`, `tags`, `excerpt`, `reading_time`, `status`, `publish_date` (`null` for a draft that was never published), `created_at`, `updated_at`, `author`, `author_username`, `author_avatar_url`, `likes` and `liked`. A single article, and the answers of `POST`, `PATCH` and the cover endpoints, also carry `article_content`.

Invalid fields answer `400` with a code for each one:

```json
{"message": "Invalid article", "errors": {"title": "title_too_long", "content": "content_required"}}
```

The codes are `title_required`, `title_too_long`, `summary_too_long`, `content_required`, `content_too_long`, `tags_too_many`, `tag_too_short`, `tag_too_long` and `invalid` for a value of the wrong type, such as tags that are not a list of text or an unknown status. A missing article answers `404`, and an action the member may not take answers `403` with a message that says why.

A cover that cannot be used answers `400`, or `413` when the request is too large, with the code under `cover`: `image_missing`, `image_invalid`, `image_format` or `image_too_large`.
