-- The file name of the member's photo in the uploads volume, or NULL for the initials.

ALTER TABLE USERS ADD COLUMN avatar_path VARCHAR(64) NULL AFTER website;
