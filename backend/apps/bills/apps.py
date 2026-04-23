"""App config for the ``bills`` app.

Owns recurring obligations: ``Bill`` templates (cadence + due day +
paying account) and ``BillInstance`` rows (materialised expected + paid
records). See SPEC §3.3.
"""

from __future__ import annotations

from django.apps import AppConfig


class BillsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bills"
    label = "bills"
    verbose_name = "Recurring bills"
