"""Django admin for cross-cutting models.

AuditLog is registered read-only — no add / change / delete actions — so
administrators can inspect the audit trail without being able to tamper
with it (SPEC §7.5). Attachment is registered read-only too: the raw
ciphertext bytes are useless in the UI, and an admin who needs to delete
a file should do so through the owning domain object.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin

from .models import Attachment, AuditLog


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: Any) -> bool:
        return False

    def has_change_permission(self, request: Any, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        return False


@admin.register(Attachment)
class AttachmentAdmin(ReadOnlyAdmin):
    list_display = ("filename", "mime", "size", "owner_type", "owner_id", "created_at")
    list_filter = ("mime", "owner_type")
    search_fields = ("filename", "sha256")
    readonly_fields = (
        "id",
        "owner_type",
        "owner_id",
        "filename",
        "mime",
        "size",
        "sha256",
        "encrypted_blob_ref",
        "dek_enc",
        "created_at",
        "updated_at",
    )


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyAdmin):
    list_display = ("at", "action", "entity", "household_id", "user_id", "ip")
    list_filter = ("action", "entity")
    search_fields = ("action", "entity", "user_agent")
    date_hierarchy = "at"
    readonly_fields = (
        "id",
        "household_id",
        "user_id",
        "at",
        "action",
        "entity",
        "before_hash",
        "after_hash",
        "ip",
        "user_agent",
    )
