from django.db import migrations

# Placeholder rows seeded in 0009, superseded by the real coraldb catalog below.
PLACEHOLDER_DIVE_SITES = [
    'Rapua Parat / Manokwari',
    'Raja Ampat / Misool - Marine Protected Area',
    'Bali / Padangbai',
    'Bali / Nusa Penida',
    'Bali / Amed',
]

# Sourced from coraldb's diving_sites reference table (province, location, dive_site),
# deduplicated to one row per physical site — depth is tracked separately per upload/log.
DIVE_SITES = [
    ('Bali / Padangbai', 'Blue Lagoon'),
    ('Bali / Padangbai', 'Gili Tepekong'),
    ('Bali / Padangbai', 'Jepun'),
    ('Bali / Padangbai', 'Restoration'),
    ('Bali / Padangbai', 'White Sand Beach'),
    ('Papua Barat / Manokwari', 'Korepyar'),
    ('Papua Barat / Manokwari', 'Kwawi'),
    ('Papua Barat / Manokwari', 'Manggewa'),
    ('Papua Barat / Manokwari', 'Warenseki'),
    ('Papua Barat / Raja Ampat - Misool', 'Kalig_Housereef'),
    ('Papua Barat / Raja Ampat - Misool', 'MR_BlueHole'),
    ('Papua Barat / Raja Ampat - Misool', 'MR_Housereef'),
    ('Papua Barat / Raja Ampat - Misool', 'Rep_Kima'),
    ('Papua Barat / Raja Ampat - Misool', 'SW_Batbitim'),
]


def seed_coraldb_dive_sites(apps, schema_editor):
    """Replace the placeholder dive sites with coraldb's real site catalog."""
    DiveSite = apps.get_model('upload', 'DiveSite')
    DiveSite.objects.filter(name__in=PLACEHOLDER_DIVE_SITES).delete()
    for region, name in DIVE_SITES:
        DiveSite.objects.get_or_create(
            name=name,
            defaults={'country': 'Indonesia', 'region': region},
        )


def restore_placeholder_dive_sites(apps, schema_editor):
    """Reverse the migration by removing the coraldb sites and restoring placeholders."""
    DiveSite = apps.get_model('upload', 'DiveSite')
    DiveSite.objects.filter(name__in=[name for _, name in DIVE_SITES]).delete()
    for site_name in PLACEHOLDER_DIVE_SITES:
        DiveSite.objects.get_or_create(
            name=site_name,
            defaults={'country': 'Indonesia', 'region': site_name},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0012_uploadimagemodel_dive_time'),
    ]

    operations = [
        migrations.RunPython(seed_coraldb_dive_sites, restore_placeholder_dive_sites),
    ]
