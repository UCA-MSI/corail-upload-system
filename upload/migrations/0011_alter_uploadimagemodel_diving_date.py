from django.db import migrations, models


def backfill_diving_date(apps, schema_editor):
    """Fill missing diving_date with the row's upload date so the NOT NULL
    constraint below doesn't fail on images uploaded before this field was
    mandatory."""
    UploadImageModel = apps.get_model('upload', 'UploadImageModel')
    for image in UploadImageModel.objects.filter(diving_date__isnull=True):
        image.diving_date = image.uploaded_at.date()
        image.save(update_fields=['diving_date'])


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0010_alter_divesite_latitude_alter_divesite_longitude'),
    ]

    operations = [
        migrations.RunPython(backfill_diving_date, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='uploadimagemodel',
            name='diving_date',
            field=models.DateField(),
        ),
    ]
