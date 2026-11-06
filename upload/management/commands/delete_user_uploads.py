"""Delete every upload of one user, together with its stored files."""
from argparse import ArgumentParser

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db.models import FileField, QuerySet

from upload.models import UploadImageModel

FILE_FIELDS = [
    field.name
    for field in UploadImageModel._meta.fields
    if isinstance(field, FileField)
]


class Command(BaseCommand):
    help = "Delete all uploads of a user and their files. Cannot be undone."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("username")
        parser.add_argument(
            "--dry-run", action="store_true", help="Only report what would go."
        )

    def handle(self, *args, username: str, dry_run: bool, **options) -> None:
        if not User.objects.filter(username=username).exists():
            raise CommandError(f"No user named {username!r}")
        uploads = UploadImageModel.objects.filter(user__username=username)
        if dry_run:
            self.stdout.write(f"Would delete {uploads.count()} uploads of {username}")
            return
        self.stdout.write(f"Deleted {delete_uploads(uploads)} uploads of {username}")


def delete_uploads(uploads: QuerySet[UploadImageModel]) -> int:
    """Delete the rows first, then their files, so no row points to a lost file."""
    files = [getattr(upload, name) for upload in uploads for name in FILE_FIELDS]
    count, _ = uploads.delete()
    for file in files:
        file.delete(save=False)
    return count
