import io

import pytest
from PIL import Image

import uploads
from helpers import create_article
from repositories import article_repository


@pytest.fixture(autouse=True)
def upload_dir(app, tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, 'UPLOAD_DIR', tmp_path)
    return tmp_path


def image_bytes(image_format='PNG', size=(1600, 1200)) -> bytes:
    buffer = io.BytesIO()
    Image.new('RGB', size, 'blue').save(buffer, image_format)
    return buffer.getvalue()


def upload(client, article_id: int, data: bytes, filename: str = 'capa.png'):
    return client.put(
        f'/api/articles/{article_id}/cover',
        data={'cover': (io.BytesIO(data), filename)},
        content_type='multipart/form-data',
    )


def stored_file(upload_dir, cover_url: str):
    return upload_dir / cover_url.rsplit('/', 1)[1]


def test_the_author_uploads_a_cover_in_the_size_of_covers(reader_client, reader_id, upload_dir):
    article_id = create_article(reader_id)

    response = upload(reader_client, article_id, image_bytes())

    assert response.status_code == 200
    cover_url = response.get_json()['cover_url']
    assert cover_url.startswith('/media/') and cover_url.endswith('.webp')
    with Image.open(stored_file(upload_dir, cover_url)) as saved:
        assert saved.format == 'WEBP'
        assert saved.size == uploads.COVER_SIZE


def test_the_article_carries_its_cover(client, reader_client, reader_id):
    article_id = create_article(reader_id)
    cover_url = upload(reader_client, article_id, image_bytes()).get_json()['cover_url']

    assert client.get(f'/api/articles/{article_id}').get_json()['cover_url'] == cover_url


def test_articles_without_a_cover_have_none(client, reader_id):
    article_id = create_article(reader_id)

    assert client.get(f'/api/articles/{article_id}').get_json()['cover_url'] is None


def test_a_new_cover_replaces_the_file_of_the_old_one(reader_client, reader_id, upload_dir):
    article_id = create_article(reader_id)
    first = upload(reader_client, article_id, image_bytes()).get_json()['cover_url']

    second = upload(reader_client, article_id, image_bytes('JPEG'), 'capa.jpg').get_json()['cover_url']

    assert second != first
    assert not stored_file(upload_dir, first).exists()
    assert stored_file(upload_dir, second).exists()


def test_removing_the_cover_removes_its_file(reader_client, reader_id, upload_dir):
    article_id = create_article(reader_id)
    cover_url = upload(reader_client, article_id, image_bytes()).get_json()['cover_url']

    response = reader_client.delete(f'/api/articles/{article_id}/cover')

    assert response.status_code == 200
    assert response.get_json()['cover_url'] is None
    assert not stored_file(upload_dir, cover_url).exists()


def test_deleting_the_article_removes_its_cover(reader_client, reader_id, upload_dir):
    article_id = create_article(reader_id)
    cover_url = upload(reader_client, article_id, image_bytes()).get_json()['cover_url']

    reader_client.delete(f'/api/articles/{article_id}')

    assert not stored_file(upload_dir, cover_url).exists()


def test_drafts_take_a_cover_too(reader_client, reader_id):
    article_id = create_article(reader_id, status='draft')

    assert upload(reader_client, article_id, image_bytes()).status_code == 200


def test_only_the_author_changes_the_cover(admin_client, reader_id, upload_dir):
    article_id = create_article(reader_id)

    uploaded = upload(admin_client, article_id, image_bytes())
    removed = admin_client.delete(f'/api/articles/{article_id}/cover')

    assert uploaded.status_code == 403 and removed.status_code == 403
    assert list(upload_dir.iterdir()) == []


def test_the_cover_of_another_members_draft_is_not_found(admin_client, reader_id):
    article_id = create_article(reader_id, status='draft')

    assert upload(admin_client, article_id, image_bytes()).status_code == 404


def test_changing_a_cover_needs_a_session(client, reader_id):
    article_id = create_article(reader_id)

    assert upload(client, article_id, image_bytes()).status_code == 401


@pytest.mark.parametrize(('data', 'code'), [
    (b'not an image', uploads.IMAGE_INVALID),
    (image_bytes('GIF'), uploads.IMAGE_FORMAT),
])
def test_files_that_are_not_covers_are_refused(reader_client, reader_id, data, code):
    article_id = create_article(reader_id)

    response = upload(reader_client, article_id, data)

    assert response.status_code == 400
    assert response.get_json()['errors'] == {'cover': code}


def test_a_request_without_the_file_is_refused(reader_client, reader_id):
    article_id = create_article(reader_id)

    response = reader_client.put(f'/api/articles/{article_id}/cover', data={}, content_type='multipart/form-data')

    assert response.status_code == 400
    assert response.get_json()['errors'] == {'cover': uploads.IMAGE_MISSING}


def test_a_cover_for_an_article_removed_meanwhile_leaves_no_file(reader_client, reader_id, upload_dir, monkeypatch):
    article_id = create_article(reader_id)
    save_cover = uploads.save_cover

    def removed_while_uploading(*args):
        name = save_cover(*args)
        article_repository.delete(article_id)
        return name

    monkeypatch.setattr(uploads, 'save_cover', removed_while_uploading)

    response = upload(reader_client, article_id, image_bytes())

    assert response.status_code == 404
    assert list(upload_dir.iterdir()) == []
