def replace_article_tags(cursor, article_id: int, names: list[str]) -> None:
    """Replace the tags of an article, keeping the order the author gave them.

    It runs on the cursor of the article's own save, so the article and its tags are
    written together or not at all.
    """
    cursor.execute('DELETE FROM ARTICLE_TAGS WHERE article_id = %s', (article_id,))

    tag_ids = []
    for name in names:
        # LAST_INSERT_ID(tag_id) hands back the id of a tag that already exists.
        cursor.execute(
            'INSERT INTO TAGS (name) VALUES (%s) '
            'ON DUPLICATE KEY UPDATE tag_id = LAST_INSERT_ID(tag_id)',
            (name,)
        )
        # Variants with and without accents are one tag, so ids can repeat.
        if cursor.lastrowid not in tag_ids:
            tag_ids.append(cursor.lastrowid)

    for position, tag_id in enumerate(tag_ids):
        cursor.execute(
            'INSERT INTO ARTICLE_TAGS (article_id, tag_id, position) VALUES (%s, %s, %s)',
            (article_id, tag_id, position)
        )
