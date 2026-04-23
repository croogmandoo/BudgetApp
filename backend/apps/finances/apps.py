"""App config for the ``finances`` app.

Owns accounts, categories, transactions, splits, categorization rules, and
file-based imports (per-bank profiles + import batches). See SPEC §3.1.
"""

from __future__ import annotations

from django.apps import AppConfig


class FinancesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.finances"
    label = "finances"
    verbose_name = "Accounts, transactions & imports"
