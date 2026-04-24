from __future__ import annotations

import uuid

from django.db import migrations

from apps.finances.importers.profiles import DEFAULT_PROFILES


def seed_profiles(apps, schema_editor):
    Household = apps.get_model("accounts", "Household")
    ImportProfile = apps.get_model("finances", "ImportProfile")
    for household in Household.objects.all():
        for p in DEFAULT_PROFILES:
            ImportProfile.objects.create(
                id=uuid.uuid4(),
                household=household,
                institution=p["institution"],
                format=p["format"],
                mapping_json=p["mapping_json"],
            )


def unseed_profiles(apps, schema_editor):
    ImportProfile = apps.get_model("finances", "ImportProfile")
    institutions = [p["institution"] for p in DEFAULT_PROFILES]
    ImportProfile.objects.filter(institution__in=institutions).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("finances", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_profiles, unseed_profiles),
    ]
