from werkzeug.security import generate_password_hash

from repositories import article_repository, user_repository

ADMIN = {
    'username': 'Owner',
    'email': 'owner@example.com',
    'password': 'admin-password-1',
}
READER = {
    'username': 'Reader',
    'email': 'reader@example.com',
    'password': 'reader-password-1',
}


def create_user(
    username: str, email: str, password: str, is_admin: bool = False
) -> int:
    password_hash = generate_password_hash(password)
    return user_repository.create(username, email, password_hash, is_admin)


def create_article(
    author_id: int, title: str = 'Título', content: str = 'Conteúdo'
) -> int:
    return article_repository.create(title, content, author_id)


def login(client, email: str, password: str):
    return client.post('/auth/login', data={'email': email, 'password': password})
