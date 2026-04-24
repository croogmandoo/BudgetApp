"""Django admin for projects, project tasks, and project-transaction links."""

from __future__ import annotations

from django.contrib import admin

from .models import Project, ProjectTask, ProjectTransactionLink


class ProjectTaskInline(admin.TabularInline):
    model = ProjectTask
    extra = 0
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "budget", "start_date", "end_date", "household")
    list_filter = ("status", "household")
    search_fields = ("name", "notes")
    date_hierarchy = "start_date"
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [ProjectTaskInline]


@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "est_cost", "actual_cost", "assignee", "due_date")
    list_filter = ("status", "project__household")
    search_fields = ("title",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ProjectTransactionLink)
class ProjectTransactionLinkAdmin(admin.ModelAdmin):
    list_display = ("transaction", "project", "task", "created_at")
    list_filter = ("project__household",)
    readonly_fields = ("id", "created_at", "updated_at")
