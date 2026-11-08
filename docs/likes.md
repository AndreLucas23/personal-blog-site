# Likes

Signed-in users can like and unlike articles. Visitors see the like counts, and clicking a like button sends them to the login page.

## Rules

- A user likes an article at most once. The primary key of the `LIKES` table, `(user_id, article_id)`, enforces it in the database.
- Liking an article that is already liked, or unliking one that is not, changes nothing and still succeeds.
- Likes are removed together with their article or their user.

## API

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/articles/<id>/likes` | Like the article as the signed-in user |
| `DELETE` | `/api/articles/<id>/likes` | Remove the like of the signed-in user |

Both need a session and answer `200` with the new state:

```json
{"liked": true, "likes": 3}
```

They answer `401` without a session and `404` for a missing article.

Every article returned by the API also has `likes`, the number of likes, and `liked`, which is `true` when the signed-in viewer liked it and always `false` for visitors.

## Interface

Each card on the home page and on the admin panel, and the article page, show a heart with the count. The button toggles between liked and not liked without reloading the page, and its state comes from the server, so it is the same after a reload or on another page.
