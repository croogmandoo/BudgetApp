"""Round-trip tests for cross-cutting models."""

from __future__ import annotations

import uuid

import pytest

from apps.core.models import Attachment, AuditLog


@pytest.mark.django_db
def test_attachment_roundtrip() -> None:
    attachment = Attachment.objects.create(
        owner_type="transaction",
        owner_id=uuid.uuid4(),
        filename="receipt.pdf",
        mime="application/pdf",
        size=12345,
        sha256="a" * 64,
        encrypted_blob_ref="attachments/2026/04/receipt.enc",
        dek_enc=b"\x00" * 32,
    )
    fetched = Attachment.objects.get(pk=attachment.pk)
    assert fetched.filename == "receipt.pdf"
    assert fetched.mime == "application/pdf"
    assert fetched.size == 12345
    assert "receipt.pdf" in str(fetched)


@pytest.mark.django_db
def test_auditlog_has_no_updated_at() -> None:
    entry = AuditLog.objects.create(
        household_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        action="transaction.created",
        entity="transaction",
        before_hash="",
        after_hash="x" * 64,
    )
    assert entry.at is not None
    # AuditLog must NOT inherit TimestampedModel (SPEC §7.5: append-only,
    # no mutation). Guard against someone adding updated_at later.
    assert not hasattr(entry, "updated_at")
