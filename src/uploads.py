"""Checking, resizing and storing the images members upload."""
import io
import logging
import re
import secrets
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = frozenset({'JPEG', 'PNG', 'WEBP'})
MAX_IMAGE_BYTES = 5 * 1024 * 1024
# The whole request may carry a little more than the file, such as the multipart headers.
MAX_REQUEST_BYTES = 6 * 1024 * 1024
# Decoding is what costs memory, so huge dimensions are refused before it.
MAX_IMAGE_PIXELS = 40_000_000
AVATAR_SIZE = 400
FILE_NAME = re.compile(r'[0-9a-f]{32}\.webp')

IMAGE_MISSING = 'image_missing'
IMAGE_INVALID = 'image_invalid'
IMAGE_FORMAT = 'image_format'
IMAGE_TOO_LARGE = 'image_too_large'

logger = logging.getLogger(__name__)


class ImageError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def is_upload_name(name: str) -> bool:
    # fullmatch, because $ in match() also accepts a trailing newline.
    return bool(FILE_NAME.fullmatch(name))


def _mode_for(image: Image.Image) -> str:
    has_alpha = 'A' in image.getbands() or 'transparency' in image.info
    return 'RGBA' if has_alpha else 'RGB'


def save_avatar(stream: BinaryIO, upload_dir: Path) -> str:
    """Store a square WebP version of the image and return its file name.

    Raises ImageError with a code when the file is not an image the site accepts.
    """
    return _save_fitted(stream, upload_dir, (AVATAR_SIZE, AVATAR_SIZE))


def _save_fitted(stream: BinaryIO, upload_dir: Path, size: tuple[int, int]) -> str:
    """Store the image cropped to the shape of size and scaled to it, as WebP."""
    data = stream.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ImageError(IMAGE_TOO_LARGE)

    try:
        with Image.open(io.BytesIO(data)) as original:
            if original.format not in ALLOWED_FORMATS:
                raise ImageError(IMAGE_FORMAT)
            if original.width * original.height > MAX_IMAGE_PIXELS:
                raise ImageError(IMAGE_TOO_LARGE)

            # Phones store photos sideways with a rotation tag that browsers would ignore here.
            upright = ImageOps.exif_transpose(original)
            fitted = ImageOps.fit(
                upright.convert(_mode_for(upright)),
                size,
                Image.Resampling.LANCZOS,
            )
    except ImageError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError) as error:
        raise ImageError(IMAGE_INVALID) from error
    except Exception as error:
        # Broken or crafted files make decoders fail in many ways (EOFError,
        # SyntaxError, struct.error...). They are the sender's problem, not a 500,
        # but the log keeps them visible in case one is a bug.
        logger.warning('Could not decode an uploaded image', exc_info=True)
        raise ImageError(IMAGE_INVALID) from error

    # A new random name per upload, so browsers can cache each file forever.
    name = f'{secrets.token_hex(16)}.webp'
    upload_dir.mkdir(parents=True, exist_ok=True)
    fitted.save(upload_dir / name, 'WEBP', quality=85)
    return name


def delete_upload(name: str | None, upload_dir: Path) -> None:
    if not name or not is_upload_name(name):
        return

    try:
        (upload_dir / name).unlink()
    except FileNotFoundError:
        return
    except OSError:
        logger.warning('Could not delete the upload %s', name, exc_info=True)
