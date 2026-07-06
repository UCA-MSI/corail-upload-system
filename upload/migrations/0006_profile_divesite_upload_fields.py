from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_dive_sites(apps, schema_editor):
    """Create DiveSite records from existing diving_site CharField values."""
    UploadImageModel = apps.get_model('upload', 'UploadImageModel')
    DiveSite = apps.get_model('upload', 'DiveSite')
    User = apps.get_model('auth', 'User')
    admin = User.objects.filter(is_superuser=True).first()

    site_map = {}
    for img in UploadImageModel.objects.exclude(diving_site=''):
        name = img.diving_site.strip()
        if not name:
            continue
        if name not in site_map:
            site, _ = DiveSite.objects.get_or_create(
                name=name, defaults={'created_by': admin}
            )
            site_map[name] = site
        img.dive_site = site_map[name]
        img.save(update_fields=['dive_site'])


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0005_add_userdivesite'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── New standalone models ─────────────────────────────────────────
        migrations.CreateModel(
            name='DiveSite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_sites',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organisation_type', models.CharField(
                    blank=True,
                    choices=[('academia', 'Academia'), ('ngo', 'NGO / Non-profit'), ('private', 'Private')],
                    max_length=20,
                )),
                ('organisation_responsible', models.CharField(blank=True, max_length=255)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),

        # ── New fields on UploadImageModel (diving_site CharField kept for now) ──
        migrations.AddField('uploadimagemodel', 'dive_site',
            models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='images',
                to='upload.divesite',
            ),
        ),
        migrations.AddField('uploadimagemodel', 'photographer_name',
            models.CharField(blank=True, max_length=255)),
        migrations.AddField('uploadimagemodel', 'photographer_surname',
            models.CharField(blank=True, max_length=255)),
        migrations.AddField('uploadimagemodel', 'photographer_email',
            models.EmailField(blank=True, max_length=254)),
        migrations.AddField('uploadimagemodel', 'dive_master_name',
            models.CharField(blank=True, max_length=255)),
        migrations.AddField('uploadimagemodel', 'dive_master_surname',
            models.CharField(blank=True, max_length=255)),
        migrations.AddField('uploadimagemodel', 'dive_master_email',
            models.EmailField(blank=True, max_length=254)),
        migrations.AddField('uploadimagemodel', 'depth_category',
            models.CharField(
                blank=True,
                choices=[('0_5m', '0 – 5 m'), ('5_10m', '5 – 10 m'), ('gt_10m', '> 10 m'), ('custom', 'Free entry')],
                max_length=10,
            ),
        ),
        migrations.AddField('uploadimagemodel', 'depth_custom',
            models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
        migrations.AddField('uploadimagemodel', 'water_temperature',
            models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True)),
        migrations.AddField('uploadimagemodel', 'water_conditions',
            models.CharField(
                blank=True,
                choices=[('clear', 'Clear'), ('murky', 'Murky'), ('turbid', 'Turbid'), ('low_vis', 'Low visibility'), ('good_vis', 'Good visibility')],
                max_length=15,
            ),
        ),
        migrations.AddField('uploadimagemodel', 'weather_conditions',
            models.CharField(
                blank=True,
                choices=[('sunny', 'Sunny'), ('partly_cloudy', 'Partly cloudy'), ('cloudy', 'Cloudy'), ('overcast', 'Overcast'), ('rainy', 'Rainy'), ('stormy', 'Stormy')],
                max_length=15,
            ),
        ),

        # ── Data migration: populate dive_site FK from existing CharField ──
        migrations.RunPython(migrate_dive_sites, migrations.RunPython.noop),

        # ── Remove old diving_site CharField ──────────────────────────────
        migrations.RemoveField('uploadimagemodel', 'diving_site'),

        # ── Rebuild UserDiveSite with FK to DiveSite ─────────────────────
        # (dev-only data loss accepted; model was created in 0005)
        migrations.DeleteModel('UserDiveSite'),
        migrations.CreateModel(
            name='UserDiveSite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('depth', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dive_sites',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('dive_site', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_logs',
                    to='upload.divesite',
                )),
            ],
        ),
    ]
