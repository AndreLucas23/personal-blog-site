USE BLOG;

INSERT INTO USERS (username, email, password_hash, is_admin)
VALUES (
    'admin',
    'admin@gmail.com',
    'scrypt:32768:8:1$9unkRsxUBLqivnSE$821e7a7568be252bce23927f222f78776e27fe424e99e408309db4e1bca2c664675d026dadc264aca56f7c4781d7ae496f34b34056e8888340f303eb79540d48',
    1
);

INSERT INTO USERS (username, email, password_hash, is_admin)
VALUES (
    'user',
    'user@gmail.com',
    'scrypt:32768:8:1$mymzIyGdmMwXjH0i$402eefbbc34b34476da14c9cc8047a5ada7d91debe42e17dc3780dcd092427ce63f9ed9d60f53dc335a9364e511030d41c366a3b4464a906aa9c1351a8e73104',
    0
);

INSERT INTO ARTICLES (article_title, article_content, author_id)
VALUES (
    'Um breve artigo',
    'Este é um artigo usado para teste de desenvolvimento',
    1
);

INSERT INTO ARTICLES (article_title, article_content, author_id)
VALUES (
    'Mais um teste',
    'Como dito, essa escritura é apenas uma ferramenta de apoio',
    2
);

INSERT INTO ARTICLES (article_title, article_content, author_id)
VALUES (
    'Artigo de teste',
    'Este artigo é apenas para fins de teste e desenvolvimento',
    2
);
