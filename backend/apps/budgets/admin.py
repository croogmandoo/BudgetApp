"""Django admin for envelope-budgeting models."""

from __future__ import annotations

from django.contrib import admin

from .models import BudgetAllocation, BudgetPeriod, BudgetTransfer


class BudgetAllocationInline(admin.TabularInline):
    model = BudgetAllocation
    extra = 0
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(BudgetPeriod)
class BudgetPeriodAdmin(admin.ModelAdmin):
    list_display = ("month", "household", "locked_at")
    list_filter = ("household",)
    date_hierarchy = "month"
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [BudgetAllocationInline]


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = ("period", "category", "amount")
    list_filter = ("period__household",)
    search_fields = ("category__name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(BudgetTransfer)
class BudgetTransferAdmin(admin.ModelAdmin):
    list_display = ("at", "period", "from_category", "to_category", "amount", "user")
    list_filter = ("period__household",)
    readonly_fields = ("id", "at", "created_at", "updated_at")
