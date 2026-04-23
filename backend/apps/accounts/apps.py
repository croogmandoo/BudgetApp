"""App config for the ``accounts`` app.

Owns the ``Household`` tenant boundary, the custom ``User`` (TOTP-mandatory
from day one, SPEC §7.1), and personal access tokens used by API clients
(SPEC §5.1).
"""

from __future__ import annotations

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Accounts & identity"
