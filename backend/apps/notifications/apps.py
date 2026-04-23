"""App config for the ``notifications`` app.

Owns the single notification subsystem: in-app inbox, outbound webhooks
(HMAC-signed), and per-user channel preferences. External channel
adapters (SMTP, ntfy, Gotify) sit behind the same event model.
See SPEC §3.7.
"""

from __future__ import annotations

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    label = "notifications"
    verbose_name = "Notifications"
