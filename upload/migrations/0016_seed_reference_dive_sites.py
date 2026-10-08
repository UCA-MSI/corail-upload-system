from decimal import Decimal

from django.db import migrations

SOURCE_VERSION = '0.3.0'

# Copied verbatim from coraldb databases/dive_sites_0.3.0.parquet as
# (site_id, dive_site_website, country, 'province / location', depth, lat, lon).
# Reference sites are read-only: never edit these rows, import a new coraldb
# version instead.
REFERENCE_DIVE_SITES = [
    ('1.1', 'Kalig House Reef (1.1)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.226244, 130.503402),
    ('1.2', 'Kalig House Reef (1.2)',
     'Indonesia', 'Raja Ampat / Misool', 10,
     -2.226019, 130.503517),
    ('1.3', 'Kalig House Reef restoration (1.3)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.226145, 130.503222),
    ('2.1', 'Rep Kima (2.1)',
     'Indonesia', 'Raja Ampat / Misool', 10,
     -2.21927, 130.573054),
    ('3.1', 'South-West Batbitim (3.1)',
     'Indonesia', 'Raja Ampat / Misool', 10,
     -2.249537, 130.544385),
    ('3.2', 'South-West Batbitim (3.2)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.249646, 130.544259),
    ('4.1', 'Misool Resort House Reef GR1 (4.1)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.245249, 130.557039),
    ('4.2', 'Misool Resort House Reef GR2 (4.2)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.245008, 130.557023),
    ('4.3', 'Misool Resort House Reef GR3 (4.3)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.244826, 130.557017),
    ('4.4', 'Misool Resort House Reef GR4 (4.4)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.244622, 130.557023),
    ('4.5', 'Misool Resort House Reef GR1 (4.5)',
     'Indonesia', 'Raja Ampat / Misool', 10,
     -2.245276, 130.556996),
    ('4.6', 'Misool Resort House Reef GR2 (4.6)',
     'Indonesia', 'Raja Ampat / Misool', 10,
     -2.245051, 130.557028),
    ('4.7', 'Misool Resort House Reef GR3 (4.7)',
     'Indonesia', 'Raja Ampat / Misool', 10,
     -2.244842, 130.557082),
    ('4.8', 'Misool Resort House Reef GR4 (4.8)',
     'Indonesia', 'Raja Ampat / Misool', 10,
     -2.244612, 130.557093),
    ('4.9', 'Misool Resort House Reef restoration (4.9)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.245657, 130.556958),
    ('4.10', 'Misool Resort House Reef (4.10)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.245871, 130.556964),
    ('4.11', 'Misool Resort House Reef (4.11)',
     'Indonesia', 'Raja Ampat / Misool', 10,
     -2.245957, 130.557039),
    ('5.1', 'Misool Resort Blue Hole (5.1)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.246348, 130.554689),
    ('5.2', 'Misool Resort Blue Hole (5.2)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.246327, 130.555295),
    ('5.3', 'Misool Resort Blue Hole (5.3)',
     'Indonesia', 'Raja Ampat / Misool', 5,
     -2.246123, 130.555848),
    ('13.1', 'Kwawi (13.1)',
     'Indonesia', 'Papua Barat / Manokwari', 5,
     -0.876173, 134.084825),
    ('13.2', 'Kwawi (13.2)',
     'Indonesia', 'Papua Barat / Manokwari', 10,
     -0.87621, 134.084788),
    ('14.1', 'Warenseki (14.1)',
     'Indonesia', 'Papua Barat / Manokwari', 5,
     -0.881452, 134.121081),
    ('14.2', 'Warenseki (14.2)',
     'Indonesia', 'Papua Barat / Manokwari', 10,
     -0.881596, 134.121086),
    ('15.1', 'Korepyar (15.1)',
     'Indonesia', 'Papua Barat / Manokwari', 10,
     -0.89613, 134.086633),
    ('16.1', 'Manggewa (16.1)',
     'Indonesia', 'Papua Barat / Manokwari', 10,
     -0.923679, 134.105151),
    ('50.1', 'Blue Lagoon Drop-off (50.1)',
     'Indonesia', 'Bali / Padangbai', 5,
     -8.529076, 115.514742),
    ('50.2', 'Blue Lagoon Drop-off (50.2)',
     'Indonesia', 'Bali / Padangbai', 10,
     -8.529107, 115.514903),
    ('50.3', 'Blue Lagoon to Padangbai (50.3)',
     'Indonesia', 'Bali / Padangbai', 5,
     -8.53055, 115.514238),
    ('51.1', 'Restoration (51.1)',
     'Indonesia', 'Bali / Padangbai', 5,
     -8.526964, 115.513058),
    ('52.1', 'White Sand Beach (52.1)',
     'Indonesia', 'Bali / Padangbai', 5,
     -8.536884, 115.509248),
    ('52.2', 'White Sand Beach (52.2)',
     'Indonesia', 'Bali / Padangbai', 10,
     -8.536895, 115.509538),
    ('53.1', 'Gili Tepekong (53.1)',
     'Indonesia', 'Bali / Padangbai', 10,
     -8.532032, 115.585242),
    ('54.1', 'Jepun (54.1)',
     'Indonesia', 'Bali / Padangbai', 5,
     -8.521797, 115.512814),
]


def seed_reference_dive_sites(apps, schema_editor):
    """Import coraldb's reference dive sites, one row per site_id."""
    DiveSite = apps.get_model('upload', 'DiveSite')
    for site_id, name, country, region, depth, lat, lon in REFERENCE_DIVE_SITES:
        DiveSite.objects.create(
            site_id=site_id, name=name, country=country, region=region,
            depth=depth, latitude=Decimal(str(lat)), longitude=Decimal(str(lon)),
            source_version=SOURCE_VERSION,
        )


def remove_reference_dive_sites(apps, schema_editor):
    """Reverse the import by deleting the reference sites."""
    DiveSite = apps.get_model('upload', 'DiveSite')
    DiveSite.objects.filter(source_version=SOURCE_VERSION).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0015_divesite_site_id_depth'),
    ]

    operations = [
        migrations.RunPython(seed_reference_dive_sites, remove_reference_dive_sites),
    ]
