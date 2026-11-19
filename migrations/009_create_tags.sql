-- Topics members give their articles. The collation makes a tag match its variants
-- with and without accents, so "programação" and "programacao" are one tag.

CREATE TABLE TAGS (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    CONSTRAINT uq_tags_name UNIQUE (name)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ARTICLE_TAGS (
    article_id INT NOT NULL,
    tag_id INT NOT NULL,
    position TINYINT NOT NULL,
    PRIMARY KEY (article_id, tag_id),
    INDEX idx_article_tags_tag (tag_id, article_id),
    CONSTRAINT fk_article_tags_article FOREIGN KEY (article_id) REFERENCES ARTICLES(article_id) ON DELETE CASCADE,
    CONSTRAINT fk_article_tags_tag FOREIGN KEY (tag_id) REFERENCES TAGS(tag_id) ON DELETE CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
