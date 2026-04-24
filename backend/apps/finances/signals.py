from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Household
from apps.finances.importers.profiles import DEFAULT_PROFILES


@receiver(post_save, sender=Household)
def seed_import_profiles(sender, instance, created, **kwargs):
    if not created:
        return
    from apps.finances.models import ImportProfile  # noqa: PLC0415
    ImportProfile.objects.bulk_create([
        ImportProfile(
            household=instance,
            institution=p["institution"],
            format=p["format"],
            mapping_json=p["mapping_json"],
        )
        for p in DEFAULT_PROFILES
    ])
