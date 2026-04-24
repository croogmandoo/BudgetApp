"""Django admin for notifications, webhooks, and per-user channel prefs.

Webhook ciphertext columns (``secret_enc`` / ``secret_dek_enc``) are
never exposed in the admin UI — an admin who needs to rotate a webhook
secret should delete the row and re-create from the API.
"""

from __future__ import annotations

from django.contrib import admin

from .models import Notification, UserChannelPreference, Webhook


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ("url", "enabled", "household", "created_at")
    list_filter = ("enabled", "household")
    search_fields = ("url",)
    readonly_fields = ("id", "secret_enc", "secret_dek_enc", "created_at", "updated_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("event_type", "user", "household", "status", "read_at", "created_at")
    list_filter = ("status", "event_type", "household")
    search_fields = ("event_type", "entity_ref")
    date_hierarchy = "created_at"
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(UserChannelPreference)
class UserChannelPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "channel", "enabled")
    list_filter = ("channel", "enabled", "event_type")
    search_fields = ("user__username", "event_type")
    readonly_fields = ("id", "created_at", "updated_at")
