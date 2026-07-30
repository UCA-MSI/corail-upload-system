from django.db import migrations

DIVE_SITES = [
    'Rapua Parat / Manokwari',
    'Raja Ampat / Misool - Marine Protected Area',
    'Bali / Padangbai',
    'Bali / Nusa Penida',
    'Bali / Amed',
]


def seed_dive_sites(apps, schema_editor):
    """Populate the initial set of Indonesian dive site regions."""
    DiveSite = apps.get_model('upload', 'DiveSite')
    for site_name in DIVE_SITES:
        DiveSite.objects.get_or_create(
            name=site_name,
            defaults={'country': 'Indonesia', 'region': site_name},
        )


def remove_dive_sites(apps, schema_editor):
    """Reverse the seeding by deleting the seeded dive sites."""
    DiveSite = apps.get_model('upload', 'DiveSite')
    DiveSite.objects.filter(name__in=DIVE_SITES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0008_divesite_country_divesite_region'),
    ]

    operations = [
        migrations.RunPython(seed_dive_sites, remove_dive_sites),
    ]
