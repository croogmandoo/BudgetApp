"""Webhook, Notification, UserChannelPreference.

Design notes (SPEC §3.7):

    - Webhook secrets are envelope-encrypted at rest
      (``secret_enc`` + ``secret_dek_enc``); the plaintext is never
      persisted.
    - ``event_mask`` is a JSON list of event type strings such as
      ``"transaction.imported"`` or ``"bill.overdue"``.
    - ``Notification`` is the in-app inbox row. External-channel delivery
      state is tracked per-channel in a JSON field so adapters can add
      new channels (Matrix, Slack, Discord) without schema changes.
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Household, User
from apps.core.models import TimestampedModel


class Webhook(TimestampedModel):
    """Outbound HMAC-signed webhook endpoint owned by a household."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="webhooks")
    url = models.URLField(max_length=1024)
    # Envelope-encrypted shared secret used to sign payloads (SPEC §7.2).
    secret_enc = models.BinaryField()
    secret_dek_enc = models.BinaryField()
    event_mask = models.JSONField(default=list)
    enabled = models.BooleanField(default=True)


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    DEAD_LETTER = "dead_letter", "Dead-lettered"


class Notification(TimestampedModel):
    """An in-app inbox row; also the source record for external delivery."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        help_text="Null for household-wide notices.",
    )
    event_type = models.CharField(max_length=64)
    entity_ref = models.CharField(max_length=128, blank=True)
    payload_json = models.JSONField(default=dict)
    status = models.CharField(
        max_length=16,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["household", "created_at"]),
            models.Index(fields=["user", "read_at"]),
        ]


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In-app"
    EMAIL = "email", "Email"
    NTFY = "ntfy", "ntfy"
    GOTIFY = "gotify", "Gotify"
    WEBHOOK = "webhook", "Webhook"


class UserChannelPreference(TimestampedModel):
    """Per-user opt-in map of event type to channel.

    A row's existence with ``enabled=True`` means "deliver this event type
    to this channel for this user". Missing rows are treated as opt-out,
    except for the in-app inbox which is always on (SPEC §3.7).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="channel_preferences",
    )
    event_type = models.CharField(max_length=64)
    channel = models.CharField(max_length=16, choices=NotificationChannel.choices)
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event_type", "channel"],
                name="uniq_pref_per_user_event_channel",
            ),
        ]
