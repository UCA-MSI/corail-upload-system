"""Backup pull API: staff tokens fetch DB snapshots and originals over HTTPS."""
from pathlib import PurePath

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from .backup import (
    acknowledge, backlog_status, manifest_entry, pending_originals, snapshot_db,
)
from .models import UploadImageModel


@api_view(['GET'])
@permission_classes([IsAdminUser])
def db_snapshot_view(request: Request) -> FileResponse:
    """Download a fresh, consistent snapshot of the SQLite database."""
    filename = f"corail-db-{timezone.now():%Y%m%dT%H%M%SZ}.sqlite3"
    return FileResponse(snapshot_db(), as_attachment=True, filename=filename)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def originals_manifest_view(request: Request) -> Response:
    """List every original still on the web host, with its metadata."""
    return Response([manifest_entry(upload) for upload in pending_originals()])


@api_view(['GET'])
@permission_classes([IsAdminUser])
def original_download_view(request: Request, upload_id: int) -> FileResponse:
    """Download one pending original."""
    upload = _pending_upload(upload_id)
    try:
        file = upload.original.open('rb')
    except FileNotFoundError:
        raise Http404('Original file is missing.')
    filename = PurePath(upload.original.name).name
    return FileResponse(file, as_attachment=True, filename=filename)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def original_ack_view(request: Request, upload_id: int) -> Response:
    """Delete an original once the client proves it holds an identical copy."""
    sha256 = str(request.data.get('sha256', '')).strip()
    if not sha256:
        return Response(
            {'error': 'sha256 is required.'}, status=status.HTTP_400_BAD_REQUEST
        )
    upload = _pending_upload(upload_id)
    try:
        deleted = acknowledge(upload, sha256)
    except FileNotFoundError:
        raise Http404('Original file is missing.')
    if not deleted:
        return Response(
            {'error': 'sha256 does not match; original kept.'},
            status=status.HTTP_409_CONFLICT,
        )
    return Response({'deleted': upload_id})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def backlog_status_view(request: Request) -> Response:
    """How many originals still wait to be pulled, for monitoring."""
    return Response(backlog_status())


def _pending_upload(upload_id: int) -> UploadImageModel:
    """The upload with this id if its original is still here, else 404."""
    return get_object_or_404(pending_originals(), id=upload_id)
