"""Thumbnail generation for uploaded dive photos."""
import io
from pathlib import Path
from typing import IO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

register_heif_opener()

THUMBNAIL_SIZE = (400, 400)
THUMBNAIL_QUALITY = 85
# Errors Pillow raises for files it cannot decode (corrupt, unsupported, too large).
DECODE_ERRORS = (
    UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError
)


class ThumbnailError(ValueError):
    """Raised when an uploaded file cannot be decoded as an image."""


def make_thumbnail(file: IO[bytes], name: str) -> ContentFile:
    """Return an upright JPEG thumbnail of `file`, without EXIF/GPS metadata.

    The file position is reset afterwards, so the original can still be saved.
    """
    file.seek(0)
    try:
        with Image.open(file) as img:
            img.draft("RGB", THUMBNAIL_SIZE)  # JPEG only: decode at reduced scale
            thumbnail = ImageOps.exif_transpose(img).convert("RGB")
            thumbnail.thumbnail(THUMBNAIL_SIZE)
            buffer = io.BytesIO()
            thumbnail.save(buffer, format="JPEG", quality=THUMBNAIL_QUALITY)
    except DECODE_ERRORS as exc:
        raise ThumbnailError(
            f"Could not read {Path(name).name} as an image. "
            "Please upload JPEG, PNG, TIFF, WebP or HEIC photos."
        ) from exc
    finally:
        file.seek(0)
    return ContentFile(buffer.getvalue(), name=f"{Path(name).stem}.jpg")
