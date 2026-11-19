from werkzeug.security import generate_password_hash

from repositories import article_repository, user_repository

ADMIN = {
    'display_name': 'Owner',
    'username': 'owner',
    'email': 'owner@example.com',
    'password': 'admin-password-1',
}
READER = {
    'display_name': 'Reader',
    'username': 'reader',
    'email': 'reader@example.com',
    'password': 'reader-password-1',
}


def create_user(
    display_name: str,
    username: str,
    email: str,
    password: str,
    is_admin: bool = False,
) -> int:
    password_hash = generate_password_hash(password)
    return user_repository.create(display_name, username, email, password_hash, is_admin)


def create_article(
    author_id: int,
    title: str = 'Título',
    content: str = 'Conteúdo',
    summary: str | None = None,
    status: str = 'published',
) -> int:
    return article_repository.create(title, summary, content, author_id, status)


def login(client, login_name: str, password: str):
    return client.post('/auth/login', data={'login': login_name, 'password': password})
