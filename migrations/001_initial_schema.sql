-- IF NOT EXISTS keeps the tables and the data of a database created before
-- migrations existed, where this file only records the starting point.

CREATE TABLE IF NOT EXISTS USERS (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ARTICLES (
    article_id INT AUTO_INCREMENT PRIMARY KEY,
    article_title VARCHAR(30) NOT NULL,
    article_content TEXT NOT NULL,
    author_id INT NOT NULL,
    publish_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_articles_author FOREIGN KEY (author_id) REFERENCES USERS(user_id) ON DELETE CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS LIKES (
    user_id INT NOT NULL,
    article_id INT NOT NULL,
    PRIMARY KEY (user_id, article_id),
    CONSTRAINT fk_likes_user FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_likes_article FOREIGN KEY (article_id) REFERENCES ARTICLES(article_id) ON DELETE CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
