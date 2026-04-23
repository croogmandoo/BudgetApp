"""App config for the ``budgets`` app.

Owns envelope budgeting: per-month budget periods, per-category allocations,
and audit-visible transfers between envelopes (SPEC §3.2).
"""

from __future__ import annotations

from django.apps import AppConfig


class BudgetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.budgets"
    label = "budgets"
    verbose_name = "Envelope budgeting"
