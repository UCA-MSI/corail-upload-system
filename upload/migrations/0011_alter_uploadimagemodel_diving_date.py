from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0010_alter_divesite_latitude_alter_divesite_longitude'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadimagemodel',
            name='diving_date',
            field=models.DateField(),
        ),
    ]
