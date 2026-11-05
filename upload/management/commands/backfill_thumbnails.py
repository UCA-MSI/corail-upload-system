"""Turn uploads made before thumbnails existed into original + thumbnail pairs."""
from django.core.management.base import BaseCommand

from upload.models import UploadImageModel
from upload.thumbnails import ThumbnailError, make_thumbnail


class Command(BaseCommand):
    help = (
        "For uploads without an original, keep the current file as the original "
        "and replace `image` with a thumbnail. Safe to run more than once."
    )

    def handle(self, *args, **options) -> None:
        # list(): SQLite gives no isolation when writing to the table being iterated.
        pending = list(UploadImageModel.objects.filter(original=''))
        failed = 0
        for upload in pending:
            try:
                backfill_thumbnail(upload)
            except (ThumbnailError, FileNotFoundError) as exc:
                failed += 1
                self.stderr.write(f"Upload {upload.id} ({upload.image.name}): {exc}")
        self.stdout.write(f"{len(pending) - failed} backfilled, {failed} failed")


def backfill_thumbnail(upload: UploadImageModel) -> None:
    """Keep the current file as the original and point `image` to a thumbnail."""
    with upload.image.open('rb') as file:
        thumbnail = make_thumbnail(file, upload.image.name)
    upload.original.name = upload.image.name
    upload.image.save(thumbnail.name, thumbnail, save=False)
    upload.save(update_fields=['image', 'original'])
