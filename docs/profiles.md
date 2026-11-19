# Profiles

Every member has a public profile: a display name, a unique username, a few fields that describe them and an optional photo. The username is the address of the profile, and the display name is how pages show the member.

## Usernames

- 3 to 30 lowercase letters without accents, digits and underscores, unique across the site.
- Members may type it with uppercase letters, surrounding spaces or the `@` of the profile address: the site stores `@Ana_Souza ` as `ana_souza`.
- `me`, `admin`, `moderacao`, `socialblog` and `suporte` are reserved. `me` would clash with `/api/users/me`, and the others could pass for the staff.
- Members can change their username. The old one is free again at once, and its profile address stops working.

Accounts created before usernames existed got one from their name when migration `003_add_usernames.sql` ran: lowercase, without accents, with an underscore for anything that is not a letter or a digit, and cut at 30 characters. `André Lucas` became `andre_lucas`. A name that ended up shorter than 3 characters, reserved or already taken became `user_<id>` instead. The previous name became the display name.

## Fields

| Field | Rule |
| --- | --- |
| `display_name` | Required, up to 50 characters, with surrounding spaces removed |
| `username` | The rules above |
| `headline` | Optional, up to 120 characters, such as a role or a company |
| `bio` | Optional, up to 500 characters. Line breaks are kept |
| `location` | Optional, up to 80 characters |
| `website` | Optional, an `http` or `https` address of up to 200 characters, without a user name or password before the host. `https://` is added when the scheme is missing |

An empty optional field clears it. The email is never shown on a public profile.

## Avatars

A member can upload a JPEG, PNG or WebP of up to 5 MB and 40 million pixels. The site turns the photo upright from its EXIF orientation, crops the center to a square, resizes it to 400 by 400 pixels and stores it as WebP, which also drops the metadata of the original file. Transparency is kept. Other files are refused before anything is stored.

Each upload gets a new random name in the directory set by `UPLOAD_DIR`, `/data/uploads` by default, which Docker Compose keeps in the `uploads_data` volume. Uploading a new avatar or removing it deletes the previous file. `/media/<name>` serves the files as `image/webp`. Browsers keep them for a day and shared caches such as proxies never store them, so a removed photo stops showing up.

Without an avatar, pages show the initials of the display name on a color picked from the name.

## Pages

| Page | Who sees it | What it offers |
| --- | --- | --- |
| `/@<username>` | Everyone | The photo, name, username, headline, location, website, join date, bio and articles of the member. Your own profile has an Editar perfil button. Other letter cases redirect to the lowercase address, and unknown usernames answer `404` |
| `/settings/profile` | Signed in | The form for every field, with the rules and counters next to them, and the photo upload. Errors from the API appear under their fields in Portuguese |

The top bar, the account menu, the profile card on the home page, the article cards and the byline of an article show the member's photo, and their names and photos lead to the profile. The account menu links to your profile and to the profile settings. A change saved in the settings, including a new photo or username, shows up on the page without a reload.

The website opens in a new tab with `rel="nofollow ugc noopener noreferrer"`, so the page cannot reach back to the site and search engines do not count the link as an endorsement. Its text is the host and the path, without the scheme or `www.`, so it always names the site the link opens.

## API

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `GET` | `/api/users/<username>` | Everyone | The public profile |
| `GET` | `/api/users/me` | Signed in | Your profile, with your email |
| `PATCH` | `/api/users/me` | Signed in | Change any of the fields above |
| `PUT` | `/api/users/me/avatar` | Signed in | Upload your avatar as the `avatar` field of a `multipart/form-data` body |
| `DELETE` | `/api/users/me/avatar` | Signed in | Remove your avatar |

A profile looks like this:

```json
{
  "username": "ana_souza",
  "display_name": "Ana Souza",
  "headline": "Engenheira de dados",
  "bio": "Escrevo sobre bancos de dados.",
  "location": "Recife, PE",
  "website": "https://ana.dev",
  "avatar_url": "/media/90d3d185479424cdda709135cdbf1dc6.webp",
  "joined_at": "Wed, 18 Nov 2026 23:32:18 GMT",
  "articles": 3
}
```

`PATCH` answers `200` with your profile, `400` with an error code for each invalid field, and `409` when the username is taken:

```json
{"message": "Invalid profile", "errors": {"username": "username_too_short", "website": "website_invalid"}}
```

The codes are `name_required`, `name_too_long`, `username_required`, `username_too_short`, `username_too_long`, `username_invalid`, `username_reserved`, `username_taken`, `headline_too_long`, `bio_too_long`, `location_too_long`, `website_too_long`, `website_invalid` and `invalid` for a value that is not text. Fields other than the ones above are ignored.

The avatar upload answers `200` with `{"avatar_url": "/media/<name>.webp"}`, `400` with the code `image_missing`, `image_invalid`, `image_format` or `image_too_large` in `errors.avatar`, and `413` with `image_too_large` when the whole request is larger than 6 MB.

Profiles of unknown usernames answer `404` with `{"message": "User not found"}`. Like every request that changes something, `PATCH`, `PUT` and `DELETE` need the [CSRF token](authentication.md#csrf-protection).
