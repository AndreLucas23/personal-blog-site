-- Every member writes now: titles of up to 150 characters, an optional summary and
-- Markdown content longer than a TEXT column holds.

ALTER TABLE ARTICLES
    MODIFY article_title VARCHAR(150) NOT NULL,
    ADD COLUMN summary VARCHAR(300) NULL AFTER article_title,
    MODIFY article_content MEDIUMTEXT NOT NULL;
