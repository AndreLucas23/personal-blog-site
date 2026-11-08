import mysql.connector
import pytest

from db import get_db_connection
from helpers import create_article
from repositories import like_repository


@pytest.fixture
def article_id(admin_id):
    return create_article(admin_id)


def likes_url(article_id: int) -> str:
    return f'/api/articles/{article_id}/likes'


def count_likes(article_id: int) -> int:
    return like_repository.count(article_id)


def run_sql(statement: str, params: tuple) -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(statement, params)
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def test_like_returns_the_new_state_and_count(reader_client, article_id):
    response = reader_client.post(likes_url(article_id))

    assert response.status_code == 200
    assert response.get_json() == {'liked': True, 'likes': 1}


def test_liking_twice_keeps_a_single_like(reader_client, article_id):
    reader_client.post(likes_url(article_id))

    response = reader_client.post(likes_url(article_id))

    assert response.get_json() == {'liked': True, 'likes': 1}
    assert count_likes(article_id) == 1


def test_unlike_removes_only_the_viewer_like(admin_client, reader_client, article_id):
    admin_client.post(likes_url(article_id))
    reader_client.post(likes_url(article_id))

    response = reader_client.delete(likes_url(article_id))

    assert response.get_json() == {'liked': False, 'likes': 1}
    assert reader_client.delete(likes_url(article_id)).status_code == 200
    assert count_likes(article_id) == 1


def test_articles_report_whether_the_viewer_liked_them(
    client, admin_client, reader_client, article_id
):
    reader_client.post(likes_url(article_id))

    def liked_by(some_client):
        return some_client.get(f'/api/articles/id/{article_id}').get_json()[0]

    assert liked_by(reader_client)['liked'] is True
    assert liked_by(admin_client)['liked'] is False
    assert liked_by(client)['liked'] is False
    assert liked_by(client)['likes'] == 1


def test_article_page_shows_the_viewer_like(reader_client, article_id):
    reader_client.post(likes_url(article_id))

    page = reader_client.get(f'/open/{article_id}').get_data(as_text=True)

    assert 'aria-pressed="true"' in page


def test_liking_a_missing_article_answers_404(reader_client):
    assert reader_client.post(likes_url(999)).status_code == 404
    assert reader_client.delete(likes_url(999)).status_code == 404


def test_database_rejects_a_duplicated_like(reader_id, article_id):
    statement = 'INSERT INTO LIKES (user_id, article_id) VALUES (%s, %s)'
    run_sql(statement, (reader_id, article_id))

    with pytest.raises(mysql.connector.IntegrityError):
        run_sql(statement, (reader_id, article_id))


def test_likes_are_removed_with_their_article(admin_client, reader_client, article_id):
    reader_client.post(likes_url(article_id))

    admin_client.delete(f'/api/articles/{article_id}')

    assert count_likes(article_id) == 0


def test_likes_are_removed_with_their_user(reader_client, reader_id, article_id):
    reader_client.post(likes_url(article_id))

    run_sql('DELETE FROM USERS WHERE user_id = %s', (reader_id,))

    assert count_likes(article_id) == 0
