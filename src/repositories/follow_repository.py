from datetime import datetime

import mysql.connector

from db import db_cursor
from pagination import PAGE_SIZE

MISSING_REFERENCE_ERROR = 1452
SUGGESTIONS = 3
MAX_SUGGESTIONS = 10

# Whether the viewer, the placeholder, follows the member u. Profiles and lists share it,
# so they never disagree.
VIEWER_FOLLOWS = (
    'EXISTS(SELECT 1 FROM FOLLOWS mine WHERE mine.follower_id = %s AND mine.followed_id = u.user_id)'
)
# The first placeholder is the viewer id, to tell whether they follow each member listed.
MEMBER_COLUMNS = (
    'u.user_id, u.username, u.display_name, u.headline, u.avatar_path, '
    f'{VIEWER_FOLLOWS} AS followed'
)

# Suggestions leave out everyone the viewer follows, so none of them is followed yet.
SUGGESTION_COLUMNS = 'u.user_id, u.username, u.display_name, u.headline, u.avatar_path, FALSE AS followed'

# For each list: the column of the member whose list it is, and of the members listed.
LISTS = {
    'followers': ('f.followed_id', 'f.follower_id'),
    'following': ('f.follower_id', 'f.followed_id'),
}


def follow(follower_id: int, followed_id: int) -> bool:
    """Follow a member. Following again keeps the single row the primary key allows.

    False when the member no longer exists, such as an account removed during the request.
    """
    try:
        with db_cursor() as cursor:
            cursor.execute(
                'INSERT INTO FOLLOWS (follower_id, followed_id) VALUES (%s, %s) '
                'ON DUPLICATE KEY UPDATE follower_id = follower_id',
                (follower_id, followed_id)
            )
    except mysql.connector.IntegrityError as error:
        if error.errno != MISSING_REFERENCE_ERROR:
            raise
        return False
    return True


def unfollow(follower_id: int, followed_id: int) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            'DELETE FROM FOLLOWS WHERE follower_id = %s AND followed_id = %s',
            (follower_id, followed_id)
        )


def is_following(follower_id: int, followed_id: int) -> bool:
    with db_cursor() as cursor:
        cursor.execute(
            'SELECT 1 FROM FOLLOWS WHERE follower_id = %s AND followed_id = %s',
            (follower_id, followed_id)
        )
        return cursor.fetchone() is not None


def get_members(
    kind: str,
    user_id: int,
    viewer_id: int | None = None,
    after: tuple[datetime, int] | None = None,
    limit: int = PAGE_SIZE,
) -> list[dict]:
    """A member's followers or following, the most recent follows first, after the cursor."""
    owner, listed = LISTS[kind]
    query = (
        f'SELECT {MEMBER_COLUMNS}, f.created_at AS followed_at FROM FOLLOWS f '
        f'JOIN USERS u ON u.user_id = {listed} WHERE {owner} = %s'
    )
    params = [viewer_id, user_id]
    if after is not None:
        followed_at, member_id = after
        # The id orders follows made in the same second.
        query += f' AND (f.created_at < %s OR (f.created_at = %s AND {listed} < %s))'
        params += [followed_at, followed_at, member_id]
    query += f' ORDER BY f.created_at DESC, {listed} DESC LIMIT %s'
    params.append(limit)

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, tuple(params))
        return [with_follow_flag(member) for member in cursor.fetchall()]


def suggestions(user_id: int, limit: int = SUGGESTIONS) -> list[dict]:
    """Members to follow: those the people you follow follow, then recent authors.

    Never yourself, someone you already follow or the same member twice.
    """
    # Placeholders: the member's id, twice.
    new_to_you = (
        'u.user_id <> %s AND NOT EXISTS (SELECT 1 FROM FOLLOWS f '
        'WHERE f.follower_id = %s AND f.followed_id = u.user_id)'
    )
    with db_cursor(dictionary=True) as cursor:
        # The more of the people you follow follow someone, the earlier they come.
        cursor.execute(
            f'SELECT {SUGGESTION_COLUMNS} FROM FOLLOWS yours '
            'JOIN FOLLOWS theirs ON theirs.follower_id = yours.followed_id '
            'JOIN USERS u ON u.user_id = theirs.followed_id '
            f'WHERE yours.follower_id = %s AND {new_to_you} '
            'GROUP BY u.user_id ORDER BY COUNT(*) DESC, u.user_id DESC LIMIT %s',
            (user_id, user_id, user_id, limit),
        )
        chosen = cursor.fetchall()

        if len(chosen) < limit:
            ids = [member['user_id'] for member in chosen]
            not_chosen = f' AND u.user_id NOT IN ({", ".join(["%s"] * len(ids))})' if ids else ''
            cursor.execute(
                f'SELECT {SUGGESTION_COLUMNS} FROM USERS u '
                "JOIN ARTICLES a ON a.author_id = u.user_id AND a.status = 'published' "
                f'WHERE {new_to_you}{not_chosen} '
                'GROUP BY u.user_id ORDER BY MAX(a.publish_date) DESC, u.user_id DESC LIMIT %s',
                (user_id, user_id, *ids, limit - len(chosen)),
            )
            chosen += cursor.fetchall()

    return [with_follow_flag(member) for member in chosen]


def with_follow_flag(member: dict | None) -> dict | None:
    """The member with followed as a bool, as MySQL answers 0 or 1."""
    if member is not None:
        member['followed'] = bool(member['followed'])
    return member


def count_followers(user_id: int) -> int:
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM FOLLOWS WHERE followed_id = %s', (user_id,))
        return cursor.fetchone()[0]
