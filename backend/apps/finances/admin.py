"""Django admin for accounts, categories, transactions, and import metadata."""

from __future__ import annotations

from django.contrib import admin

from .models import (
    Account,
    Category,
    ImportBatch,
    ImportProfile,
    Rule,
    Transaction,
    TransactionSplit,
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "institution", "currency", "household", "closed_at")
    list_filter = ("type", "currency", "household")
    search_fields = ("name", "institution")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "parent", "is_budgetable", "rollover_mode", "household")
    list_filter = ("kind", "is_budgetable", "rollover_mode", "household")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")


class TransactionSplitInline(admin.TabularInline):
    model = TransactionSplit
    extra = 0
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "account", "amount", "payee", "category", "status")
    list_filter = ("status", "account", "category")
    search_fields = ("payee", "memo", "import_hash")
    date_hierarchy = "date"
    readonly_fields = ("id", "import_hash", "created_at", "updated_at")
    inlines = [TransactionSplitInline]


@admin.register(ImportProfile)
class ImportProfileAdmin(admin.ModelAdmin):
    list_display = ("institution", "format", "household")
    list_filter = ("format", "household")
    search_fields = ("institution",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ("filename", "account", "user", "row_count", "created_at")
    list_filter = ("account", "user")
    search_fields = ("filename", "sha256")
    readonly_fields = ("id", "sha256", "created_at", "updated_at")


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("household", "priority", "enabled", "created_at")
    list_filter = ("enabled", "household")
    readonly_fields = ("id", "created_at", "updated_at")
