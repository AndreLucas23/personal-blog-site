-- What members tell about themselves on their profile page.

ALTER TABLE USERS
    ADD COLUMN headline VARCHAR(120) NULL AFTER display_name,
    ADD COLUMN bio VARCHAR(500) NULL AFTER headline,
    ADD COLUMN location VARCHAR(80) NULL AFTER bio,
    ADD COLUMN website VARCHAR(200) NULL AFTER location;
