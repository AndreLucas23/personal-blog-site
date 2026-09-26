USE BLOG;

INSERT INTO USERS (username, email, password_hash, is_admin)
VALUES ('admin', 'admin@gmail.com', 'admin123', 1);

INSERT INTO USERS (username, email, password_hash, is_admin)
VALUES ('user', 'user@gmail.com', 'user123', 0);

INSERT INTO ARTICLES (article_title, article_content, author_id)
VALUES ('Um breve artigo', 'Este é um artigo usado para teste de desenvolvimento', 1);

INSERT INTO ARTICLES (article_title, article_content, author_id)
VALUES ('Mais um teste', 'Como dito, essa escritura é apenas uma ferramenta de apoio', 2);

INSERT INTO ARTICLES (article_title, article_content, author_id)
VALUES ('Artigo de teste', 'Este artigo foi criado apenas para fins de teste e desenvolvimento', 2);
