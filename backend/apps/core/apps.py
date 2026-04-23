"""App config for the ``core`` app.

The ``core`` app owns cross-cutting primitives: the ``TimestampedModel``
abstract base every domain model inherits from, the ``Attachment`` model
(used by projects / transactions / bills for receipts and quotes), the
append-only ``AuditLog`` (SPEC §7.5), and the envelope-encryption helper
(``apps.core.crypto``).
"""

from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"
    verbose_name = "Core"
