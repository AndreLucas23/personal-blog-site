import io

import pytest
from PIL import Image

import uploads
from repositories import user_repository

AVATAR_URL = '/api/users/me/avatar'


@pytest.fixture(autouse=True)
def upload_dir(app, tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, 'UPLOAD_DIR', tmp_path)
    return tmp_path


def image_bytes(image_format='PNG', size=(800, 600), color='red', mode='RGB', **save_options) -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, size, color).save(buffer, image_format, **save_options)
    return buffer.getvalue()


def upload(client, data: bytes, filename: str = 'avatar.png'):
    return client.put(
        AVATAR_URL,
        data={'avatar': (io.BytesIO(data), filename)},
        content_type='multipart/form-data',
    )


def stored_file(upload_dir, avatar_url: str):
    return upload_dir / avatar_url.rsplit('/', 1)[1]


def test_upload_stores_a_square_webp(reader_client, upload_dir):
    response = upload(reader_client, image_bytes())

    assert response.status_code == 200
    avatar_url = response.get_json()['avatar_url']
    assert avatar_url.startswith('/media/') and avatar_url.endswith('.webp')
    with Image.open(stored_file(upload_dir, avatar_url)) as saved:
        assert saved.format == 'WEBP'
        assert saved.size == (uploads.AVATAR_SIZE, uploads.AVATAR_SIZE)


def test_profiles_show_the_avatar(client, reader_client):
    avatar_url = upload(reader_client, image_bytes()).get_json()['avatar_url']

    assert reader_client.get('/api/users/me').get_json()['avatar_url'] == avatar_url
    assert client.get('/api/users/reader').get_json()['avatar_url'] == avatar_url


def test_jpeg_and_webp_are_accepted(reader_client):
    assert upload(reader_client, image_bytes('JPEG'), 'a.jpg').status_code == 200
    assert upload(reader_client, image_bytes('WEBP'), 'a.webp').status_code == 200


def test_transparency_is_kept(reader_client, upload_dir):
    data = image_bytes(mode='RGBA', color=(255, 0, 0, 0))

    avatar_url = upload(reader_client, data).get_json()['avatar_url']

    with Image.open(stored_file(upload_dir, avatar_url)) as saved:
        assert saved.mode == 'RGBA'


def test_photos_are_turned_upright(reader_client, upload_dir):
    # Stored sideways: left half red, right half blue, with the "rotate 90° clockwise" tag.
    photo = Image.new('RGB', (200, 100), 'blue')
    photo.paste('red', (0, 0, 100, 100))
    exif = photo.getexif()
    exif[0x0112] = 6
    buffer = io.BytesIO()
    photo.save(buffer, 'JPEG', exif=exif.tobytes(), quality=95)

    avatar_url = upload(reader_client, buffer.getvalue(), 'photo.jpg').get_json()['avatar_url']

    with Image.open(stored_file(upload_dir, avatar_url)) as saved:
        top = saved.convert('RGB').getpixel((200, 40))
        bottom = saved.convert('RGB').getpixel((200, 360))
    assert top[0] > 200 and top[2] < 60
    assert bottom[2] > 200 and bottom[0] < 60


@pytest.mark.parametrize(('data', 'filename', 'code'), [
    (image_bytes('GIF'), 'a.gif', uploads.IMAGE_FORMAT),
    (b'just some text', 'a.png', uploads.IMAGE_INVALID),
    (image_bytes()[:120], 'a.png', uploads.IMAGE_INVALID),
    (image_bytes(mode='1', size=(9000, 9000), color=0), 'big.png', uploads.IMAGE_TOO_LARGE),
    (b'\0' * (uploads.MAX_IMAGE_BYTES + 1), 'heavy.png', uploads.IMAGE_TOO_LARGE),
])
def test_files_the_site_cannot_use_are_rejected(reader_client, upload_dir, data, filename, code):
    response = upload(reader_client, data, filename)

    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid image', 'errors': {'avatar': code}}
    assert list(upload_dir.iterdir()) == []
    assert user_repository.get_by_username('reader')['avatar_path'] is None


def test_request_larger_than_the_limit_answers_413(reader_client):
    response = upload(reader_client, b'\0' * (uploads.MAX_REQUEST_BYTES + 1))

    assert response.status_code == 413
    assert response.get_json() == {'message': 'Request too large'}


def test_missing_file_is_reported(reader_client):
    response = reader_client.put(AVATAR_URL, data={}, content_type='multipart/form-data')

    assert response.status_code == 400
    assert response.get_json()['errors'] == {'avatar': uploads.IMAGE_MISSING}


def test_a_new_avatar_replaces_and_deletes_the_old_file(reader_client, upload_dir):
    first = upload(reader_client, image_bytes(color='red')).get_json()['avatar_url']
    second = upload(reader_client, image_bytes(color='green')).get_json()['avatar_url']

    assert first != second
    assert not stored_file(upload_dir, first).exists()
    assert stored_file(upload_dir, second).exists()


def test_removing_the_avatar_deletes_the_file(reader_client, upload_dir):
    avatar_url = upload(reader_client, image_bytes()).get_json()['avatar_url']

    response = reader_client.delete(AVATAR_URL)

    assert response.status_code == 200
    assert response.get_json() == {'avatar_url': None}
    assert not stored_file(upload_dir, avatar_url).exists()
    assert reader_client.get('/api/users/me').get_json()['avatar_url'] is None


def test_avatar_changes_need_a_session(client):
    assert upload(client, image_bytes()).status_code == 401
    assert client.delete(AVATAR_URL).status_code == 401


def test_media_serves_uploads_with_long_cache(client, reader_client):
    avatar_url = upload(reader_client, image_bytes()).get_json()['avatar_url']

    response = client.get(avatar_url)

    assert response.status_code == 200
    assert response.mimetype == 'image/webp'
    cache = response.headers['Cache-Control']
    assert 'max-age=31536000' in cache
    assert 'immutable' in cache


@pytest.mark.parametrize('path', [
    '/media/' + 'a' * 32 + '.webp',
    '/media/..%2F..%2Fetc%2Fpasswd',
    '/media/avatar.png',
    '/media/' + 'A' * 32 + '.webp',
])
def test_media_answers_404_for_anything_else(client, path):
    assert client.get(path).status_code == 404


def test_delete_upload_ignores_missing_and_foreign_names(tmp_path):
    outside = tmp_path / 'keep.txt'
    outside.write_text('x')

    uploads.delete_upload('a' * 32 + '.webp', tmp_path)
    uploads.delete_upload('keep.txt', tmp_path)
    uploads.delete_upload(None, tmp_path)

    assert outside.exists()


@pytest.mark.parametrize('failure', [EOFError, SyntaxError, IndexError])
def test_any_decoding_failure_reads_as_an_invalid_image(reader_client, monkeypatch, failure):
    def broken_convert(self, *args, **kwargs):
        raise failure('broken file')

    monkeypatch.setattr(Image.Image, 'convert', broken_convert)

    response = upload(reader_client, image_bytes())

    assert response.status_code == 400
    assert response.get_json()['errors'] == {'avatar': uploads.IMAGE_INVALID}


def test_upload_names_must_match_entirely():
    name = 'a' * 32 + '.webp'

    assert uploads.is_upload_name(name)
    assert not uploads.is_upload_name(name + '\n')
    assert not uploads.is_upload_name('x' + name)
