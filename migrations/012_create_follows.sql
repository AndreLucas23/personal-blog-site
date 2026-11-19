-- Members follow each other without approval. A row goes from the follower to the
-- member followed, and goes away with either account.

CREATE TABLE FOLLOWS (
    follower_id INT NOT NULL,
    followed_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followed_id),
    INDEX idx_follows_followed (followed_id, created_at),
    CONSTRAINT fk_follows_follower FOREIGN KEY (follower_id) REFERENCES USERS(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_follows_followed FOREIGN KEY (followed_id) REFERENCES USERS(user_id) ON DELETE CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
