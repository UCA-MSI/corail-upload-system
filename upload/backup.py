"""Database snapshots and pending originals, for the backup pull API."""
import hashlib
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime
from pathlib import PurePath
from typing import IO, Any

from django.db import connection
from django.db.models import QuerySet
from django.db.models.fields.files import FieldFile

from .models import UploadImageModel

HASH_CHUNK_SIZE = 1024 * 1024


def snapshot_db() -> IO[bytes]:
    """Copy the live SQLite DB into a temp file that is deleted when closed.

    Uses SQLite's online backup, which is consistent even while the site
    writes; copying the file itself is not.
    """
    snapshot = tempfile.NamedTemporaryFile(suffix='.sqlite3')
    connection.ensure_connection()
    with closing(sqlite3.connect(snapshot.name)) as target:
        connection.connection.backup(target)
    return snapshot


def pending_originals() -> QuerySet[UploadImageModel]:
    """Uploads whose original is still on the web host, oldest first."""
    return (
        UploadImageModel.objects.exclude(original='')
        .select_related('dive_site', 'user')
        .order_by('id')
    )


def manifest_entry(upload: UploadImageModel) -> dict[str, Any]:
    """What a pull client needs to fetch one original and keep its metadata."""
    site = upload.dive_site
    photographer = f'{upload.photographer_name} {upload.photographer_surname}'
    return {
        'id': upload.id,
        'session_id': str(upload.session_id),
        'filename': PurePath(upload.original.name).name,
        'size': _size_or_none(upload.original),
        'uploaded_at': upload.uploaded_at,
        'uploader': upload.user.username,
        'diving_date': upload.diving_date,
        'dive_time': upload.dive_time,
        'site_id': site.site_id if site else '',
        'site_name': site.name if site else '',
        'depth_category': upload.depth_category,
        'depth_custom': upload.depth_custom,
        'water_temperature': upload.water_temperature,
        'water_conditions': upload.water_conditions,
        'weather_conditions': upload.weather_conditions,
        'description': upload.description,
        'photographer': photographer.strip(),
    }


def acknowledge(upload: UploadImageModel, sha256: str) -> bool:
    """Delete the original if the client's checksum proves it has a full copy."""
    if file_sha256(upload.original) != sha256.lower():
        return False
    upload.original.delete(save=False)
    upload.save(update_fields=['original'])
    return True


def backlog_status() -> dict[str, int | datetime | None]:
    """How many originals still wait to be pulled, and since when."""
    pending = pending_originals()
    oldest = pending.first()
    return {
        'pending': pending.count(),
        'oldest_uploaded_at': oldest.uploaded_at if oldest else None,
    }


def file_sha256(file: FieldFile) -> str:
    """Hex SHA-256 of a stored file, read in chunks to keep memory flat."""
    digest = hashlib.sha256()
    with file.open('rb') as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_SIZE), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _size_or_none(file: FieldFile) -> int | None:
    """File size in bytes, or None if the file is missing from storage."""
    try:
        return file.size
    except FileNotFoundError:
        return None
