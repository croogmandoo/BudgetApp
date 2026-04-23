"""App config for the ``maintenance`` app.

Owns recurring upkeep reminders (HVAC filters, gutters, vehicle service).
See SPEC §3.5.
"""

from __future__ import annotations

from django.apps import AppConfig


class MaintenanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.maintenance"
    label = "maintenance"
    verbose_name = "Maintenance reminders"
