-- Names become display names, and every member gets a unique username for the
-- profile address. Existing names turn into usernames: lowercase, without accents,
-- with an underscore for anything that is not a letter or a digit. A username that
-- ends up too short, reserved or taken becomes user_<id>.

ALTER TABLE USERS ADD COLUMN display_name VARCHAR(50) NULL AFTER username;

UPDATE USERS SET display_name = username;

UPDATE USERS SET username = LOWER(username);
UPDATE USERS SET username = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(username, 'á', 'a'), 'à', 'a'), 'â', 'a'), 'ã', 'a'), 'ä', 'a');
UPDATE USERS SET username = REPLACE(REPLACE(REPLACE(REPLACE(username, 'é', 'e'), 'è', 'e'), 'ê', 'e'), 'ë', 'e');
UPDATE USERS SET username = REPLACE(REPLACE(REPLACE(REPLACE(username, 'í', 'i'), 'ì', 'i'), 'î', 'i'), 'ï', 'i');
UPDATE USERS SET username = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(username, 'ó', 'o'), 'ò', 'o'), 'ô', 'o'), 'õ', 'o'), 'ö', 'o');
UPDATE USERS SET username = REPLACE(REPLACE(REPLACE(REPLACE(username, 'ú', 'u'), 'ù', 'u'), 'û', 'u'), 'ü', 'u');
UPDATE USERS SET username = REPLACE(REPLACE(username, 'ç', 'c'), 'ñ', 'n');
UPDATE USERS SET username = REGEXP_REPLACE(username, '[^a-z0-9_]+', '_');
UPDATE USERS SET username = LEFT(TRIM(BOTH '_' FROM username), 30);
UPDATE USERS SET username = TRIM(TRAILING '_' FROM username);

-- Keep in step with RESERVED_USERNAMES in src/user_validation.py.
UPDATE USERS SET username = CONCAT('user_', user_id)
WHERE CHAR_LENGTH(username) < 3
    OR username IN ('me', 'admin', 'moderacao', 'socialblog', 'suporte');

-- In each group of equal usernames the account whose username is its own
-- user_<id> keeps it, since that one cannot change, and so does the oldest
-- account otherwise. The others become user_<id>, which can only clash with a
-- name that was already user_<another id>, so each pass settles one more link
-- of such a chain.
UPDATE USERS u
JOIN (
    SELECT user_id FROM (
        SELECT user_id, ROW_NUMBER() OVER (
            PARTITION BY username
            ORDER BY username = CONCAT('user_', user_id) DESC, user_id
        ) AS position
        FROM USERS
    ) ranked
    WHERE position > 1
) taken ON taken.user_id = u.user_id
SET u.username = CONCAT('user_', u.user_id);

UPDATE USERS u
JOIN (
    SELECT user_id FROM (
        SELECT user_id, ROW_NUMBER() OVER (
            PARTITION BY username
            ORDER BY username = CONCAT('user_', user_id) DESC, user_id
        ) AS position
        FROM USERS
    ) ranked
    WHERE position > 1
) taken ON taken.user_id = u.user_id
SET u.username = CONCAT('user_', u.user_id);

UPDATE USERS u
JOIN (
    SELECT user_id FROM (
        SELECT user_id, ROW_NUMBER() OVER (
            PARTITION BY username
            ORDER BY username = CONCAT('user_', user_id) DESC, user_id
        ) AS position
        FROM USERS
    ) ranked
    WHERE position > 1
) taken ON taken.user_id = u.user_id
SET u.username = CONCAT('user_', u.user_id);

ALTER TABLE USERS
    MODIFY username VARCHAR(30) NOT NULL,
    MODIFY display_name VARCHAR(50) NOT NULL,
    ADD CONSTRAINT uq_users_username UNIQUE (username);
