-- Drafts stay private to their author until they are published. The publication
-- date is set by the first publication, and edits record when they happened.

ALTER TABLE ARTICLES
    ADD COLUMN status ENUM('draft', 'published') NOT NULL DEFAULT 'published' AFTER article_content,
    MODIFY publish_date TIMESTAMP NULL DEFAULT NULL,
    ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN updated_at TIMESTAMP NULL;

UPDATE ARTICLES SET created_at = publish_date;
