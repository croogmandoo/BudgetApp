"""Django admin for recurring maintenance tasks."""

from __future__ import annotations

from django.contrib import admin

from .models import MaintenanceTask


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "cadence_interval", "cadence", "last_done", "next_due", "household")
    list_filter = ("cadence", "household")
    search_fields = ("title", "notes")
    date_hierarchy = "next_due"
    readonly_fields = ("id", "created_at", "updated_at")
