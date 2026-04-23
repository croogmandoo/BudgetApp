"""App config for the ``projects`` app.

Owns home projects (SPEC §3.4): projects, sub-tasks, and the many-to-many
link between projects / tasks and transactions for cost rollups.
"""

from __future__ import annotations

from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.projects"
    label = "projects"
    verbose_name = "Home projects"
