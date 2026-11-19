-- The login accepts an email or a username, so failed attempts are kept by either one.

ALTER TABLE FAILED_LOGINS RENAME COLUMN email TO login;
