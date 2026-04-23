"""Placeholder tests for ``apps.projects``."""

from __future__ import annotations


def test_projects_app_imports() -> None:
    """Sanity-check that the project models import cleanly."""
    from apps.projects import models  # noqa: F401
