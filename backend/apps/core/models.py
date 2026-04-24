"""Cross-cutting models.

Contents:
    - ``TimestampedModel``: abstract base providing ``created_at`` / ``updated_at``.
      Every domain model in the project inherits from this to give every row
      an audit-friendly creation and mutation timestamp.
    - ``Attachment``: envelope-encrypted blob storage (SPEC §6, §7.2). The
      raw bytes live on disk under ``encrypted_blob_ref``; the per-file DEK
      is stored wrapped in ``dek_enc``.
    - ``AuditLog``: append-only activity record (SPEC §7.5). Writes must go
      through a dedicated service layer; there is no ``delete`` path.
"""

from __future__ import annotations

import uuid

from django.db import models


class TimestampedModel(models.Model):
    """Abstract base model with creation + mutation timestamps.

    Every concrete model in ``apps.*`` should inherit from this so all rows
    carry consistent audit metadata.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Attachment(TimestampedModel):
    """Envelope-encrypted attachment (receipt, quote, photo, PDF).

    The plaintext file is never stored. On upload the app generates a random
    per-file DEK, encrypts the bytes with it, writes the ciphertext to
    ``encrypted_blob_ref`` (a filesystem path relative to ``MEDIA_ROOT``),
    wraps the DEK with the master key, and stores the wrapped blob in
    ``dek_enc``. See SPEC §7.2.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Generic owner pointer. We intentionally do not use Django's
    # GenericForeignKey here: the full set of owner tables is small and
    # enumerated in SPEC §6, and a plain (owner_type, owner_id) pair keeps
    # queries and the OpenAPI schema simpler.
    owner_type = models.CharField(max_length=64)
    owner_id = models.UUIDField()

    filename = models.CharField(max_length=255)
    mime = models.CharField(max_length=128)
    size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)

    encrypted_blob_ref = models.CharField(max_length=512)
    dek_enc = models.BinaryField(editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["owner_type", "owner_id"]),
            models.Index(fields=["sha256"]),
        ]

    def __str__(self) -> str:
        return f"{self.filename} ({self.owner_type}:{self.owner_id})"


class AuditLog(models.Model):
    """Append-only record of security- and finance-relevant actions.

    Only the writer service ever inserts into this table. There is no
    ``updated_at`` and no delete path; migrations must not add either.
    See SPEC §7.5.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    at = models.DateTimeField(auto_now_add=True, db_index=True)
    action = models.CharField(max_length=64)
    entity = models.CharField(max_length=64)
    before_hash = models.CharField(max_length=64, blank=True)
    after_hash = models.CharField(max_length=64, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["household_id", "at"]),
            models.Index(fields=["entity", "at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity} @ {self.at:%Y-%m-%d %H:%M:%S}"
