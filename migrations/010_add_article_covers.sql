-- The file name of the article's cover in the uploads volume, or NULL for none.

ALTER TABLE ARTICLES ADD COLUMN cover_path VARCHAR(64) NULL AFTER summary;
