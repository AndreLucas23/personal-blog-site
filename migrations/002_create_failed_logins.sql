-- Failed login attempts, kept only for as long as they count towards the limit.

CREATE TABLE FAILED_LOGINS (
    failed_login_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_failed_logins_lookup (email, ip_address, attempted_at),
    INDEX idx_failed_logins_attempted_at (attempted_at)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
