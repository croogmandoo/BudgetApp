"""Django admin for bills and bill instances."""

from __future__ import annotations

from django.contrib import admin

from .models import Bill, BillInstance


class BillInstanceInline(admin.TabularInline):
    model = BillInstance
    extra = 0
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("name", "payee", "amount", "cadence", "next_due", "autopay", "household")
    list_filter = ("cadence", "autopay", "household")
    search_fields = ("name", "payee")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [BillInstanceInline]


@admin.register(BillInstance)
class BillInstanceAdmin(admin.ModelAdmin):
    list_display = ("bill", "due_date", "amount_expected", "status", "paid_transaction")
    list_filter = ("status", "bill__household")
    date_hierarchy = "due_date"
    readonly_fields = ("id", "created_at", "updated_at")
